import socket
from . import config

# Create a UDP socket
#udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_client = None

def init():
    global udp_client
    # Create a UDP socket
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the socket to non-blocking mode
    udp_client.setblocking(0)
    # Set the socket timeout to 0.1 seconds
    udp_client.settimeout(0.1)

def send_bytes(data: bytes):
    try:
        # Send the data to the UDP server
        udp_client.sendto(data, (config.UDP_IP, config.UDP_PORT))
    except Exception as e:
        print(f"An error occurred: {e}")