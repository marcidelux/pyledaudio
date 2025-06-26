from dataclasses import dataclass
from typing import Optional, List
from ..utils import (
    Command,
    Effect,
    PixelArray,
    PixelArrayView,
    colors,
    Pixel,
    AudioInfo
)


@dataclass
class EffectConfig:
    name: str
    colors: list[Pixel] = None


class Spectrum4(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(name="Spectrum4", colors=[
            colors.RED, colors.GREEN,
            colors.BLUE, colors.YELLOW,
            colors.CYAN, colors.MAGENTA,
            colors.WHITE
        ])

        self.spectrum = PixelArray(90)
        self.view_A = PixelArrayView(self.spectrum, 0, 30)
        self.view_C = PixelArrayView(self.spectrum, 30, 60)

        self.segments_A = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT,
                                  Command.SECTION_ID_A, bytearray([0, 2, 4, 6]), self.view_A)
        self.segments_C = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT,
                                  Command.SECTION_ID_C, bytearray([0, 2, 4, 6]), self.view_C)

    def update(self, audio_info: Optional[AudioInfo] = None) -> List[Command]:
        if audio_info is None:
            return [self.segments_A, self.segments_C]
        num_bands = len(audio_info.bands)
        leds_per_band = len(self.spectrum) // num_bands
        for i, level in enumerate(audio_info.bands):
            pixel = self.config.colors[i % len(
                self.config.colors)].set_intensity(level)
            # Calculate LED start index for this band
            start = i * leds_per_band
            end = start + leds_per_band
            # Set the pixels for this band
            self.spectrum[start:end] = pixel

        return [self.segments_A, self.segments_C]


spectrum4 = Spectrum4()
