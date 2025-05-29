from .protocol import Command, PixelArray, PixelArrayView, Color

from typing import List, Optional
from abc import ABC, abstractmethod
import time
import random


class EffectStatic(ABC):
    @abstractmethod
    def update(self) -> None:
        """Calculate the effect based on the provided band levels."""
        pass

    @abstractmethod
    def get_commands(self) -> List[Command]:
        """Return a list of commands to be sent to the LED strips."""
        pass


class Line:
    def __init__(self, start_index: int):
        self.index = start_index
        self.colors = random.sample(Color.PALETTE, 4)  # pick 4 unique colors

    def set_intensity(self, intensity: int):
        self.colors = [color.set_intensity(intensity) for color in self.colors]

    def advance(self):
        self.index += 1


class Triangle(EffectStatic):
    def __init__(self):
        self.triangle = PixelArray(180)
        self.view_A_1 = PixelArrayView(self.triangle, 0, 30)    # 0 - 29
        self.view_C_1 = PixelArrayView(self.triangle, 30, 60)   # 30 - 89
        self.view_C_2 = PixelArrayView(
            self.triangle, 90, 60, True)   # 90 - 149
        self.view_A_2 = PixelArrayView(
            self.triangle, 150, 30, True)  # 150 - 179
        self.view_A_1_index = 0
        self.view_C_1_index = 0
        self.view_A_2_index = 4
        self.view_C_2_index = 4
        self.cmd_A_1 = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT, Command.SECTION_ID_A, bytearray(
            [self.view_A_1_index]), self.view_A_1)
        self.cmd_C_1 = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT, Command.SECTION_ID_C, bytearray(
            [self.view_C_1_index]), self.view_C_1)
        self.cmd_A_2 = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT, Command.SECTION_ID_A, bytearray(
            [self.view_A_2_index]), self.view_A_2)
        self.cmd_C_2 = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT, Command.SECTION_ID_C, bytearray(
            [self.view_C_2_index]), self.view_C_2)
        self.animation_index = 0
        self.previous_time = time.time()
        self.update_speed = 0.05  # seconds
        self.lines: list[Line] = []

    def calculate(self, band_levels: bytes) -> None:
        self.triangle.set_all(Color.BLACK)
        # Move and draw each line
        new_lines = []
        for line in self.lines:
            if line.index < self.triangle.length:
                for i, color in enumerate(line.colors):
                    idx = (line.index + i) % self.triangle.length
                    self.triangle[idx] = color
                line.advance()
                new_lines.append(line)  # keep it alive
        self.lines = new_lines

        # Spawn new line every 10 ticks
        if self.animation_index % 10 == 0:
            new_line = Line(0)
            self.lines.append(new_line)

        for i, line in enumerate(self.lines):
            level = band_levels[i % len(band_levels)] if band_levels else 10
            line.set_intensity(level)

        self.animation_index += 1

    def update(self, band_levels: Optional[bytes] = None) -> None:
        current_time = time.time()
        if current_time - self.previous_time >= self.update_speed:
            self.previous_time = current_time
            self.calculate(band_levels)
            return True
        return False

    def get_commands(self) -> list[Command]:
        return [self.cmd_A_1, self.cmd_C_1, self.cmd_A_2, self.cmd_C_2]


triangleEffect = Triangle()
