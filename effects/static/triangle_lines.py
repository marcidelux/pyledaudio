import time
from dataclasses import dataclass
from typing import List, Optional
from ..utils import (
    Command,
    Effect,
    Line,
    PixelArray,
    PixelArrayView,
    colors
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float


class TriangleLines(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="TriangleLines",
            update_speed=0.05,
        )

        self.triangle = PixelArray(180)
        # A1 0-29, C1 30-89, C2 90-149, A2 150-179
        self.view_A_1 = PixelArrayView(self.triangle, 0, 30)
        self.view_C_1 = PixelArrayView(self.triangle, 30, 60)
        self.view_C_2 = PixelArrayView(self.triangle, 90, 60, True)
        self.view_A_2 = PixelArrayView(self.triangle, 150, 30, True)
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
        self.lines: list[Line] = []

    def calculate(self) -> None:
        self.triangle.set_all(colors.BLACK)
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

        self.animation_index += 1

    def update(self, band_levels: Optional[bytes] = None) -> List[Command]:
        current_time = time.time()
        if current_time - self.previous_time >= self.config.update_speed:
            self.previous_time = current_time
            self.calculate()
        return [
            self.cmd_A_1,
            self.cmd_C_1,
            self.cmd_A_2,
            self.cmd_C_2
        ]


triangleLines = TriangleLines()
