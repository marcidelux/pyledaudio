import time
from dataclasses import dataclass
from typing import List
from ..utils import (
    Command,
    Effect,
    Pixel,
    DigitalPyramid,
    Colors,
    Particle
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


class BottomTriangles(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="BottomTriangles",
            update_speed=0.03,
            colors=[Pixel(255, 0, 0), Pixel(0, 255, 0), Pixel(0, 0, 255)]
        )
        self.pyramid = DigitalPyramid()
        self.previous_time = time.time()
        self.spawn_time = 0.5
        self.time_count_up = 0

    def update(self) -> List[Command] | None:
        if time.time() - self.previous_time < self.config.update_speed:
            return None
        self.previous_time = time.time()
        self.time_count_up += self.config.update_speed

        if self.time_count_up >= self.spawn_time:
            self.time_count_up = 0
            particle1 = Particle(
                color=self.config.colors[0],
                position=0,
                direction=1,
                lifetime=7.0,
                update_speed=0.05,
                speed=1,
                time_of_creation=self.previous_time
            )
            self.pyramid.lines_A[0].add_particle(particle1)

            particle3 = Particle(
                color=self.config.colors[2],
                position=0,
                direction=1,
                lifetime=7.0,
                update_speed=0.05,
                speed=2,
                time_of_creation=self.previous_time
            )
            self.pyramid.lines_A[0].add_particle(particle3)

        self.pyramid.update(self.previous_time)

        return [self.pyramid.cmd_A, self.pyramid.cmd_B, self.pyramid.cmd_C]


bottom_triangles = BottomTriangles()
