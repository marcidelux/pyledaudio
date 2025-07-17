import numpy as np
import pyaudio
import aubio
import time
from dataclasses import dataclass
from scipy.ndimage import gaussian_filter1d
from . import config
from . import dsp


@dataclass
class AudioInfo:
    bands: bytes | None = None
    beat_detected: bool = False
    bpm: float = 0.0


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
        self._aubio_tempo = None
        self._stream = None
        self._frames_per_buffer = 0
        self._is_beat = False
        self._display_cntr = 0
        self._display_cntr_limit = 0

        # Internal state
        self.mel_gain = None
        self.mel_smoothing = None
        self.y_roll = None
        self.fft_window = None
        self.max_volume = 0

    def setup(self, callback):
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

        self._frames_per_buffer = int(
            config.MIC_RATE / config.SAMPLING_FREQUENCY)
        win_size = 512

        rolling_frames = config.N_ROLLING_HISTORY
        self.y_roll = np.random.rand(
            rolling_frames, self._frames_per_buffer) / 1e16
        self.fft_window = np.hamming(self._frames_per_buffer * rolling_frames)
        self.max_volume = config.MAX_VOLUME

        self._aubio_tempo = aubio.tempo(
            "default",
            win_size,
            self._frames_per_buffer,
            config.MIC_RATE
        )

        self._display_cntr_limit = config.SAMPLING_FREQUENCY / config.DISPLAY_FREQUENCY

    def _pyaudio_callback(self, in_data, frame_count, time_info, status):
        # self.print_fps("audio")
        y = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)

        float_data = y / 2.0**15
        bpm = self._aubio_tempo.get_bpm()
        if self._aubio_tempo(float_data)[0] > 0.0:
            self._is_beat = True
            # print("Beat detected at", time.time())
            # print(f"BPM: {bpm}")

        self._display_cntr += 1

        if self._display_cntr >= self._display_cntr_limit:
            # self.print_fps("display")
            self._display_cntr = 0
            bands = self.create_band_levels(y)
            audio_info = AudioInfo(
                bands=bands,
                beat_detected=self._is_beat,
                bpm=bpm
            )
            self._is_beat = False
            if self.callback:
                self.callback(audio_info)

        return (None, pyaudio.paContinue)

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

    def start(self):
        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=config.MIC_RATE,
            input=True,
            frames_per_buffer=self._frames_per_buffer,
            input_device_index=config.MIC_DEVICE_INDEX,
            # <-- This is where PyAudio gets the stream callback
            stream_callback=self._pyaudio_callback
        )
        self._stream.start_stream()

    def stop(self):
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

    def terminate(self):
        self.stop()
        self._pyaudio.terminate()

    def print_fps(self, job: str):
        current_time = time.time()
        last_time_attr = job + '_last_time'
        fps_cntr_attr = job + '_fps_cntr'

        if not hasattr(self, last_time_attr):
            setattr(self, last_time_attr, current_time)
            setattr(self, fps_cntr_attr, 0)
            return

        if current_time - getattr(self, last_time_attr) >= 1.0:
            print(f"FPS {job}: {getattr(self, fps_cntr_attr)}")
            setattr(self, fps_cntr_attr, 0)
            setattr(self, last_time_attr, current_time)
        else:
            setattr(self, fps_cntr_attr, getattr(self, fps_cntr_attr) + 1)

    @staticmethod
    def list_audio_devices():
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            for key, value in info.items():
                print(f"{key}: {value}")
        p.terminate()


audioProcessor = AudioProcessor()
