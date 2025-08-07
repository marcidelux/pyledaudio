from dataclasses import dataclass
from typing import Optional
from ..utils import (
    PyramidSimpleCommands,
    Effect,
    colors,
    Pixel,
    AudioInfo
)


@dataclass
class EffectConfig:
    name: str
    colors: list[Pixel] = None


class SpectrumTriangles(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(name="SpectrumTriangles", colors=[
            colors.RED, colors.GREEN,
            colors.BLUE, colors.YELLOW,
            colors.CYAN, colors.MAGENTA,
            colors.WHITE
        ])
        self.idx_mod = 0
        self.pixel_mod = 0
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
                self.pixel_mod += 1

        for i in range(4):
            idx = (i * 2 + self.idx_mod) % 8
            color_idx = (i + self.pixel_mod) % len(self.config.colors)
            pixel = self.config.colors[color_idx].set_intensity(
                audio_info.bands[i % num_bands])
            self.pyramid.triangle_bottom_groups[idx].set_all(pixel)
            self.pyramid.triangle_side_groups[idx].set_all(pixel)

    def get_commands(self) -> PyramidSimpleCommands:
        return self.pyramid.cmds
