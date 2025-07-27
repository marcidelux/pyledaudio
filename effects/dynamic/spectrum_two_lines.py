from dataclasses import dataclass
from typing import Optional, List
from ..utils import (
    Command,
    Effect,
    colors,
    Pixel,
    DigitalPyramid,
    AudioInfo
)


@dataclass
class EffectConfig:
    name: str
    colors: list[Pixel] = None


class SpectrumTwoLines(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(name="SpectrumTwoLines", colors=[
            colors.RED, colors.GREEN,
            colors.BLUE, colors.YELLOW,
            colors.CYAN, colors.MAGENTA,
            colors.WHITE, colors.ORANGE
        ])
        self.idx_mod = 0
        self.beat_cntr = 0

    def update(self, audio_info: Optional[AudioInfo] = None) -> None:
        if audio_info is None:
            return None

        self.pyramid.clear()
        num_bands = len(audio_info.bands)

        if audio_info.beat_detected:
            self.idx_mod += 1
            self.beat_cntr += 1
            if self.beat_cntr >= 8:
                self.idx_mod = 0
                self.beat_cntr = 0

        for i in range(8):
            idx = (i + self.idx_mod) % 8
            color_idx = (i) % len(self.config.colors)
            pixel = self.config.colors[color_idx].set_intensity(
                audio_info.bands[i % num_bands])
            self.pyramid.two_lines_body_groups[idx].set_all(pixel)

    def get_commands(self) -> List[Command]:
        return self.pyramid.cmds
