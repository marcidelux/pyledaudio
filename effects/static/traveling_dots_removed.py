import time
from dataclasses import dataclass
from typing import List
from ..utils import (
    Command,
    Effect,
    Pixel,
    PixelArray,
    colors
)


@dataclass
class EffectConfig:
    name: str
    update_speed: float
    colors: list[Pixel] = None


class TravelingDots(Effect):
    def __init__(self):
        super().__init__()
        self.is_dynamic = False  # Static effect
        self.config = EffectConfig(
            name="TravelingDots",
            update_speed=0.05,
        )
        self.section_A = PixelArray(240)
        self.section_B = PixelArray(176)
        self.section_C = PixelArray(480)

        self.cmd_section_A = Command(Command.COMMAND_TYPE_FULL_SECTION,
                                     Command.SECTION_ID_A, bytearray(), self.section_A)
        self.cmd_section_B = Command(Command.COMMAND_TYPE_FULL_SECTION,
                                     Command.SECTION_ID_B, bytearray(), self.section_B)
        self.cmd_section_C = Command(Command.COMMAND_TYPE_FULL_SECTION,
                                     Command.SECTION_ID_C, bytearray(), self.section_C)
        self.step_A = 0
        self.step_B = 0
        self.step_C = 0
        self.previous_time = time.time()

    def demo_full_section_A(self) -> None:
        self.section_A.set_all(colors.BLACK)
        idx = self.step_A % len(self.section_A)
        self.section_A[idx] = colors.RED
        self.step_A += 1

    def demo_full_section_B(self) -> None:
        self.section_B.set_all(colors.BLACK)
        idx = self.step_B % len(self.section_B)
        self.section_B[idx] = colors.GREEN
        self.step_B += 1

    def demo_full_section_C(self) -> None:
        self.section_C.set_all(colors.BLACK)
        idx = self.step_C % len(self.section_C)
        self.section_C[idx] = colors.BLUE
        self.step_C += 1

    def update(self) -> None:
        current_time = time.time()
        if current_time - self.previous_time < self.config.update_speed:
            self.demo_full_section_A()
            self.demo_full_section_B()
            self.demo_full_section_C()

    def get_commands(self) -> List[Command]:
        return [
            self.cmd_section_A,
            self.cmd_section_B,
            self.cmd_section_C
        ]


# Singleton instance of TravelingDots
travelingDots = TravelingDots()
