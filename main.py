import config
from audio import config as audio_config, process
from udp import udp_client, protocol
from udp import config as output_config
import numpy as np
from api import server, config as api_config

def send_bands_to_client(band_levels):
    # Only put data into queue if ready
    if server.broadcast_queue is not None:
        server.broadcast_queue.put_nowait(band_levels)

def process_audio_and_send(audio_chunk: np.ndarray) -> None:
    band_levels = process.create_band_levels(audio_chunk)
    send_bands_to_client(band_levels)
    print(band_levels)

def init():
    audio_config.set_config(config.get_config_dict())
    output_config.set_config(config.get_config_dict())
    api_config.set_config(config.get_config_dict())
    process.init()
    server.start()

if __name__ == "__main__":
    init()
    process.start_stream(process_audio_and_send)












def send_three_colors(c1, c2, c3):
    # Store the previous values
    if not hasattr(send_three_colors, "prev_colors"):
        send_three_colors.prev_colors = (None, None, None)

    # Check if the values have changed
    if (c1, c2, c3) != send_three_colors.prev_colors:
        protocol.command_segments_A.set_pixel(0, protocol.Color(c1, 0, 0))
        protocol.command_segments_A.set_pixel(1, protocol.Color(0, c2, 0))
        protocol.command_segments_A.set_pixel(2, protocol.Color(0, 0, c3))
        udp_client.send_command(protocol.command_segments_A)
        # Update the previous values
        send_three_colors.prev_colors = (c1, c2, c3)
        #print(f"Sent colors: {c1}, {c2}, {c3}")