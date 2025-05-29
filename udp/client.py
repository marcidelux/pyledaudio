import socket
from . import config


class UdpClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(0)
        self.socket.settimeout(0.1)

    def send_bytes(self, data: bytes):
        try:
            self.socket.sendto(data, (config.UDP_IP, config.UDP_PORT))
        except Exception as e:
            print(f"An error occurred: {e}")


udp_client = UdpClient()
