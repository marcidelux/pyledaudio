import socket
import time

# Target ESP32 IP and port
UDP_IP = "192.168.60.150"
UDP_PORT = 12345

# LED counts
LED_COUNT_A = 240
LED_COUNT_B = 176
LED_COUNT_C = 480

# Buffers
BUFFER_SIZE_A = LED_COUNT_A * 3
BUFFER_SIZE_B = LED_COUNT_B * 3
BUFFER_SIZE_C = LED_COUNT_C * 3

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

packet_id = 0
position_A = 0
position_B = 0
position_C = 0


def create_frame(strip_id, led_count, r, g, b, position):
    buffer = bytearray()
    buffer.append(packet_id)   # Packet ID
    buffer.append(strip_id)   # Strip ID

    for i in range(led_count):
        if i == position:
            buffer += bytes([r, g, b])
        else:
            buffer += bytes([0, 0, 0])

    return buffer


try:
    while True:
        # Strip A - Red
        frame_a = create_frame(0, LED_COUNT_A, 255, 0, 0, position_A)
        sock.sendto(frame_a, (UDP_IP, UDP_PORT))

        # Strip B - Green
        frame_b = create_frame(1, LED_COUNT_B, 0, 255, 0, position_B)
        sock.sendto(frame_b, (UDP_IP, UDP_PORT))

        # Strip C - Blue
        frame_c = create_frame(2, LED_COUNT_C, 0, 0, 255, position_C)
        sock.sendto(frame_c, (UDP_IP, UDP_PORT))

        time.sleep(0.03)  # ~33 FPS

        # Update positions
        position_A = (position_A + 1) % LED_COUNT_A
        position_B = (position_B + 1) % LED_COUNT_B
        position_C = (position_C + 1) % LED_COUNT_C

        packet_id += 1
        if packet_id >= 255:
            packet_id = 0

except KeyboardInterrupt:
    print("Stopped by user.")
