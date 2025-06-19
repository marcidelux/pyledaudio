from dataclasses import dataclass
from typing import Optional, List
from ..utils import (
    Command,
    Effect,
    PixelArray,
    PixelArrayView,
    colors,
    Pixel
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
        self.section_A = PixelArray(240)
        self.radial_A0 = PixelArrayView(self.section_A, 0, 30)
        self.radial_A1 = PixelArrayView(self.section_A, 30, 30)
        self.radial_A2 = PixelArrayView(self.section_A, 60, 30)
        self.radial_A3 = PixelArrayView(self.section_A, 90, 30)
        self.radial_A4 = PixelArrayView(self.section_A, 120, 30)
        self.radial_A5 = PixelArrayView(self.section_A, 150, 30)
        self.radial_A6 = PixelArrayView(self.section_A, 180, 30)
        self.radial_A7 = PixelArrayView(self.section_A, 210, 30)
        self.radials = [
            self.radial_A0, self.radial_A1, self.radial_A2,
            self.radial_A3, self.radial_A4, self.radial_A5,
            self.radial_A6, self.radial_A7
        ]

        self.command = Command(Command.COMMAND_TYPE_FULL_SECTION,
                               Command.SECTION_ID_A, bytearray([0, 2, 4, 6]), self.section_A)

    def update(self, band_levels: Optional[bytes] = None) -> List[Command]:
        if band_levels is None:
            return [self.command]
        num_bands = len(band_levels)

        for i, radial in enumerate(self.radials):
            pixel = self.config.colors[i % len(
                self.config.colors)].set_intensity(band_levels[i % num_bands])
            radial[:] = pixel

        return [self.command]


spectrum_octagon = SpectrumOctagon()
