from dataclasses import dataclass
from typing import Optional, List
from ..utils import (
    Command,
    Effect,
    colors,
    Pixel,
    DigitalPyramid
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

        self.pyramid = DigitalPyramid()

    def update(self, band_levels: Optional[bytes] = None) -> List[Command]:
        print("Updating SpectrumTriangles with band_levels:", band_levels)
        if band_levels is None:
            return [self.pyramid.cmd_A, self.pyramid.cmd_B, self.pyramid.cmd_C]
        num_bands = len(band_levels)

        for i in range(8):
            pixel = self.config.colors[i % len(self.config.colors)].set_intensity(
                band_levels[i % num_bands])
            self.pyramid.body_tetrahedron_groups[i].set_all(pixel)

        return [self.pyramid.cmd_A, self.pyramid.cmd_B, self.pyramid.cmd_C]


spectrum_triangles = SpectrumTriangles()
