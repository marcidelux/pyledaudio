DISPLAY_FREQUENCY = 30
N_FFT_BINS = 12

""" Set the configuration for the audio visualization."""


def set_config(config: dict):
    global DISPLAY_FREQUENCY, N_FFT_BINS
    DISPLAY_FREQUENCY = config.get('DISPLAY_FREQUENCY', DISPLAY_FREQUENCY)
    N_FFT_BINS = config.get('N_FFT_BINS', N_FFT_BINS)

    # Print all global variables defined in this file
    print("Current configuration:")
    print(f"DISPLAY_FREQUENCY: {DISPLAY_FREQUENCY}")
    print(f"N_FFT_BINS: {N_FFT_BINS}")
