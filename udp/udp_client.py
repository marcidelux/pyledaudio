import socket
from . import config
from .protocol import Command

# Create a UDP socket
udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_command(command: Command):
    try:
        # Convert the command to bytes and send it to the UDP server
        udp_client.sendto(command.to_bytes(), (config.UDP_IP, config.UDP_PORT))
    except Exception as e:
        print(f"An error occurred: {e}")