from dataclasses import dataclass
from typing import List, Iterable, Optional
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, fields
from typing import List, Any, Optional, Dict, Literal, Tuple
from numpy import uint8
from time import time


@dataclass
class Pixel:
    r: uint8
    g: uint8
    b: uint8

    def __add__(self, other: 'Pixel') -> 'Pixel':
        avg_r = uint8((int(self.r) + int(other.r)) // 2)
        avg_g = uint8((int(self.g) + int(other.g)) // 2)
        avg_b = uint8((int(self.b) + int(other.b)) // 2)
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

    def __bytes__(self) -> bytes:
        return bytes([self.g, self.r, self.b])

    def __repr__(self):
        return f"(r:{self.r}, g:{self.g}, b:{self.b})"


class PixelArray:
    def __init__(self,
                 length: int,
                 pixels: Optional[Iterable[Pixel]] = None,
                 default: Pixel = Pixel(0, 0, 0)):
        if pixels is not None:
            px_list = list(pixels)
            if len(px_list) != length:
                raise ValueError(
                    f"Expected {length} pixels, got {len(px_list)}")
            self._pixels = px_list
        else:
            self._pixels = [default for _ in range(length)]
        self._length = length

    def __getitem__(self, index: int) -> Pixel:
        return self._pixels[index]

    def __setitem__(self, index: int | slice, value: Pixel):
        if isinstance(index, int):
            self._pixels[index] = value
        elif isinstance(index, slice):
            for i in range(*index.indices(len(self))):
                self._pixels[i] = value

    def __len__(self) -> int:
        return self._length

    def __iter__(self):
        return iter(self._pixels)

    def __bytes__(self) -> bytes:
        return b''.join(bytes(p) for p in self._pixels)

    def __add__(self, other: 'PixelArray') -> 'PixelArray':
        if len(self) != len(other):
            raise ValueError("PixelArrays must be the same length to add")

        combined_pixels = [self[i] + other[i] for i in range(len(self))]
        return PixelArray(len(self), pixels=combined_pixels)

    def __iadd__(self, other: 'PixelArray') -> 'PixelArray':
        if len(self) != len(other):
            raise ValueError("PixelArrays must be the same length to add")

        for i in range(len(self)):
            self[i] += other[i]
        return self

    def set_intensity(self, intensity: uint8):
        for i in range(len(self)):
            self[i] = self[i].set_intensity(intensity)

    def set_all(self, pixel: Pixel):
        for i in range(len(self)):
            self[i] = pixel

    def __repr__(self):
        lines = [f"{i}: {p!r}" for i, p in enumerate(self._pixels)]
        return "PixelArray[\n  " + "\n  ".join(lines) + "\n]"


class PixelArrayView:
    def __init__(self,
                 parent: PixelArray,
                 start: int,
                 length: int,
                 flip: bool = False):
        self._parent = parent
        self._start = start
        self._length = length
        self._flip = flip

    def __getitem__(self, idx: int) -> Pixel:
        actual_idx = self._resolve_index(idx)
        return self._parent[actual_idx]

    def __setitem__(self, index: int | slice, value: Pixel):
        if isinstance(index, int):
            actual_idx = self._resolve_index(index)
            self._parent[actual_idx] = value
        elif isinstance(index, slice):
            indices = range(*index.indices(self._length))
            for i in indices:
                actual_idx = self._resolve_index(i)
                self._parent[actual_idx] = value
        else:
            raise TypeError("Index must be int or slice")

    def _resolve_index(self, idx: int) -> int:
        if idx < 0 or idx >= self._length:
            raise IndexError("PixelArrayView index out of range")
        return self._start + (self._length - 1 - idx if self._flip else idx)

    def __len__(self) -> int:
        return self._length

    def __iter__(self):
        for i in range(self._length):
            yield self[i]

    def __bytes__(self) -> bytes:
        return b''.join(bytes(self[i]) for i in range(self._length))

    def __add__(self, other: 'PixelArrayView') -> PixelArray:
        if len(self) != len(other):
            raise ValueError("PixelArrayViews must be the same length to add")
        return PixelArray(len(self), pixels=[self[i] + other[i] for i in range(len(self))])

    def __iadd__(self, other: 'PixelArrayView') -> 'PixelArrayView':
        if len(self) != len(other):
            raise ValueError("PixelArrayViews must be the same length to add")
        for i in range(len(self)):
            self[i] += other[i]
        return self

    def set_intensity(self, intensity: uint8):
        for i in range(len(self)):
            self[i] = self[i].set_intensity(intensity)

    def __repr__(self):
        lines = [f"{i}: {self[i]!r}" for i in range(self._length)]
        return "PixelArrayView[\n  " + "\n  ".join(lines) + "\n]"


class PixelGroup:
    def __init__(self, *views: tuple[PixelArrayView, bool]):
        self.views: List[PixelArrayView] = []
        for view, flip in views:
            self.views.append(PixelArrayView(
                view._parent,
                view._start,
                view._length,
                flip
            ))

    def __len__(self):
        return sum(len(v) for v in self.views)

    def __getitem__(self, index: int) -> PixelArrayView:
        for view in self.views:
            if index < len(view):
                return view[index]
            index -= len(view)
        raise IndexError("PixelGroup index out of range")

    def __setitem__(self, index: int, value: Pixel):
        for view in self.views:
            if index < len(view):
                view[index] = value
                return
            index -= len(view)
        raise IndexError("PixelGroup index out of range")

    def __bytes__(self) -> bytes:
        return b''.join(bytes(view) for view in self.views)

    def view(self, index: int) -> PixelArrayView:
        if index < 0 or index >= len(self.views):
            raise IndexError("PixelGroup view index out of range")
        return self.views[index]

    def set_all(self, pixel: Pixel):
        for view in self.views:
            view[:] = pixel

    def set_intensity(self, intensity: uint8):
        for view in self.views:
            view.set_intensity(intensity)

    def __repr__(self):
        return "PixelGroup[\n" + "\n".join(repr(v) for v in self.views) + "\n]"


class Particle:
    def __init__(self,
                 color: Pixel,
                 position: int,
                 direction: int,
                 speed: int,  # how fast the particle moves 1-30
                 lifetime: float,
                 update_speed: float,
                 time_of_creation: float = time()):
        self.color = color
        self.position = position
        self.direction = direction
        self.lifetime = lifetime
        self.update_speed = update_speed
        self._last_update = time_of_creation
        self.speed = speed
        self.step = direction * speed

    def update(self, current_time: float = time()):
        time_passed = current_time - self._last_update
        self.lifetime -= time_passed

        if time_passed >= self.update_speed:
            self.position += self.step

        self._last_update = current_time

    def is_alive(self) -> bool:
        return self.lifetime > 0

    def set_direction(self, direction: int):
        if direction not in (-1, 1):
            raise ValueError("Direction must be -1 or 1")
        self.direction = direction
        self.step = direction * self.speed

    def clone(self, position, direction) -> 'Particle':
        return Particle(
            color=self.color,
            position=position,
            direction=direction,
            lifetime=self.lifetime,
            update_speed=self.update_speed,
            time_of_creation=self._last_update,
            speed=self.speed
        )


class ParticleLine:
    def __init__(self, view: PixelArrayView):
        self.view = view
        self.particles: list[Particle] = []
        self._connections_head: List[Tuple['ParticleLine',
                                           Literal["head", "tail"]]] = []
        self._connections_tail: List[Tuple['ParticleLine',
                                           Literal["head", "tail"]]] = []

    def add_connection_to_head(self, other: Tuple['ParticleLine', Literal["head", "tail"]]):
        if other not in self._connections_head:
            self._connections_head.append(other)

    def add_connections_to_head(self, others: Iterable[Tuple['ParticleLine', Literal["head", "tail"]]]):
        for other in others:
            self.add_connection_to_head(other)

    def add_connection_to_tail(self, other: Tuple['ParticleLine', Literal["head", "tail"]]):
        if other not in self._connections_tail:
            self._connections_tail.append(other)

    def add_connections_to_tail(self, others: Iterable[Tuple['ParticleLine', Literal["head", "tail"]]]):
        for other in others:
            self.add_connection_to_tail(other)

    def remove_connection_to_head(self, other: Tuple['ParticleLine', Literal["head", "tail"]]):
        if other in self._connections_head:
            self._connections_head.remove(other)

    def remove_connection_to_tail(self, other: Tuple['ParticleLine', Literal["head", "tail"]]):
        if other in self._connections_tail:
            self._connections_tail.remove(other)

    def add_connection(self, from_end: Literal["head", "tail"], target: Tuple['ParticleLine', Literal["head", "tail"]]):
        connections = self._connections_head if from_end == "head" else self._connections_tail
        if target not in connections:
            connections.append(target)

    def update(self, current_time: float = time()):
        self.view[:] = Colors.BLACK
        remaining_particles: list[Particle] = []

        for p in self.particles:
            p.update(current_time)

            if not p.is_alive():
                continue

            if p.position < 0:
                # Particle exited through head
                for target_line, target_end in self._connections_head:
                    if target_end == "head":
                        new_p = p.clone(position=0, direction=1)
                    else:
                        new_p = p.clone(position=len(
                            target_line.view) - 1, direction=-1)
                    target_line.particles.append(new_p)
                continue  # Don't keep the original particle

            elif p.position >= len(self.view):
                # Particle exited through tail
                for target_line, target_end in self._connections_tail:
                    if target_end == "head":
                        new_p = p.clone(position=0, direction=1)
                    else:
                        new_p = p.clone(position=len(
                            target_line.view) - 1, direction=-1)
                    target_line.particles.append(new_p)
                continue  # Don't keep the original particle

            # Within bounds — render it
            if self.view[p.position] != Colors.BLACK:
                self.view[p.position] += p.color  # Blend
            else:
                self.view[p.position] = p.color

            remaining_particles.append(p)

        self.particles = remaining_particles

    def add_particle(self, particle: Particle):
        self.particles.append(particle)


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
        self.pixels = pixels  # PixelArray or PixelArrayView

        self.header_size = 4  # 1 byte for type, 1 byte for section_id, 2 bytes for payload_len
        self.segment_ids_len = len(segment_ids)  # number of segments
        self.pixels_byte_len = len(pixels) * 3  # 3 bytes per pixel (GRB)
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
                     self.pixels_byte_len] = bytes(self.pixels)

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

    def shared_segment_ids(self, other: 'Command') -> bytearray:
        if self.type != other.type or self.section_id != other.section_id:
            return bytearray()

        ids_a = set(self.segment_ids)
        ids_b = set(other.segment_ids)
        shared_ids = ids_a & ids_b
        return bytearray(shared_ids)

    def __add__(self, other: 'Command') -> List['Command']:
        if self.type == Command.COMMAND_TYPE_OFF or \
           self.type != other.type or \
           self.section_id != other.section_id:
            # print("Cannot combine commands with different types or section IDs.")
            return []

        if self.type == Command.COMMAND_TYPE_FULL_SECTION:
            # print("Combining full section commands.")
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
                # print("Combining commands with the same segment IDs:", ids_a)
                return [Command(
                    self.type,
                    self.section_id,
                    self.segment_ids,
                    self.pixels + other.pixels
                )]

            # If there are no shared segment IDs, return both commands separately
            if not shared:
                # print("No shared segment IDs, returning both commands separately.")
                return [self, other]

            if only_a:
                # print("Adding command with only A segment IDs:", only_a)
                result.append(Command(
                    self.type,
                    self.section_id,
                    bytearray(only_a),
                    self.pixels
                ))

            if only_b:
                # print("Adding command with only B segment IDs:", only_b)
                result.append(Command(
                    self.type,
                    self.section_id,
                    bytearray(only_b),
                    other.pixels
                ))

            # print("Adding command with shared segment IDs:", shared)
            shared_ids = list(shared)
            result.append(Command(
                self.type,
                self.section_id,
                bytearray(shared_ids),
                self.pixels + other.pixels
            ))

            return result

    def __repr__(self):
        return f"Command(type={self.type}, section_id={self.section_id}, segment_ids={self.segment_ids}, pixels={self.pixels})"

# A1 (1,2), A2 (3,4)
# B1 (2,7), B2 (3,4,5)
# C1: A1-1, C2: B1-7, C3: B2-5, C4 (A1:2 + B1:2), C5: (A2:3 + B2:3, A2:4 + B2:4)


def merge_command_lists(a: list[Command], b: list[Command]) -> list[Command]:
    merged_pairs: list[tuple[Command, Command]] = []
    unique_a: list[Command] = []
    unique_b = b.copy()

    a_copy = a.copy()

    for cmd_a in a_copy:
        found_pair = False
        for cmd_b in unique_b:
            if cmd_a.type == cmd_b.type and cmd_a.section_id == cmd_b.section_id:
                if set(cmd_a.segment_ids) & set(cmd_b.segment_ids):
                    merged_pairs.append((cmd_a, cmd_b))
                    unique_b.remove(cmd_b)
                    found_pair = True
                    break
        if not found_pair:
            unique_a.append(cmd_a)

    # Merge the found pairs using your Command.__add__()
    merged_cmds: list[Command] = []
    for a_cmd, b_cmd in merged_pairs:
        merged_cmds.extend(a_cmd + b_cmd)

    return merged_cmds + unique_a + unique_b


# Digital Pyramid
class DigitalPyramid:
    def __init__(self):
        self.section_A = PixelArray(Command.SECTION_LEN_A)
        self.section_B = PixelArray(Command.SECTION_LEN_B)
        self.section_C = PixelArray(Command.SECTION_LEN_C)

        self.segments_A: List[PixelArrayView] = []
        self.lines_A: List[ParticleLine] = []
        for i in range(8):
            self.segments_A.append(PixelArrayView(
                self.section_A, i * Command.SEGMENT_LEN_A, Command.SEGMENT_LEN_A))
            self.lines_A.append(ParticleLine(self.segments_A[i]))

        self.segments_B: List[PixelArrayView] = []
        self.lines_B: List[ParticleLine] = []
        for i in range(8):
            self.segments_B.append(PixelArrayView(
                self.section_B, i * Command.SEGMENT_LEN_B, Command.SEGMENT_LEN_B))
            self.lines_B.append(ParticleLine(self.segments_B[i]))

        self.segments_C: List[PixelArrayView] = []
        self.lines_C: List[ParticleLine] = []
        for i in range(8):
            self.segments_C.append(PixelArrayView(
                self.section_C, i * Command.SEGMENT_LEN_C, Command.SEGMENT_LEN_C))
            self.lines_C.append(ParticleLine(self.segments_C[i]))

        # create groups as shapes
        # small triangle at bottom
        self.triangle_bottom_groups = [
            PixelGroup(
                (self.segments_A[0], False),
                (self.segments_B[0], False),
                (self.segments_A[1], True),
            ),
            PixelGroup(
                (self.segments_A[1], False),
                (self.segments_B[1], False),
                (self.segments_A[2], True),
            ),
            PixelGroup(
                (self.segments_A[2], False),
                (self.segments_B[2], False),
                (self.segments_A[3], True),
            ),
            PixelGroup(
                (self.segments_A[3], False),
                (self.segments_B[3], False),
                (self.segments_A[4], True),
            ),
            PixelGroup(
                (self.segments_A[4], False),
                (self.segments_B[4], False),
                (self.segments_A[5], True),
            ),
            PixelGroup(
                (self.segments_A[5], False),
                (self.segments_B[5], False),
                (self.segments_A[6], True),
            ),
            PixelGroup(
                (self.segments_A[6], False),
                (self.segments_B[6], False),
                (self.segments_A[7], True),
            ),
            PixelGroup(
                (self.segments_A[7], False),
                (self.segments_B[7], False),
                (self.segments_A[0], True),
            ),
        ]

        self.triangle_side_groups = [
            PixelGroup(
                (self.segments_B[0], False),
                (self.segments_C[1], False),
                (self.segments_C[0], True),
            ),
            PixelGroup(
                (self.segments_B[1], False),
                (self.segments_C[2], False),
                (self.segments_C[1], True),
            ),
            PixelGroup(
                (self.segments_B[2], False),
                (self.segments_C[3], False),
                (self.segments_C[2], True),
            ),
            PixelGroup(
                (self.segments_B[3], False),
                (self.segments_C[4], False),
                (self.segments_C[3], True),
            ),
            PixelGroup(
                (self.segments_B[4], False),
                (self.segments_C[5], False),
                (self.segments_C[4], True),
            ),
            PixelGroup(
                (self.segments_B[5], False),
                (self.segments_C[6], False),
                (self.segments_C[5], True),
            ),
            PixelGroup(
                (self.segments_B[6], False),
                (self.segments_C[7], False),
                (self.segments_C[6], True),
            ),
            PixelGroup(
                (self.segments_B[7], False),
                (self.segments_C[0], False),
                (self.segments_C[7], True),
            ),
        ]

        self.triangle_body_groups = [
            PixelGroup(
                (self.segments_A[0], False),
                (self.segments_C[0], False),
                (self.segments_C[4], True),
                (self.segments_A[4], True),
            ),
            PixelGroup(
                (self.segments_A[1], False),
                (self.segments_C[1], False),
                (self.segments_C[5], True),
                (self.segments_A[5], True),
            ),
            PixelGroup(
                (self.segments_A[2], False),
                (self.segments_C[2], False),
                (self.segments_C[6], True),
                (self.segments_A[6], True),
            ),
            PixelGroup(
                (self.segments_A[3], False),
                (self.segments_C[3], False),
                (self.segments_C[7], True),
                (self.segments_A[7], True),
            ),
            PixelGroup(
                (self.segments_A[4], False),
                (self.segments_C[4], False),
                (self.segments_C[0], True),
                (self.segments_A[0], True),
            ),
            PixelGroup(
                (self.segments_A[5], False),
                (self.segments_C[5], False),
                (self.segments_C[1], True),
                (self.segments_A[1], True),
            ),
            PixelGroup(
                (self.segments_A[6], False),
                (self.segments_C[6], False),
                (self.segments_C[2], True),
                (self.segments_A[2], True),
            ),
            PixelGroup(
                (self.segments_A[7], False),
                (self.segments_C[7], False),
                (self.segments_C[3], True),
                (self.segments_A[3], True),
            ),
        ]

        self.body_tetrahedron_groups: List[PixelGroup] = [
            PixelGroup(
                (self.segments_A[0], False),
                (self.segments_C[0], False),
                (self.segments_C[1], True),
                (self.segments_B[0], True),
                (self.segments_A[1], True),
            ),
            PixelGroup(
                (self.segments_A[1], False),
                (self.segments_C[1], False),
                (self.segments_C[2], True),
                (self.segments_B[1], True),
                (self.segments_A[2], True),
            ),
            PixelGroup(
                (self.segments_A[2], False),
                (self.segments_C[2], False),
                (self.segments_C[3], True),
                (self.segments_B[2], True),
                (self.segments_A[3], True),
            ),
            PixelGroup(
                (self.segments_A[3], False),
                (self.segments_C[3], False),
                (self.segments_C[4], True),
                (self.segments_B[3], True),
                (self.segments_A[4], True),
            ),
            PixelGroup(
                (self.segments_A[4], False),
                (self.segments_C[4], False),
                (self.segments_C[5], True),
                (self.segments_B[4], True),
                (self.segments_A[5], True),
            ),
            PixelGroup(
                (self.segments_A[5], False),
                (self.segments_C[5], False),
                (self.segments_C[6], True),
                (self.segments_B[5], True),
                (self.segments_A[6], True),
            ),
            PixelGroup(
                (self.segments_A[6], False),
                (self.segments_C[6], False),
                (self.segments_C[7], True),
                (self.segments_B[6], True),
                (self.segments_A[7], True),
            ),
            PixelGroup(
                (self.segments_A[7], False),
                (self.segments_C[7], False),
                (self.segments_C[0], True),
                (self.segments_B[7], True),
                (self.segments_A[0], True),
            ),
        ]

        self.lines_A[0].add_connections_to_tail([
            (self.lines_B[0], "head"),
            (self.lines_B[7], "tail"),
            (self.lines_C[0], "hea1d")
        ])

        self.lines_B[0].add_connections_to_tail([
            (self.lines_A[1], "tail"),
            (self.lines_B[1], "head"),
            (self.lines_C[1], "head")
        ])
        self.lines_B[7].add_connections_to_head([
            (self.lines_A[7], "tail"),
            (self.lines_B[6], "tail"),
            (self.lines_C[7], "head")
        ])

        self.cmd_A = Command(Command.COMMAND_TYPE_FULL_SECTION,
                             Command.SECTION_ID_A, bytearray(), self.section_A)
        self.cmd_B = Command(Command.COMMAND_TYPE_FULL_SECTION,
                             Command.SECTION_ID_B, bytearray(), self.section_B)
        self.cmd_C = Command(Command.COMMAND_TYPE_FULL_SECTION,
                             Command.SECTION_ID_C, bytearray(), self.section_C)

    def update(self, update_time: float = time()):
        for line in self.lines_A:
            line.update(update_time)
        for line in self.lines_B:
            line.update(update_time)
        for line in self.lines_C:
            line.update(update_time)


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
