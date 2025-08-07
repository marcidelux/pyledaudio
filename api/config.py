N_FFT_BINS = 3
SERVER_IP = '0.0.0.0'
SERVER_PORT = 9999
UDP_IP = '192.168.100.150'
UDP_PORT = 12345


def set_config(config: dict):
    global N_FFT_BINS, SERVER_IP, SERVER_PORT, UDP_IP, UDP_PORT
    SERVER_IP = config.get('SERVER_IP', SERVER_IP)
    SERVER_PORT = config.get('SERVER_PORT', SERVER_PORT)
    N_FFT_BINS = config.get('N_FFT_BINS', N_FFT_BINS)
    UDP_IP = config.get('UDP_IP', UDP_IP)
    UDP_PORT = config.get('UDP_PORT', UDP_PORT)

    print("#### API ### - Current configuration:")
    print(f"SERVER_IP: {SERVER_IP}")
    print(f"SERVER_PORT: {SERVER_PORT}")
    print(f"N_FFT_BINS: {N_FFT_BINS}\n")
    print(f"UDP_IP: {UDP_IP}")
    print(f"UDP_PORT: {UDP_PORT}\n")
