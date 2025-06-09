import time
import threading
import numpy as np
import pyaudio
from scipy.ndimage import gaussian_filter1d
from . import config
from . import dsp


class ExpFilter:
    def __init__(self, val, alpha_decay=0.5, alpha_rise=0.5):
        self.alpha_decay = alpha_decay
        self.alpha_rise = alpha_rise
        self.value = np.array(val)

    def update(self, new_value):
        delta = new_value - self.value
        alpha = np.where(delta > 0, self.alpha_rise, self.alpha_decay)
        self.value += alpha * delta
        return self.value


class AudioProcessor:
    def __init__(self):
        self.callback = None
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._thread = None
        self._running = False
        self._overflows = 0

        # Internal state
        self.mel_gain = None
        self.mel_smoothing = None
        self.y_roll = None
        self.fft_window = None
        self.max_volume = 0

    def init(self, callback):
        dsp.create_mel_bank()

        self.callback = callback

        self.mel_gain = ExpFilter(
            np.tile(1e-1, config.N_FFT_BINS),
            alpha_decay=0.05,
            alpha_rise=0.8
        )

        self.mel_smoothing = ExpFilter(
            np.tile(1e-1, config.N_FFT_BINS),
            alpha_decay=0.5,
            alpha_rise=0.8
        )

        samples_per_frame = int(config.MIC_RATE / config.FPS)
        rolling_frames = config.N_ROLLING_HISTORY

        self.y_roll = np.random.rand(rolling_frames, samples_per_frame) / 1e16
        self.fft_window = np.hamming(samples_per_frame * rolling_frames)

        self.max_volume = config.MAX_VOLUME

    def create_band_levels(self, audio_chunk: np.ndarray) -> bytes | None:
        y = audio_chunk / 2.0**15
        self.y_roll[:-1] = self.y_roll[1:]
        self.y_roll[-1, :] = y
        y_data = np.concatenate(self.y_roll, axis=0).astype(np.float32)

        volume = np.sqrt(np.mean(y_data**2))
        if volume < self.max_volume:
            return None

        y_data *= self.fft_window
        N = len(y_data)
        N_zeros = 2**int(np.ceil(np.log2(N))) - N
        y_padded = np.pad(y_data, (0, N_zeros), mode='constant')

        YS = np.abs(np.fft.rfft(y_padded)[:N // 2])
        mel = np.atleast_2d(YS).T * dsp.mel_y.T
        mel = np.sum(mel, axis=0)
        mel = mel**2.0

        self.mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
        mel /= self.mel_gain.value
        mel = self.mel_smoothing.update(mel)

        mel = np.clip(mel, 0, 1)
        return bytes((mel * 255).astype(np.uint8))

    def _stream_loop(self):
        frames_per_buffer = int(config.MIC_RATE / config.FPS)
        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=config.MIC_RATE,
            input=True,
            frames_per_buffer=frames_per_buffer,
            input_device_index=config.MIC_DEVICE_INDEX
        )
        prev_ovf_time = time.time()

        while self._running:
            try:
                y = np.frombuffer(
                    self._stream.read(frames_per_buffer,
                                      exception_on_overflow=False),
                    dtype=np.int16
                ).astype(np.float32)
                self._stream.read(
                    self._stream.get_read_available(), exception_on_overflow=False)
                self.callback(y)
            except IOError:
                self._overflows += 1
                if time.time() > prev_ovf_time + 1:
                    prev_ovf_time = time.time()
                    print(
                        f'Audio buffer has overflowed {self._overflows} times')

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._stream = None

    def terminate(self):
        self.stop()
        self._pyaudio.terminate()

    @staticmethod
    def list_audio_devices():
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            for key, value in info.items():
                print(f"{key}: {value}")
        p.terminate()


audioProcessor = AudioProcessor()
