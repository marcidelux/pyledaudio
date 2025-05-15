UDP_IP = '192.168.100.150'
"""IP address of the ESP32"""
UDP_PORT = 12345
"""Port number used for socket communication between Python and ESP32"""

def set_config(config:dict):
    global UDP_IP, UDP_PORT
    UDP_IP = config.get('UDP_IP', UDP_IP)
    UDP_PORT = config.get('UDP_PORT', UDP_PORT)
    print(f"UDP_IP: {UDP_IP}")
    print(f"UDP_PORT: {UDP_PORT}")