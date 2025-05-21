from .protocol import Command, Mumush, Color

class SpectrumEffect(Mumush):
    def __init__(self):
        super().__init__()
        self.two_segments_A = Command(self.COMMAND_TYPE_SINGLE_SEGMENT, self.SECTION_ID_A, bytearray([0, 2, 4, 6]), self.segment_A)
        self.two_segments_C = Command(self.COMMAND_TYPE_SINGLE_SEGMENT, self.SECTION_ID_C, bytearray([0, 2, 4, 6]), self.segment_C)
        self.colors = [
            Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW,
            Color.CYAN, Color.MAGENTA, Color.WHITE, Color.BLACK
        ]

    def calculate(self, band_levels:bytes) -> None:
        total_leds = self.segment_A.length + self.segment_C.length
        num_bands = len(band_levels)
        leds_per_band = total_leds // num_bands
        for i, level in enumerate(band_levels):
            pixel = self.colors[i % len(self.colors)].set_intensity(level)
             # Calculate LED start index for this band
            start = i * leds_per_band
            end = start + leds_per_band
            # Set the pixels for this band
            if start < self.segment_A.length:
                # Set pixels in segment A
                if end > self.segment_A.length:
                    overflow = end - self.segment_A.length
                    end = self.segment_A.length
                    self.segment_A.set_pixels(start, end, pixel)
                    self.segment_C.set_pixels(0, overflow, pixel)
                else:
                    self.segment_A.set_pixels(start, end, pixel)
            else:
                # Set pixels in segment C
                start -= self.segment_A.length
                end -= self.segment_A.length
                self.segment_C.set_pixels(start, end, pixel)

spectrumEffect = SpectrumEffect()
        
        



