# process.py  — JACK backend version (no PyAudio)
import time
from dataclasses import dataclass

import numpy as np
import aubio
import jack
from scipy.ndimage import gaussian_filter1d

from . import config
from . import dsp


@dataclass
class AudioInfo:
    bands: bytes | None = None
    beat_detected: bool = False
    bpm: float = 0.0


class AudioProcessor:
    """
    JACK-based audio capture with fixed-hop DSP (mel bands + aubio tempo).

    Public API preserved:
      - setup(callback)
      - start()
      - stop()
      - terminate()
      - list_audio_devices()  (now lists JACK ports)
    """

    def __init__(self):
        # JACK
        self._jack: jack.Client | None = None
        self._inport: jack.OwnPort | None = None
        self._activated = False

        # DSP config/state
        self.callback = None
        self.max_volume = getattr(config, "MAX_VOLUME", 0.0001)

        # Fixed DSP hop (samples at MIC_RATE)
        self._hop = int(config.MIC_RATE / config.SAMPLING_FREQUENCY)

        # Rolling FFT window state (N_ROLLING_HISTORY hops)
        self.y_roll: np.ndarray | None = None
        self.fft_window: np.ndarray | None = None

        # Display throttle: run visual callback at DISPLAY_FREQUENCY
        self._display_cntr = 0
        self._display_cntr_limit = max(
            1, int(config.SAMPLING_FREQUENCY / config.DISPLAY_FREQUENCY)
        )

        # aubio tempo
        self._aubio_tempo: aubio.tempo | None = None
        self._is_beat = False

        # Ring buffer for variable JACK periods → fixed hop DSP
        self._ring_capacity = 8 * self._hop
        self._ring = np.zeros(self._ring_capacity, dtype=np.float32)
        self._ring_w = 0
        self._ring_r = 0
        self._ring_len = 0

        # FPS/diagnostics counters (kept for compatibility)
        self._last_fps_time = time.time()
        self._frames_counted = 0

    # ---------------------------
    # Setup & helpers
    # ---------------------------
    def setup(self, callback):
        """Prepare DSP and register the downstream callback."""
        # Mel bank / filters prepared by your DSP module
        dsp.create_mel_bank()

        self.callback = callback

        # Smoothing/gain filters (from your dsp utilities)
        ExpFilter = getattr(dsp, "ExpFilter")
        self.mel_gain = ExpFilter(
            np.tile(1e-1, config.N_FFT_BINS), alpha_decay=0.05, alpha_rise=0.8
        )
        self.mel_smoothing = ExpFilter(
            np.tile(1e-1, config.N_FFT_BINS), alpha_decay=0.5, alpha_rise=0.8
        )

        # Rolling window sized to fixed hop
        rolling_frames = config.N_ROLLING_HISTORY
        self.y_roll = (
            np.random.rand(rolling_frames, self._hop).astype(np.float32) / 1e16
        )
        self.fft_window = np.hamming(
            self._hop * rolling_frames).astype(np.float32)

        # aubio tempo: fixed hop; window size can be tuned (512 is common)
        win_size = 512
        self._aubio_tempo = aubio.tempo(
            "default",
            win_size,
            self._hop,
            config.MIC_RATE,
        )

        self._display_cntr_limit = max(
            1, int(config.SAMPLING_FREQUENCY / config.DISPLAY_FREQUENCY)
        )

    # ---------------------------
    # JACK lifecycle
    # ---------------------------
    def start(self):
        """Connect to JACK and start processing."""
        if self._jack is not None and self._activated:
            return

        # connects to running server
        self._jack = jack.Client("PyJackListener")
        self._inport = self._jack.inports.register("in")

        # Register callbacks
        self._jack.set_process_callback(self._jack_process_cb)
        self._jack.set_xrun_callback(self._on_xrun)
        self._jack.set_samplerate_callback(self._on_samplerate)
        self._jack.set_blocksize_callback(self._on_blocksize)

        # Activate client
        self._jack.activate()
        self._activated = True

        # Optional: auto-connect the first physical capture source to our input
        try:
            phys_srcs = self._jack.get_ports(is_physical=True, is_output=True)
            if phys_srcs:
                self._jack.connect(phys_srcs[0], self._inport)
        except jack.JackError:
            # Avoid prints in RT path; this is non-RT
            pass

        print(
            f"SR={self._jack.samplerate} Hz, blocksize={self._jack.blocksize} frames."
        )

    def stop(self):
        """Deactivate the JACK client (keeps ports until close)."""
        if self._jack and self._activated:
            self._jack.deactivate()
            self._activated = False

    def terminate(self):
        """Close JACK client and free resources."""
        self.stop()
        if self._jack:
            self._jack.close()
            self._jack = None

    # ---------------------------
    # JACK callbacks
    # ---------------------------
    def _on_xrun(self, delay_us: float):
        # Non-RT logging is safer; JACK may call in RT context, so keep it minimal.
        # Here we just mark a flag or a counter; print is okay but keep rare.
        # print(f"XRUN ~{delay_us:.0f} µs")
        pass

    def _on_samplerate(self, sr: int):
        # We intentionally keep DSP hop fixed; nothing to do.
        print(f"JACK samplerate -> {sr}")

    def _on_blocksize(self, bs: int):
        # Our accumulator makes this a no-op; just log.
        print(f"JACK blocksize -> {bs}")

    @property
    def _jack_process_cb(self):
        # Wrap the instance method so JACK can call it
        def _cb(frames: int):
            self._jack_callback(frames)
        return _cb

    def _jack_callback(self, frames: int):
        """RT callback: pull JACK buffer, enqueue, consume in fixed hops."""
        buf = self._inport.get_buffer()                      # CFFI buffer of float32
        inbuf = np.frombuffer(buf, dtype=np.float32,
                              count=frames)  # 1D NumPy view
        self._ring_write(inbuf)

        while True:
            hop = self._ring_pop_hop()
            if hop is None:
                break

            # aubio expects float32 mono
            bpm = 0.0
            if self._aubio_tempo is not None:
                bpm = float(self._aubio_tempo.get_bpm() or 0.0)
                if self._aubio_tempo(hop)[0] > 0.0:
                    self._is_beat = True

            # Throttle visualization/consumer callback to DISPLAY_FREQUENCY
            self._display_cntr += 1
            if self._display_cntr >= self._display_cntr_limit:
                self._display_cntr = 0
                bands = self.create_band_levels(hop)  # bytes | None
                audio_info = AudioInfo(
                    bands=bands, beat_detected=self._is_beat, bpm=bpm
                )
                self._is_beat = False
                if self.callback:
                    # NOTE: This runs in JACK RT thread. Keep it light/lock-free.
                    self.callback(audio_info)

            # Diagnostics (cheap)
            self._count_fps()

    # ---------------------------
    # Ring buffer (lock-free, overwrite-oldest on overflow)
    # ---------------------------
    def _ring_write(self, x: np.ndarray):
        n = int(x.size)
        if n <= 0:
            return

        # If input is larger than capacity, keep only the tail that fits
        if n > self._ring_capacity:
            x = x[-self._ring_capacity:]
            n = x.shape[0]
            self._ring_w = 0
            self._ring_r = 0
            self._ring_len = 0

        # Ensure room (overwrite oldest frames if necessary)
        needed = self._ring_len + n - self._ring_capacity
        if needed > 0:
            drop = min(needed, self._ring_len)
            self._ring_r = (self._ring_r + drop) % self._ring_capacity
            self._ring_len -= drop

        # Write with wrap
        first = min(n, self._ring_capacity - self._ring_w)
        self._ring[self._ring_w: self._ring_w + first] = x[:first]
        self._ring_w = (self._ring_w + first) % self._ring_capacity
        rest = n - first
        if rest:
            self._ring[0:rest] = x[first:]
            self._ring_w = rest
        self._ring_len += n

    def _ring_pop_hop(self) -> np.ndarray | None:
        if self._ring_len < self._hop:
            return None
        first = min(self._hop, self._ring_capacity - self._ring_r)
        if first == self._hop:
            out = self._ring[self._ring_r: self._ring_r + self._hop]
        else:
            out = np.empty(self._hop, dtype=np.float32)
            out[:first] = self._ring[self._ring_r: self._ring_r + first]
            out[first:] = self._ring[0: self._hop - first]
        self._ring_r = (self._ring_r + self._hop) % self._ring_capacity
        self._ring_len -= self._hop
        return out

    # ---------------------------
    # DSP core
    # ---------------------------
    def create_band_levels(self, audio_chunk: np.ndarray) -> bytes | None:
        """
        Compute mel-band levels from a mono float32 chunk (length == self._hop).

        Returns:
            bytes (N_FFT_BINS) in range 0..255, or None if below volume floor.
        """
        # JACK gives float32 in [-1, 1]
        y = audio_chunk.astype(np.float32, copy=False)

        # Rolling history for a longer FFT
        self.y_roll[:-1] = self.y_roll[1:]
        self.y_roll[-1, :] = y
        y_data = np.concatenate(self.y_roll, axis=0).astype(np.float32)

        # Volume gate
        volume = np.sqrt(np.mean(y_data**2))
        if volume < self.max_volume:
            return None

        # Window & zero-pad to next power of 2
        y_data *= self.fft_window
        N = len(y_data)
        N_zeros = (1 << int(np.ceil(np.log2(max(1, N))))) - N
        if N_zeros > 0:
            y_padded = np.pad(y_data, (0, N_zeros), mode="constant")
        else:
            y_padded = y_data

        # Spectrum (one-sided)
        YS = np.abs(np.fft.rfft(y_padded))[: N // 2]

        # Mel aggregation (dsp.mel_y expected shape [N_fft_bins, mel_bins]^T or similar)
        mel = np.atleast_2d(YS).T * dsp.mel_y.T
        mel = np.sum(mel, axis=0)
        mel = mel**2.0

        # Adaptive gain + smoothing
        self.mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
        mel = mel / max(1e-12, self.mel_gain.value)
        mel = self.mel_smoothing.update(mel)

        # Clamp and convert to bytes
        mel = np.clip(mel, 0.0, 1.0)
        return bytes((mel * 255).astype(np.uint8))

    # ---------------------------
    # Diagnostics
    # ---------------------------
    def _count_fps(self):
        self._frames_counted += 1
        now = time.time()
        if now - self._last_fps_time >= 1.0:
            # Uncomment for debug:
            # print(f"Audio hops/sec: {self._frames_counted}")
            self._frames_counted = 0
            self._last_fps_time = now

    # ---------------------------
    # Utilities
    # ---------------------------
    @staticmethod
    def list_audio_devices():
        """With JACK, list physical capture/playback ports instead of devices."""
        c = jack.Client("PyJackLister")
        try:
            print("Physical capture (sources):")
            for p in c.get_ports(is_physical=True, is_output=True):
                print("  ", p)
            print("Physical playback (sinks):")
            for p in c.get_ports(is_physical=True, is_input=True):
                print("  ", p)
        finally:
            c.close()


audioProcessor = AudioProcessor()
