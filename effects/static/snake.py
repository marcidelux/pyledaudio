import time
from dataclasses import dataclass
from typing import Optional, List
import random
from ..utils import (
    Command,
    Effect,
    DigitalPyramid,
    colors,
    Pixel,
    Particle,
    EndType,
    GateMode
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


class Snake(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="Snake",
            update_speed=0.03,
            colors=[
                colors.RED, colors.GREEN,
                colors.BLUE, colors.YELLOW,
                colors.CYAN, colors.MAGENTA,
                colors.WHITE, colors.ORANGE
            ]
        )
        self.previous_time = time.time()
        self.previous_spawn_time = self.previous_time
        self.spawn_time = 1

        self.pyramid.lines_A.set_gates_mode(GateMode.ARROW)
        self.pyramid.lines_B.set_gates_mode(GateMode.ARROW)
        self.pyramid.lines_C.set_gates_mode(GateMode.ARROW)

        self.pyramid.connect_all_particle_lines()

    def update(self) -> None:
        current_time = time.time()

        if current_time - self.previous_time < self.config.update_speed:
            return None

        if current_time >= self.previous_spawn_time + self.spawn_time:
            self.previous_spawn_time = current_time
            random_A_index = random.randint(0, 7)
            color = random.choice(self.config.colors)
            length = random.randint(2, 5)
            for i in range(length):
                particle = Particle(
                    color=color,
                    position=i,
                    direction=1,
                    lifetime=8,
                    update_speed=0.03,
                    speed=1,
                    fade_time=1,
                    time_of_creation=current_time,
                )
                self.pyramid.lines_A[random_A_index].add_particle(particle)
                self.pyramid.lines_A[(random_A_index + 4) %
                                     8].add_particle(particle)

        self.pyramid.update(current_time)
        self.previous_time = current_time

    def get_commands(self) -> List[Command]:
        return self.pyramid.cmds


snake = Snake()
