import time
import numpy as np
import pyaudio
from . import config
from . import dsp
import numpy as np
from scipy.ndimage import gaussian_filter1d

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

# These will be assigned in init()
mel_gain = None
mel_smoothing = None
y_roll = None
fft_window = None
max_volume = None

def init():
    global mel_gain, mel_smoothing, y_roll, fft_window, max_volume

    dsp.create_mel_bank()

    mel_gain = ExpFilter(
        np.tile(1e-1, config.N_FFT_BINS),
        alpha_decay=0.05,
        alpha_rise=0.8
    )

    mel_smoothing = ExpFilter(
        np.tile(1e-1, config.N_FFT_BINS),
        alpha_decay=0.5,
        alpha_rise=0.8
    )

    samples_per_frame = int(config.MIC_RATE / config.FPS)
    rolling_frames = config.N_ROLLING_HISTORY

    y_roll = np.random.rand(rolling_frames, samples_per_frame) / 1e16
    fft_window = np.hamming(samples_per_frame * rolling_frames)

    max_volume = 0.002

def create_band_levels(audio_chunk: np.ndarray) -> bytes | None:
    global y_roll, max_volume
    y = audio_chunk / 2.0**15

    # Rolling buffer
    y_roll[:-1] = y_roll[1:]
    y_roll[-1, :] = y
    y_data = np.concatenate(y_roll, axis=0).astype(np.float32)

    # Volume check (before windowing)
    volume = np.sqrt(np.mean(y_data**2))
    if volume < max_volume:  # threshold (adjustable)
        return None

    # Window and pad
    y_data *= fft_window
    N = len(y_data)
    N_zeros = 2**int(np.ceil(np.log2(N))) - N
    y_padded = np.pad(y_data, (0, N_zeros), mode='constant')

    # FFT and Mel
    YS = np.abs(np.fft.rfft(y_padded)[:N // 2])
    mel = np.atleast_2d(YS).T * dsp.mel_y.T
    mel = np.sum(mel, axis=0)
    mel = mel**2.0

    # Gain & smoothing
    mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
    mel /= mel_gain.value
    mel = mel_smoothing.update(mel)

    # Convert to 0–255 brightness levels
    mel = np.clip(mel, 0, 1)
    return bytes((mel * 255).astype(np.uint8))

""" 
Starts an audio stream to capture microphone input and process it in real-time.

This function initializes a PyAudio stream to capture audio data from the microphone.
It reads audio frames in chunks determined by the specified sample rate (`rate`) and
frames per second (`fps`). The captured audio data is passed to the provided `callback`
function for further processing. The function also handles audio buffer overflows and
logs the number of overflows that occur.

Args:
    callback (function): A function to process the captured audio data. It should accept
                            a single argument, which is a NumPy array of audio samples.
    rate (int): The sampling rate of the microphone in Hz (e.g., 44100 for CD-quality audio).
    fps (int): The refresh rate of the visualization or processing in frames per second.
"""
def start_stream(callback):
    p = pyaudio.PyAudio()
    frames_per_buffer = int(config.MIC_RATE / config.FPS)
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=config.MIC_RATE,
                    input=True,
                    frames_per_buffer=frames_per_buffer,
                    input_device_index=config.MIC_DEVICE_INDEX)
    overflows = 0
    prev_ovf_time = time.time()
    while True:
        try:
            y = np.fromstring(stream.read(frames_per_buffer, exception_on_overflow=False), dtype=np.int16)
            y = y.astype(np.float32)
            stream.read(stream.get_read_available(), exception_on_overflow=False)
            callback(y)
        except IOError:
            overflows += 1
            if time.time() > prev_ovf_time + 1:
                prev_ovf_time = time.time()
                print('Audio buffer has overflowed {} times'.format(overflows))
    stream.stop_stream()
    stream.close()
    p.terminate()

def list_audio_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        for key, value in info.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    list_audio_devices()
    
    def example_callback(data):
        print("Processing audio data:", data)

    start_stream(example_callback)