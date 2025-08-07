import time
from dataclasses import dataclass
from ..utils import (
    PyramidSimpleCommands,
    Effect,
    Pixel,
    Colors
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


class SideTriangles(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="SideTriangles",
            update_speed=0.2,
            colors=[Pixel(255, 0, 0), Pixel(0, 255, 0), Pixel(0, 0, 255)]
        )
        self.previous_time = time.time()
        self.current_index = 0
        self.intensity = 0

    def update(self) -> None:
        if time.time() - self.previous_time < self.config.update_speed:
            return None

        self.pyramid.section_B.set_all(Colors.BLACK)
        self.pyramid.section_C.set_all(Colors.BLACK)

        intensities = [80, 160, 255]
        num_groups = len(self.pyramid.triangle_side_groups)

        for offset, intensity in enumerate(intensities):
            idx = (self.current_index + offset) % num_groups
            group = self.pyramid.triangle_side_groups[idx]
            for i, color in enumerate(self.config.colors[:3]):
                group.view(i)[:] = color.set_intensity(intensity)

        self.current_index = (self.current_index + 1) % num_groups
        self.previous_time = time.time()

    def get_commands(self) -> PyramidSimpleCommands:
        return self.pyramid.cmds
