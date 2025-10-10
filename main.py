import config

from audio import config as audio_config
from audio.jackconnector import audioProcessor, AudioInfo
from effects import config as effects_config
from effects.effects_manager import effect_manager
from effects.utils import cmd_off, PyramidSimpleCommands
from api import server, config as api_config
from api.broadcasters import timer_bands_queue, timer_leds_queue
from state import state_manager
from typing import List
import numpy as np
import time
import random

fpscntr = 0
last_time = time.time()
last_time_next_effect = time.time()
packet_id: np.uint8 = 0


def count_fps(now) -> None:
    global fpscntr, last_time
    if now - last_time >= 1:
        print(f"FPS: {fpscntr}")
        fpscntr = 0
        last_time = now
    else:
        fpscntr += 1


def send_bands_data(band_levels: bytes) -> None:
    if timer_bands_queue is not None:
        timer_bands_queue.put_nowait(band_levels)


def send_leds_data(data: bytes) -> None:
    if timer_leds_queue is not None:
        timer_leds_queue.put_nowait(data)


def increment_packet_id() -> None:
    global packet_id
    packet_id += 1
    if packet_id >= 255:
        packet_id = 0


def apply_brightness_to_commands(commands: PyramidSimpleCommands) -> None:
    """Applies the current brightness setting to the commands."""
    if state_manager.brightness == 255:
        return

    fade = np.clip(state_manager.brightness / 255.0, 0, 1)

    commands.cmd_A.pixels.set_fade(fade)
    commands.cmd_B.pixels.set_fade(fade)
    commands.cmd_C.pixels.set_fade(fade)


def next_time_counter(now) -> None:
    global last_time_next_effect

    if now - last_time_next_effect >= state_manager.step_time:
        effect_manager.random_effect_pair()
        last_time_next_effect = now
        state_manager.step_time = random.uniform(30, 60)


def display_effects(audio_info: AudioInfo) -> None:
    global packet_id, state_manager

    now = time.time()
    count_fps(now)
    next_time_counter(now)

    commands: PyramidSimpleCommands = None

    if state_manager.power is False:
        if state_manager.power_changed:
            state_manager.power_changed = False
            send_leds_data((
                cmd_off.cmd_A.to_bytes(),
                cmd_off.cmd_B.to_bytes(),
                cmd_off.cmd_C.to_bytes()
            ))
        return

    if audio_info.bands is None:
        if state_manager.no_sound:
            return
        else:
            state_manager.no_sound_cntr += 1
    else:
        state_manager.no_sound_cntr = 0
        state_manager.no_sound = False

    if state_manager.no_sound_cntr > config.DISPLAY_FREQUENCY:
        state_manager.no_sound = True
        send_leds_data((
            cmd_off.cmd_A.to_bytes(),
            cmd_off.cmd_B.to_bytes(),
            cmd_off.cmd_C.to_bytes()
        ))
        return

    send_bands_data(audio_info.bands)

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
        increment_packet_id()
        commands.set_packet_ids(packet_id)
        apply_brightness_to_commands(commands)

        send_leds_data((
            commands.cmd_A.to_bytes(),
            commands.cmd_B.to_bytes(),
            commands.cmd_C.to_bytes()
        ))


def on_effect_change() -> None:
    print("Effect changed")


def init():
    audioProcessor.list_audio_devices()
    conf_dict = config.get_config_dict()
    audio_config.set_config(conf_dict)
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
