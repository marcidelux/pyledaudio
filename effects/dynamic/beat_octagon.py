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
    AudioInfo,
    Particle,
    EndType
)


@dataclass
class EffectConfig:
    name: str
    colors: list[Pixel] = None


class BeatOctagon(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(name="BeatOctagon", colors=[
            colors.RED, colors.GREEN,
            colors.BLUE, colors.YELLOW,
            colors.CYAN, colors.MAGENTA,
            colors.WHITE, colors.ORANGE
        ])
        self.pyramid = DigitalPyramid()
        self.previous_time = time.time()

        for i in range(8):
            self.pyramid.lines_B[i].gate_tail.append(
                (self.pyramid.lines_B[(i+1) % 8], EndType.HEAD)
            )

    def update(self, audio_info: Optional[AudioInfo] = None) -> List[Command] | None:
        if audio_info is None:
            return None

        current_time = time.time()

        if audio_info.beat_detected:
            random_color = random.choice(self.config.colors)
            lifetime = random.uniform(1, 10)
            # random_index = random.randint(0, 7)
            random_speed = random.randint(1, 3)
            random_update_speed = random.uniform(0.03, 0.1)

            particle = Particle(
                color=random_color,
                position=0,
                direction=1,
                lifetime=5,
                update_speed=0.05,
                speed=1,
                time_of_creation=current_time
            )
            particle2 = Particle(
                color=random_color,
                position=2,
                direction=1,
                lifetime=5.5,
                update_speed=0.05,
                speed=1,
                time_of_creation=current_time
            )

            self.pyramid.lines_B[0].add_particle(particle)
            self.pyramid.lines_B[0].add_particle(particle2)
            self.pyramid.lines_B[4].add_particle(particle)
            self.pyramid.lines_B[4].add_particle(particle2)

            self.pyramid.lines_B.jump_particles(3)

        self.pyramid.update(self.previous_time)
        self.previous_time = current_time

        return self.pyramid.cmds


beat_octagon = BeatOctagon()
