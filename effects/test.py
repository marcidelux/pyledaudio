from .protocol import Command, Color, section_A, section_B, section_C, cmd_section_A, cmd_section_B, cmd_section_C
from .effect import Effect
from typing import Optional
import time

class Test(Effect):
    def __init__(self):
        self.colors = [
            Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW,
            Color.CYAN, Color.MAGENTA, Color.WHITE, Color.BLACK
        ]
        self.step_A = 0
        self.step_B = 0
        self.step_C = 0
        self.previous_time = time.time()
        self.update_speed = 0.05 #seconds

    def demo_full_section_A(self) -> None:
        section_A.set_all(Color.BLACK)
        idx = self.step_A % section_A.length
        section_A.set_pixel(idx, Color.RED)
        self.step_A += 1

    def demo_full_section_B(self) -> None:
        section_B.set_all(Color.BLACK)
        idx = self.step_B % section_B.length
        section_B.set_pixel(idx, Color.GREEN)
        self.step_B += 1
    
    def demo_full_section_C(self) -> None:
        section_C.set_all(Color.BLACK)
        idx = self.step_C % section_C.length
        section_C.set_pixel(idx, Color.BLUE)
        self.step_C += 1

    def update(self, band_levels: Optional[bytes] = None) -> None:
        current_time = time.time()
        if current_time - self.previous_time < self.update_speed:
            return
        self.demo_full_section_A()
        self.demo_full_section_B()
        self.demo_full_section_C()
    
    def get_commands(self) -> list[Command]:
        return [
            cmd_section_A,
            cmd_section_B,
            cmd_section_C
        ]

testEffects = Test()