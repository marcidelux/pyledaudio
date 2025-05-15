MIC_RATE = 48000
"""Sampling frequency of the microphone in Hz"""

""" Microphone device index to use."""
MIC_DEVICE_INDEX = 4

FPS = 60
"""Desired refresh rate of the visualization (frames per second)"""

MIN_FREQUENCY = 60
"""Frequencies below this value will be removed during audio processing"""

MAX_FREQUENCY = 18000
"""Frequencies above this value will be removed during audio processing"""

N_FFT_BINS = 12

N_ROLLING_HISTORY = 2
"""Number of past audio frames to include in the rolling window"""

""" Set the configuration for the audio visualization."""
def set_config(config:dict):
    global MIC_RATE, MIC_DEVICE_INDEX, FPS, MIN_FREQUENCY, MAX_FREQUENCY, N_FFT_BINS, N_ROLLING_HISTORY
    MIC_RATE = config.get('MIC_RATE', MIC_RATE)
    MIC_DEVICE_INDEX = config.get('MIC_DEVICE_INDEX', MIC_DEVICE_INDEX)
    FPS = config.get('FPS', FPS)
    MIN_FREQUENCY = config.get('MIN_FREQUENCY', MIN_FREQUENCY)
    MAX_FREQUENCY = config.get('MAX_FREQUENCY', MAX_FREQUENCY)
    N_FFT_BINS = config.get('N_FFT_BINS', N_FFT_BINS)
    N_ROLLING_HISTORY = config.get('N_ROLLING_HISTORY', N_ROLLING_HISTORY)

    # Print all global variables defined in this file
    print("Current configuration:")
    print(f"MIC_RATE: {MIC_RATE}")
    print(f"MIC_DEVICE_INDEX: {MIC_DEVICE_INDEX}")
    print(f"FPS: {FPS}")
    print(f"MIN_FREQUENCY: {MIN_FREQUENCY}")
    print(f"MAX_FREQUENCY: {MAX_FREQUENCY}")
    print(f"N_FFT_BINS: {N_FFT_BINS}")
    print(f"N_ROLLING_HISTORY: {N_ROLLING_HISTORY}")