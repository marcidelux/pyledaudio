from dataclasses import dataclass
from numpy import uint8

@dataclass
class Pixel:
    r: uint8
    g: uint8
    b: uint8
    
    def set_intensity(self, intensity: uint8) -> 'Pixel':
        max_val = max(self.r, self.g, self.b)
        if max_val == 0:
            return Color.BLACK
        factor = intensity / max_val
        return Pixel(
            uint8(self.r * factor),
            uint8(self.g * factor),
            uint8(self.b * factor)
        )

    def to_bytes_GRB(self):
        # Convert the RGB values to bytes We h
        return bytes([self.g, self.r, self.b])

class PixelArray:
    def __init__(self, length):
        self.length = length  # Length of the array
        self.array = bytearray(length * 3)  # RGB values (3 bytes per pixel)

    def set_pixel(self, index:int, pixel: Pixel):
        start_idx = index * 3
        self.array[start_idx:start_idx + 3] = pixel.to_bytes_GRB()
    
    def set_pixels(self, start, end, pixel: Pixel):
        for i in range(start, end):
            self.set_pixel(i, pixel)

    def set_all(self, pixel: Pixel):
        for i in range(self.length):
            self.set_pixel(i, pixel)

    def get_pixel(self, index):
        start_idx = index * 3
        return Pixel(self.array[start_idx+1], self.array[start_idx], self.array[start_idx + 2])

    def to_bytes(self):
        return self.array
    
    def __repr__(self):
        return f"RgbArray(length={self.length}, array={self.array})"

class Command:
    def __init__(self, type:uint8, section_id:uint8, segment_ids:bytearray, pixels: PixelArray):
        self.type = type
        self.section_id = section_id
        self.segment_ids = segment_ids  # array of uint8_t
        self.pixels = pixels  # array of bytes

        self.header_size = 4 # 1 byte for type, 1 byte for section_id, 2 bytes for payload_len
        self.segment_ids_len = len(segment_ids)  # number of segments
        self.pixels_byte_len = pixels.length * 3  # 3 bytes per pixel (GRB)
        self.payload_len = self.segment_ids_len +  self.pixels_byte_len # uint16_t

        # Preallocate full payload
        self.payload = bytearray(self.header_size + self.payload_len)

        self._write_header()
        self._write_segment_ids()
        self._write_pixels()

    def _write_header(self):
        self.payload[0] = self.type
        self.payload[1] = self.section_id
        self.payload[2:4] = self.payload_len.to_bytes(2, 'big')
    
    def _write_segment_ids(self):
        self.payload[4:4 + self.segment_ids_len] = self.segment_ids

    def _write_pixels(self):
        start_idx = 4 + self.segment_ids_len
        self.payload[start_idx:start_idx + self.pixels_byte_len] = self.pixels.to_bytes()

    def set_segment_ids(self, segment_ids: bytearray):
            self.segment_ids = segment_ids
            self.segment_ids_len = len(segment_ids)
            self.payload_len = self.segment_ids_len + self.pixels_byte_len
            self.payload = bytearray(self.header_size + self.payload_len)
            self._write_header()
            self._write_segment_ids()
            self._write_pixels()

    def to_bytes(self) -> bytes:
        self._write_header()
        self._write_segment_ids()
        self._write_pixels()
        return bytes(self.payload) 
    
    def __repr__(self):
        return f"Command(type={self.type}, section_id={self.section_id}, segment_ids={self.segment_ids}, pixels={self.pixels})"

class Mumush:
    COMMAND_TYPE_OFF = 0x00  # Command type for turning off the device
    COMMAND_TYPE_FULL_SECTION = 0x01  # Command type for section control
    COMMAND_TYPE_SINGLE_SEGMENT = 0x02  # Command type for single segment control

    SECTION_ID_A = 0x00  # Section ID for section A
    SECTION_ID_B = 0x01  # Section ID for section B
    SECTION_ID_C = 0x02  # Section ID for section C

    def __init__(self):
        self.segment_A = PixelArray(30)
        self.segment_B = PixelArray(22)
        self.segment_C = PixelArray(60)
        
        self.section_A = PixelArray(240)
        self.section_B = PixelArray(176)
        self.section_C = PixelArray(480)

        self.turn_off = Command(self.COMMAND_TYPE_OFF, 0x00, bytearray(), PixelArray(0))
        
        self.command_full_section_A = Command(self.COMMAND_TYPE_FULL_SECTION, self.SECTION_ID_A, bytearray(), self.section_A)
        self.command_full_section_B = Command(self.COMMAND_TYPE_FULL_SECTION, self.SECTION_ID_B, bytearray(), self.section_B)
        self.command_full_section_C = Command(self.COMMAND_TYPE_FULL_SECTION, self.SECTION_ID_C, bytearray(), self.section_C)

class Color:
    BLACK   = Pixel(0, 0, 0)
    WHITE   = Pixel(255, 255, 255)
    RED     = Pixel(255, 0, 0)
    GREEN   = Pixel(0, 255, 0)
    BLUE    = Pixel(0, 0, 255)
    YELLOW  = Pixel(255, 255, 0)
    CYAN    = Pixel(0, 255, 255)
    MAGENTA = Pixel(255, 0, 255)
    ORANGE  = Pixel(255, 128, 0)
    PURPLE  = Pixel(128, 0, 255)
    PINK    = Pixel(255, 0, 128)
    LIME    = Pixel(128, 255, 0)
    SKY     = Pixel(0, 128, 255)
    VIOLET  = Pixel(128, 0, 128)
    TEAL    = Pixel(0, 255, 128)

    PALETTE = [
        RED, GREEN, BLUE, YELLOW,
        CYAN, MAGENTA, ORANGE, PURPLE,
        PINK, LIME, SKY, VIOLET,
        TEAL, WHITE, BLACK
    ]
