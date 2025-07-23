import config

from audio import config as audio_config
from audio.process import audioProcessor, AudioInfo
from effects import config as effects_config
from effects.effects_manager import effect_manager
from effects.utils import cmd_turn_off, Command
from udp import config as udp_config
from udp.client import udp_client
from api import server, config as api_config
from api.broadcasters import bands_queue, leds_queue
from state import state_manager
from typing import List
import numpy as np
import time


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


def send_bands_to_client(band_levels: bytes) -> None:
    # Only put data into queue if ready
    if bands_queue is not None:
        bands_queue.put_nowait(band_levels)


def send_leds_to_client(data: bytes) -> None:
    # Only put data into queue if ready
    if leds_queue is not None:
        leds_queue.put_nowait(data)


def display_bands(audio_chunk: np.ndarray) -> None:
    # count_fps()
    band_levels = audioProcessor.create_band_levels(audio_chunk)
    if band_levels == None:
        return
    send_bands_to_client(band_levels)


def display_effects(audio_info: AudioInfo) -> None:
    commands: List[Command] = None

    if audio_info.bands is None:
        return

    send_bands_to_client(audio_info.bands)

    if effect_manager.current_primary_effect.is_dynamic:
        effect_manager.current_primary_effect.update(audio_info)
    else:
        effect_manager.current_primary_effect.update()

    is_double_effect = effect_manager.current_secondary_effect is not None

    if is_double_effect:
        if effect_manager.current_secondary_effect.is_dynamic:
            effect_manager.current_secondary_effect.update(audio_info)
        else:
            effect_manager.current_secondary_effect.update()

        commands = effect_manager.current_primary_effect.pyramid.combine(
            effect_manager.current_secondary_effect.pyramid
        )
    else:
        commands = effect_manager.current_primary_effect.get_commands()

    if commands is not None:
        for command in commands:
            cmd_bytes = command.to_bytes()
            send_leds_to_client(cmd_bytes)


def on_effect_change() -> None:
    send_leds_to_client(cmd_turn_off.to_bytes())
    print("Effect changed")


def init():
    audioProcessor.list_audio_devices()

    conf_dict = config.get_config_dict()
    audio_config.set_config(conf_dict)
    udp_config.set_config(conf_dict)
    api_config.set_config(conf_dict)
    effects_config.set_config(conf_dict)

    audioProcessor.setup(display_effects)
    effect_manager.set_on_change_callback(on_effect_change)

    server.start()
    audioProcessor.start()

    print("Server started")


if __name__ == "__main__":
    init()

    try:
        while True:
            time.sleep(1)  # Prevents busy waiting
    except KeyboardInterrupt:
        print("Shutting down...")
        audioProcessor.stop()
        audioProcessor.terminate()
