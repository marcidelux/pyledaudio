import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, fields
from typing import List, Any, Optional
from numpy import uint8


@dataclass
class Pixel:
    r: uint8
    g: uint8
    b: uint8

    def __add__(self, other: 'Pixel') -> 'Pixel':
        avg_r = (self.r + other.r) // 2
        avg_g = (self.g + other.g) // 2
        avg_b = (self.b + other.b) // 2
        max_intensity = max(self.r, self.g, self.b, other.r, other.g, other.b)
        return Pixel(avg_r, avg_g, avg_b).set_intensity(max_intensity)

    def __iadd__(self, other: 'Pixel') -> 'Pixel':
        return self + other

    def set_intensity(self, intensity: uint8) -> 'Pixel':
        max_val = max(self.r, self.g, self.b)
        if max_val == 0:
            return colors.BLACK
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

    def __add__(self, other: 'PixelArray') -> 'PixelArray':
        if self.length != other.length:
            raise ValueError("PixelArrays must be the same length to add.")

        result = PixelArray(self.length)
        for i in range(self.length):
            pixelA = self.get_pixel(i)
            pixelB = other.get_pixel(i)
            result.set_pixel(i, pixelA + pixelB)
        return result

    def __iadd__(self, other: 'PixelArray') -> 'PixelArray':
        return self + other

    def set_pixel(self, index: int, pixel: Pixel):
        start_idx = index * 3
        self.array[start_idx:start_idx + 3] = pixel.to_bytes_GRB()

    def set_pixels(self, start, end, pixel: Pixel):
        for i in range(start, end):
            self.set_pixel(i, pixel)

    def set_all(self, pixel: Pixel):
        for i in range(self.length):
            self.set_pixel(i, pixel)

    def __setitem__(self, index: int, pixel: Pixel):
        self.set_pixel(index, pixel)

    def get_pixel(self, index):
        start_idx = index * 3
        return Pixel(self.array[start_idx+1], self.array[start_idx], self.array[start_idx + 2])

    def __getitem__(self, index: int) -> Pixel:
        return self.get_pixel(index)

    def to_bytes(self):
        return self.array

    def __repr__(self):
        return f"RgbArray(length={self.length}, array={self.array})"


class PixelArrayView:
    def __init__(self, parent: PixelArray, start: int, length: int, flip: bool = False):
        self.parent = parent
        self.start = start
        self._length = length  # rename to avoid conflict
        self.flip = flip

    @property
    def length(self):
        return self._length

    def to_bytes(self) -> bytearray:
        start_byte = self.start * 3
        end_byte = start_byte + self.length * 3
        if self.flip:
            flipped_array = bytearray()
            for i in range(self.length):
                pixel_start = start_byte + (self.length - 1 - i) * 3
                flipped_array.extend(
                    self.parent.array[pixel_start:pixel_start + 3])
            return flipped_array
        return self.parent.array[start_byte:end_byte]

    def to_pixel_array(self) -> PixelArray:
        pixel_array = PixelArray(self.length)
        pixel_array.array = self.to_bytes()
        return pixel_array


