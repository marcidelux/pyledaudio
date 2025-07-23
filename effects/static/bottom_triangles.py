import time
from dataclasses import dataclass
from typing import List
from ..utils import (
    Command,
    Effect,
    Pixel,
    DigitalPyramid,
    Colors,
    Particle,
    EndType
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
        self.previous_time = time.time()
        self.previous_spawn_time = self.previous_time
        self.spawn_time = 1

        self.pyramid.lines_A[0].gate_tail.append([
            (self.pyramid.lines_B[0], EndType.HEAD),
            (self.pyramid.lines_C[0], EndType.HEAD),
            (self.pyramid.lines_B[7], EndType.TAIL)
        ])
        self.pyramid.lines_B[0].gate_tail.append([
            (self.pyramid.lines_C[1], EndType.HEAD),
            (self.pyramid.lines_B[1], EndType.HEAD)
        ])

        self.pyramid.lines_B[7].gate_head.append([
            (self.pyramid.lines_C[7], EndType.HEAD),
            (self.pyramid.lines_B[6], EndType.TAIL)
        ])

    def update(self) -> None:
        current_time = time.time()

        if current_time - self.previous_time < self.config.update_speed:
            return None

        if current_time >= self.previous_spawn_time + self.spawn_time:
            self.previous_spawn_time = current_time
            particle1 = Particle(
                color=self.config.colors[0],
                position=0,
                direction=1,
                lifetime=10,
                update_speed=0.03,
                speed=1,
                time_of_creation=current_time
            )
            self.pyramid.lines_A[0].add_particle(particle1)

        self.pyramid.update(self.previous_time)

        self.previous_time = current_time

    def get_commands(self) -> List[Command]:
        return [self.pyramid.cmd_A, self.pyramid.cmd_B, self.pyramid.cmd_C]


bottom_triangles = BottomTriangles()
