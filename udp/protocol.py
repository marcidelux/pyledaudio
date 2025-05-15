COMMAND_TYPE_OFF = 0x00  # Command type for turning off the device
COMMAND_TYPE_FULL_SECTION = 0x01  # Command type for section control
COMMAND_TYPE_SINGLE_SEGMENT = 0x02  # Command type for single segment control

SECTION_ID_A = 0x00  # Section ID for section A
SECTION_ID_B = 0x01  # Section ID for section B
SECTION_ID_C = 0x02  # Section ID for section C

class Color:
    def __init__(self, r, g, b):
        self.r = r  # Red value (0-255)
        self.g = g  # Green value (0-255)
        self.b = b  # Blue value (0-255)

    def to_bytes(self):
        return bytes([self.g, self.r, self.b])

class Command:
    def __init__(self, type, section_id, segment_ids, rgb_colors):
        self.type = type  # uint8_t
        self.section_id = section_id  # uint8_t
        self.payload_len = len(segment_ids) +  len(rgb_colors)# uint16_t
        self.segment_ids = segment_ids  # array of uint8_t
        self.rgb_colors = rgb_colors  # array of bytes
    
    def set_pixel(self, index, color: Color, segment_ids=None):
        if segment_ids is not None:
            self.set_segment_ids(segment_ids)

        start_idx = index * 3
        self.rgb_colors[start_idx:start_idx + 3] = color.to_bytes()
    
    def set_segment_ids(self, segment_ids):
        self.section_id = segment_ids
        self.payload_len = len(self.segment_ids) + len(self.rgb_colors)

    def to_bytes(self):
        # Convert the command to a byte array
        header = self.type.to_bytes(1, 'big') + \
                 self.section_id.to_bytes(1, 'big') + \
                 self.payload_len.to_bytes(2, 'big')
        return header + bytes(self.segment_ids) + bytes(self.rgb_colors)
    
    def __repr__(self):
        return (f"Command(type={self.type}, section_id={self.section_id}, "
                f"payload_len={self.payload_len}, segment_ids={self.segment_ids}, "
                f"rgb_colors={self.rgb_colors})")

    def __str__(self):
        return (f"Command:\n"
                f"  Type: {self.type}\n"
                f"  Section ID: {self.section_id}\n"
                f"  Payload Length: {self.payload_len}\n"
                f"  Segment IDs: {self.segment_ids}\n"
                f"  RGB Colors: {self.rgb_colors}")

command_turn_off = Command(COMMAND_TYPE_OFF, 0x00, [0x00], [0x00])
command_segments_A = Command(COMMAND_TYPE_SINGLE_SEGMENT, SECTION_ID_A, [0x00, 0x01, 0x02], [0xFF, 0x00, 0x00]* 30)