class Command:
    COMMAND_TYPE_OFF = 0x00  # Command type for turning off the device
    COMMAND_TYPE_FULL_SECTION = 0x01  # Command type for section control
    COMMAND_TYPE_SINGLE_SEGMENT = 0x02  # Command type for single segment control

    SECTION_ID_A = 0x00  # Section ID for section A
    SECTION_ID_B = 0x01  # Section ID for section B
    SECTION_ID_C = 0x02  # Section ID for section C

    # Lengths of segments
    SEGMENT_LEN_A = 30  # Length of segment A - Radials
    SEGMENT_LEN_B = 22  # Length of segment B - Octagon side
    SEGMENT_LEN_C = 60  # Length of segment C - Pyramid Side

    # Lengths of sections 8 times segment length
    SECTION_LEN_A = 240  # Length of section A
    SECTION_LEN_B = 176  # Length of section B
    SECTION_LEN_C = 480  # Length of section C

    def __init__(self, type: uint8, section_id: uint8, segment_ids: bytearray, pixels: PixelArray | PixelArrayView):
        self.type = type
        self.section_id = section_id
        self.segment_ids = segment_ids  # array of uint8_t
        self.pixels = pixels  # array of bytes

        self.header_size = 4  # 1 byte for type, 1 byte for section_id, 2 bytes for payload_len
        self.segment_ids_len = len(segment_ids)  # number of segments
        self.pixels_byte_len = pixels.length * 3  # 3 bytes per pixel (GRB)
        self.segments_pixels_len = self.segment_ids_len + self.pixels_byte_len  # uint16_t

        # Preallocate full payload
        self.payload = bytearray(self.header_size + self.segments_pixels_len)

        self._write_header()
        self._write_segment_ids()
        self._write_pixels()

    def _write_header(self):
        self.payload[0] = self.type
        self.payload[1] = self.section_id
        self.payload[2:4] = self.segments_pixels_len.to_bytes(2, 'big')

    def _write_segment_ids(self):
        self.payload[4:4 + self.segment_ids_len] = self.segment_ids

    def _write_pixels(self):
        start_idx = 4 + self.segment_ids_len
        self.payload[start_idx:start_idx +
                     self.pixels_byte_len] = self.pixels.to_bytes()

    def set_segment_ids(self, segment_ids: bytearray):
        self.segment_ids = segment_ids
        self.segment_ids_len = len(segment_ids)
        self.segments_pixels_len = self.segment_ids_len + self.pixels_byte_len
        self.payload = bytearray(self.header_size + self.segments_pixels_len)
        self._write_header()
        self._write_segment_ids()
        self._write_pixels()

    def to_bytes(self) -> bytes:
        self._write_header()
        self._write_segment_ids()
        self._write_pixels()
        return bytes(self.payload)

    def __add__(self, other: 'Command') -> List['Command']:
        if self.type == Command.COMMAND_TYPE_OFF or \
           self.type != other.type or \
           self.section_id != other.section_id:
            print("Cannot combine commands with different types or section IDs.")
            return []

        if self.type == Command.COMMAND_TYPE_FULL_SECTION:
            print("Combining full section commands.")
            return [Command(
                self.type,
                self.section_id,
                self.segment_ids,
                self.pixels + other.pixels
            )]

        elif self.type == Command.COMMAND_TYPE_SINGLE_SEGMENT:
            ids_a = set(self.segment_ids)
            ids_b = set(other.segment_ids)
            shared = ids_a & ids_b
            only_a = ids_a - ids_b
            only_b = ids_b - ids_a

            result = []

            # If both commands have the same segment IDs, return a single command
            if ids_a == ids_b:
                print("Combining commands with the same segment IDs:", ids_a)
                if isinstance(self.pixels, PixelArrayView):
                    self_pixels = self.pixels.to_pixel_array()
                else:
                    self_pixels = self.pixels

                if isinstance(other.pixels, PixelArrayView):
                    other_pixels = other.pixels.to_pixel_array()
                else:
                    other_pixels = other.pixels

                combined_pixels = self_pixels + other_pixels

                return [Command(
                    self.type,
                    self.section_id,
                    self.segment_ids,
                    combined_pixels
                )]

            # If there are no shared segment IDs, return both commands separately
            if not shared:
                print("No shared segment IDs, returning both commands separately.")
                return [self, other]

            if only_a:
                print("Adding command with only A segment IDs:", only_a)
                result.append(Command(
                    self.type,
                    self.section_id,
                    bytearray(only_a),
                    self.pixels
                ))

            if only_b:
                print("Adding command with only B segment IDs:", only_b)
                result.append(Command(
                    self.type,
                    self.section_id,
                    bytearray(only_b),
                    other.pixels
                ))

            print("Adding command with shared segment IDs:", shared)
            shared_ids = list(shared)
            if isinstance(self.pixels, PixelArrayView):
                self_pixels = self.pixels.to_pixel_array()
            else:
                self_pixels = self.pixels

            if isinstance(other.pixels, PixelArrayView):
                other_pixels = other.pixels.to_pixel_array()
            else:
                other_pixels = other.pixels

            combined_pixels = self_pixels + other_pixels
            result.append(Command(
                self.type,
                self.section_id,
                bytearray(shared_ids),
                combined_pixels
            ))

            return result

    def __repr__(self):
        return f"Command(type={self.type}, section_id={self.section_id}, segment_ids={self.segment_ids}, pixels={self.pixels})"


