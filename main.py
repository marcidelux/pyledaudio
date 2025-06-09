import config

from audio import config as audio_config
from audio.process import audioProcessor
from effects import config as effects_config
from effects.effects_manager import effect_manager
from udp import config as udp_config
from udp.client import udp_client
from api import server, config as api_config
from effects.utils import Command

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
    effect = effect_manager.get_current()
    commands = None
    if effect.is_dynamic:
        band_levels = audioProcessor.create_band_levels(audio_chunk)
        if band_levels == None:
            return
        send_bands_to_client(band_levels)
        commands = effect.update(band_levels)
    else:
        commands = effect.update()
    if commands is not None:
        for command in commands:
            cmd_bytes = command.to_bytes()
            send_leds_to_client(cmd_bytes)
            # udp_client.send_bytes(cmd_bytes)


def test_combination(audio_chunk: np.ndarray) -> None:
    band_levels = audioProcessor.create_band_levels(audio_chunk)
    effectA = effect_manager.get_effect_by_name("TriangleLines")
    effectB = effect_manager.get_effect_by_name("Spectrum4")
    commandsA = effectA.update(band_levels)
    commandsB = effectB.update(band_levels)

    for cmd in commandsA:
        print("cmd A:", cmd)
    for cmd in commandsB:
        print("cmd B:", cmd)

    # print(f"Commands A: {commandsA}\n, Commands B: {commandsB}")
    commands = merge_command_lists(commandsA, commandsB)

    for cmd in commands:
        print("cmd merged:", cmd)

    if commands is not None:
        for command in commands:
            cmd_bytes = command.to_bytes()
            send_leds_to_client(cmd_bytes)
            # udp_client.send_bytes(cmd_bytes)


def merge_command_lists(a: list[Command], b: list[Command]) -> list[Command]:
    result: list[Command] = []
    used_a = set()
    used_b = set()

    for i, cmd_a in enumerate(a):
        ids_a = set(cmd_a.segment_ids)
        for j, cmd_b in enumerate(b):
            if (i, j) in used_a or (j, i) in used_b:
                continue
            if cmd_a.type != cmd_b.type or cmd_a.section_id != cmd_b.section_id:
                continue

            ids_b = set(cmd_b.segment_ids)
            shared = ids_a & ids_b
            if not shared:
                continue

            combined = cmd_a + cmd_b  # List of 1–3 commands
            result.extend(combined)
            used_a.add(i)
            used_b.add(j)

    # Add remaining commands from A
    for i, cmd in enumerate(a):
        if i not in used_a:
            result.append(cmd)

    # Add remaining commands from B
    for j, cmd in enumerate(b):
        if j not in used_b:
            result.append(cmd)

    return result


def init():
    conf_dict = config.get_config_dict()
    audio_config.set_config(conf_dict)
    udp_config.set_config(conf_dict)
    api_config.set_config(conf_dict)
    effects_config.set_config(conf_dict)
    audioProcessor.init(test_combination)
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
