import time
import colorsys
from dataclasses import dataclass
from typing import Optional, List
from ..utils import (
    Command,
    Effect,
    Pixel,
    DigitalPyramid,
    AudioInfo
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


class VuTwoLinesTop(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = True  # Dynamic effect
        self.config = EffectConfig(
            name="VuTwoLinesTop",
            update_speed=0.05,
            colors=[
                Pixel(10, 10, 10),
                Pixel(120, 120, 120)
            ]
        )
        self.line_len = len(self.pyramid.two_lines_body_groups[0]) - 1
        self.previous_time = time.time()
        self.hue = 0.0  # start of the rainbow

    def update(self, audio_info: Optional[AudioInfo] = None) -> None:
        if audio_info is None:
            return None

        current_time = time.time()
        if current_time - self.previous_time < self.config.update_speed:
            self.hue += 0.005
            if self.hue > 1.0:
                self.hue -= 1.0

            num_colors = len(self.config.colors)
            hue_step = 1.0 / num_colors

            for i in range(num_colors):
                shifted_hue = (self.hue + i * hue_step) % 1.0
                r, g, b = colorsys.hsv_to_rgb(shifted_hue, 1.0, 1.0)
                self.config.colors[i] = Pixel(
                    int(r * 255), int(g * 255), int(b * 255))

        self.pyramid.clear()

        for i in range(8):
            normalized = audio_info.bands[i] / 255
            active_len = int(normalized * self.line_len)
            self.pyramid.two_lines_body_groups[i][self.line_len -
                                                  active_len:] = self.config.colors[i % 2]

        self.previous_time = current_time

    def get_commands(self) -> List[Command]:
        return self.pyramid.cmds
