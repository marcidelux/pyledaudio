N_FFT_BINS = 3
SERVER_IP = '0.0.0.0'
SERVER_PORT = 9999


def set_config(config: dict):
    global N_FFT_BINS, SERVER_IP, SERVER_PORT
    SERVER_IP = config.get('SERVER_IP', SERVER_IP)
    SERVER_PORT = config.get('SERVER_PORT', SERVER_PORT)
    N_FFT_BINS = config.get('N_FFT_BINS', N_FFT_BINS)

    print("#### API ### - Current configuration:")
    print(f"SERVER_IP: {SERVER_IP}")
    print(f"SERVER_PORT: {SERVER_PORT}")
    print(f"N_FFT_BINS: {N_FFT_BINS}\n")
