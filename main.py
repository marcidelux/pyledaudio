import config

from audio import config as audio_config
from audio.process import audioProcessor, AudioInfo
from effects import config as effects_config
from effects.effects_manager import effect_manager
from effects.utils import cmd_turn_off
from udp import config as udp_config
from udp.client import udp_client
from api import server, config as api_config
from state import state_manager

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


fpscntr = 0
last_time = time.time()


def count_fps() -> None:
    global fpscntr, last_time
    current_time = time.time()
    if current_time - last_time >= 1:
        print(f"FPS: {fpscntr}")
        fpscntr = 0
        last_time = current_time
    else:
        fpscntr += 1


def display_bands(audio_chunk: np.ndarray) -> None:
    # count_fps()
    band_levels = audioProcessor.create_band_levels(audio_chunk)
    if band_levels == None:
        return
    send_bands_to_client(band_levels)


def display_effects(audio_info: AudioInfo) -> None:
    effect = effect_manager.get_current()

    # count_fps()
    commands = None
    if effect.is_dynamic:
        # band_levels = audioProcessor.create_band_levels(audio_chunk)
        if audio_info.bands == None:
            return
        send_bands_to_client(audio_info.bands)
        commands = effect.update(audio_info)
    else:
        commands = effect.update()
    if commands is not None:
        for command in commands:
            cmd_bytes = command.to_bytes()
            send_leds_to_client(cmd_bytes)
            # udp_client.send_bytes(cmd_bytes)


def test_two_pyramids(audio_info: AudioInfo) -> None:
    effect = effect_manager.get_effect_by_name("Snake")
    effect2 = effect_manager.get_effect_by_name("BeatOctagon")

    commands = None
    if audio_info.bands is None:
        return

    effect.update()
    effect2.update(audio_info)

    commands = effect.pyramid.combine(effect2.pyramid)

    if commands is not None:
        for command in commands:
            cmd_bytes = command.to_bytes()
            send_leds_to_client(cmd_bytes)


def on_effect_change(effect_name: str) -> None:
    """
    Callback function to handle effect changes.
    This function is called when the effect is changed in the state manager.
    """
    print(f"Effect changed to: {effect_name}")
    effect_manager.set_current(effect_name)
    send_leds_to_client(cmd_turn_off.to_bytes())


def setup_hooks():
    state_manager.set_effect_callback(on_effect_change)


def init():
    audioProcessor.list_audio_devices()
    conf_dict = config.get_config_dict()
    audio_config.set_config(conf_dict)
    udp_config.set_config(conf_dict)
    api_config.set_config(conf_dict)
    effects_config.set_config(conf_dict)
    audioProcessor.setup(display_effects)
    setup_hooks()
    server.start()


if __name__ == "__main__":
    init()
    list_names = effect_manager.list_names()
    for name in list_names:
        print(f"Effect list: {name}")
        print(f"Elements: {effect_manager.get_list_elements(name)}")
    # effect_manager.switch_list("static")
    # effect_manager.next()
    audioProcessor.start()

    try:
        while True:
            time.sleep(1)  # Prevents busy waiting
    except KeyboardInterrupt:
        print("Shutting down...")
        audioProcessor.stop()
        audioProcessor.terminate()


"""

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
