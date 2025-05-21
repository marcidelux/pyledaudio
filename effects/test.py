from .protocol import Command, Mumush, Color

class Test(Mumush):
    def __init__(self):
        super().__init__()
        self.colors = [
            Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW,
            Color.CYAN, Color.MAGENTA, Color.WHITE, Color.BLACK
        ]
        self.step_A = 0
        self.step_B = 0
        self.step_C = 0
        self.command_segment_A = Command(self.COMMAND_TYPE_SINGLE_SEGMENT, self.SECTION_ID_A, bytearray([0,1,2,3,4,5,6,7]), self.segment_A)

    def demo_full_section_A(self) -> None:
        self.section_A.set_all(Color.BLACK)
        idx = self.step_A % self.section_A.length
        self.section_A.set_pixel(idx, Color.RED)
        self.step_A += 1

    def demo_full_section_B(self) -> None:
        self.section_B.set_all(Color.BLACK)
        idx = self.step_B % self.section_B.length
        self.section_B.set_pixel(idx, Color.GREEN)
        self.step_B += 1
    
    def demo_full_section_C(self) -> None:
        self.section_C.set_all(Color.BLACK)
        idx = self.step_C % self.section_C.length
        self.section_C.set_pixel(idx, Color.BLUE)
        self.step_C += 1

testEffects = Test()