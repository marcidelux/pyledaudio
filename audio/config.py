MIC_RATE = 48000
MIC_DEVICE_INDEX = 4
FPS = 60
MIN_FREQUENCY = 60
MAX_FREQUENCY = 18000
N_FFT_BINS = 12
N_ROLLING_HISTORY = 2


def set_config(config: dict):
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
