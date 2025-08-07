import time
from dataclasses import dataclass
import random
import colorsys
from ..utils import (
    PyramidSimpleCommands,
    Effect,
    colors,
    Pixel,
    Particle,
    GateMode
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


def shift_pixel_hue(pixel: Pixel, hue_shift: float) -> Pixel:
    # Convert RGB to HSV
    r_norm = pixel.r / 255.0
    g_norm = pixel.g / 255.0
    b_norm = pixel.b / 255.0

    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)

    # Shift hue
    h = (h + hue_shift) % 1.0

    # Convert back to RGB
    r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)

    return Pixel(int(r_new * 255), int(g_new * 255), int(b_new * 255))


class BigSnake(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="BigSnake",
            update_speed=0.03,
            colors=[
                colors.RED, colors.GREEN,
                colors.BLUE, colors.YELLOW,
                colors.CYAN, colors.MAGENTA,
                colors.WHITE, colors.ORANGE
            ]
        )
        self.previous_time = time.time()
        self.previous_spawn_time = self.previous_time
        self.spawn_time = 2

        self.pyramid.lines_A.set_gates_mode(GateMode.ARROW)
        self.pyramid.lines_B.set_gates_mode(GateMode.ARROW)
        self.pyramid.lines_C.set_gates_mode(GateMode.ARROW)

        self.pyramid.connect_all_particle_lines()

        self.hue_delta = 0.01  # start of the rainbow

    def update(self) -> None:
        current_time = time.time()

        if current_time - self.previous_time < self.config.update_speed:
            return None

        if current_time >= self.previous_spawn_time + self.spawn_time:
            self.previous_spawn_time = current_time
            random_A_index = random.randint(0, 7)
            length = 14
            random_color = random.choice(self.config.colors)
            for i in range(length):
                particle = Particle(
                    color=random_color.set_intensity(int(i * (255 / length))),
                    position=i,
                    direction=1,
                    lifetime=20,
                    update_speed=0.03,
                    speed=1,
                    fade_time=1,
                    time_of_creation=current_time,
                    hue_delta=self.hue_delta
                )
                self.pyramid.lines_A[random_A_index].add_particle(particle)

        self.pyramid.update(current_time)
        self.previous_time = current_time

    def get_commands(self) -> PyramidSimpleCommands:
        return self.pyramid.cmds
