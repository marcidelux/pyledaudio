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
    Particle
)


@dataclass
class EffectConfig:
    name: str
    colors: list[Pixel] = None


class SpectrumOctagon(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(name="SpectrumOctagon", colors=[
            colors.RED, colors.GREEN,
            colors.BLUE, colors.YELLOW,
            colors.CYAN, colors.MAGENTA,
            colors.WHITE, colors.ORANGE
        ])
        self.pyramid = DigitalPyramid()

    def update(self, audio_info: Optional[AudioInfo] = None) -> List[Command] | None:
        self.pyramid.clear()
        for i in range(4):
            intensity = (audio_info.bands[i * 2] +
                         audio_info.bands[i * 2 + 1]) / 2
            self.pyramid.triangle_body_groups[i].set_all(
                self.config.colors[i % len(self.config.colors)].set_intensity(intensity))

        return self.pyramid.cmds


spectrum_octagon = SpectrumOctagon()
