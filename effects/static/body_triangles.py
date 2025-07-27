import time
from dataclasses import dataclass
from typing import List
from ..utils import (
    Command,
    Effect,
    Pixel,
    DigitalPyramid,
    Colors
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


class BodyTriangles(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="BodyTriangles",
            update_speed=0.03,
            colors=[Pixel(255, 0, 0), Pixel(0, 255, 0), Pixel(0, 0, 255)]
        )
        self.previous_time = time.time()
        self.pixel_index = 0
        self.triangle_index = 0

    def update(self) -> None:
        if time.time() - self.previous_time < self.config.update_speed:
            return None

        self.pyramid.section_A.set_all(Colors.BLACK)
        self.pyramid.section_C.set_all(Colors.BLACK)

        self.pixel_index += 1
        if self.pixel_index >= len(self.pyramid.triangle_body_groups[0]):
            self.pixel_index = 0
            self.triangle_index += 1
            if self.triangle_index >= len(self.pyramid.triangle_body_groups):
                self.triangle_index = 0

        self.pyramid.triangle_body_groups[self.triangle_index][self.pixel_index] = Colors.RED

        self.previous_time = time.time()

    def get_commands(self) -> List[Command]:
        return [self.pyramid.cmd_A, self.pyramid.cmd_C]
