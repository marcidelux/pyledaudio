import socket
import queue
import time
import threading

from . import config


class UdpClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(True)
        # self.socket.settimeout(0.001)

    def send_bytes(self, data: bytes):
        try:
            self.socket.sendto(data, (config.UDP_IP, config.UDP_PORT))
        except Exception as e:
            print(f"Error sending data via UDP: {e}")


udp_client = UdpClient()
