# UDP DATA FOR ESP32
UDP_IP = '192.168.100.150'
UDP_PORT = 12345
SERVER_GUI = True

# SERVER DATA FOR WEBSOCKET and WEB UI
SERVER_IP = '0.0.0.0'
SERVER_PORT = 9999

MIC_RATE = 48000
"""Sampling frequency of the microphone in Hz"""

MIC_DEVICE_INDEX = 4
MIN_FREQUENCY = 60
"""Frequencies below this value will be removed during audio processing"""
MAX_FREQUENCY = 18000
"""Frequencies above this value will be removed during audio processing"""

SAMPLING_FREQUENCY = 256
DISPLAY_FREQUENCY = 32

N_FFT_BINS = 8
"""Number of frequency bins to use when transforming audio to frequency domain"""
N_ROLLING_HISTORY = 2
"""Number of past audio frames to include in the rolling window"""
MIN_VOLUME_THRESHOLD = 1e-7
"""No music visualization displayed if recorded audio volume below threshold"""


def get_config_dict():
    return {k: v for k, v in globals().items() if k.isupper()}
