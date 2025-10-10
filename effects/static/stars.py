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


class Stars(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="Stars",
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
        self.spawn_time = random.uniform(2, 8)

        self.hue_delta = 0.01  # start of the rainbow

    def update(self) -> None:
        current_time = time.time()

        if current_time - self.previous_time < self.config.update_speed:
            return None

        if current_time >= self.previous_spawn_time + self.spawn_time:
            self.spawn_time = random.uniform(2, 8)
            self.previous_spawn_time = current_time

            number_of_stars = random.randint(5, 20)

            for _ in range(number_of_stars):
                random_lifetime = random.randint(5, 15)
                random_A_index = random.randint(0, 7)
                random_B_index = random.randint(0, 7)
                random_C_index = random.randint(0, 7)

                random_color = random.choice(self.config.colors)

                random_line = random.randint(0, 2)
                if random_line == 0:
                    random_position = random.randint(0, 29)
                elif random_line == 1:
                    random_position = random.randint(0, 21)
                else:
                    random_position = random.randint(0, 59)

                star = Particle(
                    color=random_color,
                    position=random_position,
                    direction=1,
                    lifetime=random_lifetime,
                    update_speed=0.03,
                    speed=0,
                    fade_time=4,
                    time_of_creation=current_time,
                    hue_delta=self.hue_delta
                )

                if random_line == 0:
                    self.pyramid.lines_A[random_A_index].add_particle(star)
                elif random_line == 1:
                    self.pyramid.lines_B[random_B_index].add_particle(star)
                else:
                    self.pyramid.lines_C[random_C_index].add_particle(star)

        self.pyramid.update(current_time)
        self.previous_time = current_time

    def get_commands(self) -> PyramidSimpleCommands:
        return self.pyramid.cmds
