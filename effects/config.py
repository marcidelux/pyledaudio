FPS = 30
N_FFT_BINS = 12

""" Set the configuration for the audio visualization."""
def set_config(config:dict):
    global FPS, N_FFT_BINS
    FPS = config.get('FPS', FPS)
    N_FFT_BINS = config.get('N_FFT_BINS', N_FFT_BINS)

    # Print all global variables defined in this file
    print("Current configuration:")
    print(f"FPS: {FPS}")
    print(f"N_FFT_BINS: {N_FFT_BINS}")