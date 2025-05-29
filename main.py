import config

from audio import config as audio_config, process
from effects import config as effects_config
from effects.effects_manager import effect_manager
from effects import protocol
from udp import config as udp_config
from udp.client import udp_client
from api import server, config as api_config

import numpy as np
import time

music_turned_off = False
last_time = time.time()
switch_time = 10


def send_bands_to_client(band_levels: bytes) -> None:
    # Only put data into queue if ready
    if server.broadcast_queue is not None:
        server.broadcast_queue.put_nowait(band_levels)


def send_leds_to_client(data: bytes) -> None:
    # Only put data into queue if ready
    if server.leds_broadcast_queue is not None:
        server.leds_broadcast_queue.put_nowait(data)


def display_effects(audio_chunk: np.ndarray) -> None:
    global last_time, switch_time
    current_time = time.time()
    effect = effect_manager.current()
    if current_time - last_time >= switch_time:
        last_time = current_time
        effect = effect_manager.next_effect()
        send_leds_to_client(protocol.cmd_turn_off.to_bytes())

    band_levels = process.create_band_levels(audio_chunk)
    effect.update(band_levels)

    if band_levels is not None:
        send_bands_to_client(band_levels)

    for command in effect.get_commands():
        cmd_bytes = command.to_bytes()
        send_leds_to_client(cmd_bytes)
        udp_client.send_bytes(cmd_bytes)


def init():
    conf_dict = config.get_config_dict()
    audio_config.set_config(conf_dict)
    udp_config.set_config(conf_dict)
    api_config.set_config(conf_dict)
    effects_config.set_config(conf_dict)
    process.init()
    server.start()


if __name__ == "__main__":
    init()
    process.start_stream(display_effects)
    # static_triangle_effect()
    # process.start_stream(process_audio_and_send)
    # test()
    # static_effects()

    """
    def process_audio_and_send(audio_chunk: np.ndarray) -> None:
    global music_turned_off

    band_levels = process.create_band_levels(audio_chunk)
    if band_levels is None:
        if not music_turned_off:
            music_turned_off = True
            send_leds_to_client(protocol.cmd_turn_off.to_bytes())
            print("Music turned off")
        return
    music_turned_off = False

    send_bands_to_client(band_levels)

    spectrumEffect.calculate(band_levels)
    for command in spectrumEffect.get_commands():
        send_leds_to_client(command.to_bytes())
        #udp_client.send_bytes(command.to_bytes())
    
    #udp_client.send_bytes(spectrumEffect.two_segments_A.to_bytes())
    #udp_client.send_bytes(spectrumEffect.two_segments_C.to_bytes())

def static_triangle_effect():
    while True:
        if (triangleEffect.update()):
            for command in triangleEffect.get_commands():
                send_leds_to_client(command.to_bytes())
        time.sleep(0.02)

def active_triangle_effect(audio_chunk: np.ndarray) -> None:
    band_levels = process.create_band_levels(audio_chunk)
    if (triangleEffect.update(band_levels)):
        for command in triangleEffect.get_commands():
            send_leds_to_client(command.to_bytes())
"""
