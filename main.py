import config

from audio import config as audio_config, process
from effects.spectrums import spectrumEffect
from effects.test import testEffects
from udp import config as udp_config, udp_client
from api import server, config as api_config

import numpy as np
import time

music_turned_off = False

def send_bands_to_client(band_levels: bytes) -> None:
    # Only put data into queue if ready
    if server.broadcast_queue is not None:
        server.broadcast_queue.put_nowait(band_levels)

def send_leds_to_client(data: bytes) -> None:
    # Only put data into queue if ready
    if server.leds_broadcast_queue is not None:
        server.leds_broadcast_queue.put_nowait(data)

def process_audio_and_send(audio_chunk: np.ndarray) -> None:
    global music_turned_off

    band_levels = process.create_band_levels(audio_chunk)
    if band_levels is None:
        if not music_turned_off:
            music_turned_off = True
            send_leds_to_client(spectrumEffect.turn_off.to_bytes())
            print("Music turned off")
        return
    music_turned_off = False

    send_bands_to_client(band_levels)

    spectrumEffect.calculate(band_levels)
    send_leds_to_client(spectrumEffect.two_segments_A.to_bytes())
    send_leds_to_client(spectrumEffect.two_segments_C.to_bytes())
    
    #udp_client.send_bytes(spectrumEffect.two_segments_A.to_bytes())
    #udp_client.send_bytes(spectrumEffect.two_segments_C.to_bytes())

def test():
    while True:
        testEffects.demo_full_section_A()
        testEffects.demo_full_section_B()
        testEffects.demo_full_section_C()
        send_leds_to_client(testEffects.command_full_section_A.to_bytes())
        send_leds_to_client(testEffects.command_full_section_B.to_bytes())
        send_leds_to_client(testEffects.command_full_section_C.to_bytes())
        time.sleep(0.05)

def init():
    audio_config.set_config(config.get_config_dict())
    udp_config.set_config(config.get_config_dict())
    api_config.set_config(config.get_config_dict())
    process.init()
    server.start()
    udp_client.init()

if __name__ == "__main__":
    init()
    process.start_stream(process_audio_and_send)
    #test()