import socket
from . import config


class UdpClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.socket.settimeout(0.01)

    def send_bytes(self, data: bytes):
        try:
            self.socket.sendto(data, (config.UDP_IP, config.UDP_PORT))
        except Exception as e:
            pass


udp_client = UdpClient()