class Effect(ABC):
    def __init__(self):
        self.config = None  # Must be initialized by the child class
        self.is_dynamic = False  # Indicates if the effect is dynamic or static

    def get_config(self) -> dict[str, Any]:
        config_dict = asdict(self.config)
        if "colors" in config_dict:
            config_dict["colors"] = [
                colors.name_for(c) or {"r": c.r, "g": c.g, "b": c.b}
                for c in config_dict["colors"]
            ]
        return config_dict

    def set_config(self, config_dict: dict[str, Any]) -> None:
        for field in fields(self.config):
            if field.name in config_dict:
                self.set_config_field(field.name, config_dict[field.name])

    def set_config_field(self, key: str, value: Any) -> None:
        if key == "colors" and isinstance(value, list):
            parsed = []
            for v in value:
                if isinstance(v, str) and v in colors.PALETTE:
                    parsed.append(colors.PALETTE[v])
                else:
                    raise ValueError(f"Invalid color value: {v}")
            setattr(self.config, key, parsed)
        elif hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            raise KeyError(f"Config has no field named '{key}'")

    """Calculate the effect based on the provided band levels."""
    @abstractmethod
    def update(self, band_levels: Optional[bytes] = None) -> List[Command]:
        pass


class Colors:
    BLACK = Pixel(0, 0, 0)
    WHITE = Pixel(255, 255, 255)
    RED = Pixel(255, 0, 0)
    GREEN = Pixel(0, 255, 0)
    BLUE = Pixel(0, 0, 255)
    YELLOW = Pixel(255, 255, 0)
    CYAN = Pixel(0, 255, 255)
    MAGENTA = Pixel(255, 0, 255)
    ORANGE = Pixel(255, 128, 0)
    PURPLE = Pixel(128, 0, 255)
    PINK = Pixel(255, 0, 128)
    LIME = Pixel(128, 255, 0)
    SKY = Pixel(0, 128, 255)
    VIOLET = Pixel(128, 0, 128)
    TEAL = Pixel(0, 255, 128)

    PALETTE: dict[str, Pixel] = {
        "BLACK": BLACK,
        "WHITE": WHITE,
        "RED": RED,
        "GREEN": GREEN,
        "BLUE": BLUE,
        "YELLOW": YELLOW,
        "CYAN": CYAN,
        "MAGENTA": MAGENTA,
        "ORANGE": ORANGE,
        "PURPLE": PURPLE,
        "PINK": PINK,
        "LIME": LIME,
        "SKY": SKY,
        "VIOLET": VIOLET,
        "TEAL": TEAL,
    }

    def name_for(cls, pixel: Pixel) -> str | None:
        for name, p in cls.PALETTE.items():
            if p == pixel:
                return name
        return None


class Line:
    def __init__(self, start_index: int):
        self.index = start_index
        self.colors = random.sample(list(colors.PALETTE.values()), 4)

    def set_intensity(self, intensity: int):
        self.colors = [color.set_intensity(intensity) for color in self.colors]

    def advance(self):
        self.index += 1


# SINGLETONS #
colors = Colors()
cmd_turn_off = Command(Command.COMMAND_TYPE_OFF, 0x00,
                       bytearray(), PixelArray(0))
