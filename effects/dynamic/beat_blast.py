import time
from dataclasses import dataclass
from typing import Optional, List
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


class BeatBlast(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(name="BeatBlast", colors=[
            colors.RED, colors.GREEN,
            colors.BLUE, colors.YELLOW,
            colors.CYAN, colors.MAGENTA,
            colors.WHITE
        ])
        self.pyramid = DigitalPyramid()
        self.previous_time = time.time()

        self.pyramid.lines_A[0].gate_tail.append([
            (self.pyramid.lines_B[1], EndType.HEAD),
            (self.pyramid.lines_C[0], EndType.HEAD),
            (self.pyramid.lines_B[7], EndType.TAIL),
        ])

        self.pyramid.lines_B[0].gate_tail.append([
            (self.pyramid.lines_C[1], EndType.HEAD),
            (self.pyramid.lines_B[1], EndType.HEAD),
        ])

        self.pyramid.lines_B[7].gate_head.append([
            (self.pyramid.lines_C[7], EndType.HEAD),
            (self.pyramid.lines_B[6], EndType.TAIL),
        ])

        # other side

        self.pyramid.lines_A[4].gate_tail.append([
            (self.pyramid.lines_B[4], EndType.HEAD),
            (self.pyramid.lines_C[4], EndType.HEAD),
            (self.pyramid.lines_B[3], EndType.TAIL),
        ])

        self.pyramid.lines_B[4].gate_tail.append([
            (self.pyramid.lines_C[5], EndType.HEAD),
            (self.pyramid.lines_B[5], EndType.HEAD),
        ])

        self.pyramid.lines_B[3].gate_head.append([
            (self.pyramid.lines_C[3], EndType.HEAD),
            (self.pyramid.lines_B[2], EndType.TAIL),
        ])

    def update(self, audio_info: Optional[AudioInfo] = None) -> List[Command] | None:
        current_time = time.time()

        if audio_info.beat_detected:
            # print("spawn beat particle", current_time)
            lifetime = 60 / audio_info.bpm
            if lifetime > 1:
                lifetime = 1
            else:
                lifetime *= 7

            particle1 = Particle(
                color=self.config.colors[0],
                position=0,
                direction=1,
                lifetime=lifetime,
                update_speed=0.03,
                speed=1,
                time_of_creation=current_time,
            )
            particle2 = Particle(
                color=self.config.colors[1],
                position=1,
                direction=1,
                lifetime=lifetime,
                update_speed=0.03,
                speed=1,
                time_of_creation=current_time,
            )

            self.pyramid.lines_A.add_particle(particle1)
            self.pyramid.lines_A.add_particle(particle2)

        self.pyramid.update(self.previous_time)
        # self.pyramid.lines_A.set_intensity(audio_info.bands[2])
        # self.pyramid.lines_B.set_intensity(audio_info.bands[3])
        # self.pyramid.lines_C.set_intensity(audio_info.bands[4])

        self.previous_time = current_time
        return [self.pyramid.cmd_A, self.pyramid.cmd_B, self.pyramid.cmd_C]


beat_blast = BeatBlast()
