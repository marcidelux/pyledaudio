from .protocol import Command, Color, PixelArray, PixelArrayView
from typing import List, Optional
from abc import ABC, abstractmethod


class EffectDynamic(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the effect."""
        pass

    @abstractmethod
    def update(self, band_levels: Optional[bytes] = None) -> None:
        """Calculate the effect based on the provided band levels."""
        pass

    @abstractmethod
    def get_commands(self) -> List[Command]:
        """Return a list of commands to be sent to the LED strips."""
        pass


class SpectrumEffect(EffectDynamic):
    def __init__(self):
        self.spectrum = PixelArray(90)
        self.view_A = PixelArrayView(self.spectrum, 0, 30)
        self.view_C = PixelArrayView(self.spectrum, 30, 60)

        self.segments_A = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT,
                                  Command.SECTION_ID_A, bytearray([0, 2, 4, 6]), self.view_A)
        self.segments_C = Command(Command.COMMAND_TYPE_SINGLE_SEGMENT,
                                  Command.SECTION_ID_C, bytearray([0, 2, 4, 6]), self.view_C)

        self.colors = [
            Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW,
            Color.CYAN, Color.MAGENTA, Color.WHITE
        ]

    @property
    def name(self) -> str:
        return "Spectrum"

    def update(self, band_levels: Optional[bytes] = None) -> None:
        if band_levels is None or len(band_levels) == 0:
            return
        num_bands = len(band_levels)
        leds_per_band = self.spectrum.length // num_bands
        for i, level in enumerate(band_levels):
            pixel = self.colors[i % len(self.colors)].set_intensity(level)
            # Calculate LED start index for this band
            start = i * leds_per_band
            end = start + leds_per_band
            # Set the pixels for this band
            self.spectrum.set_pixels(start, end, pixel)

    def get_commands(self) -> list[Command]:
        return [self.segments_A, self.segments_C]


spectrumEffect = SpectrumEffect()
