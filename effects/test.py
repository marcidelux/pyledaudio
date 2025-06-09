import unittest
from utils import Command, Pixel, PixelArray


class TestCommandAddition(unittest.TestCase):
    def setUp(self):
        # Create some PixelArray instances for testing
        self.pixel_array_1 = PixelArray(5)
        self.pixel_array_1.set_all(Pixel(100, 0, 0))  # Red

        self.pixel_array_2 = PixelArray(5)
        self.pixel_array_2.set_all(Pixel(100, 150, 20))  # Green

        self.pixel_array_3 = PixelArray(5)
        self.pixel_array_3.set_all(Pixel(30, 200, 255))  # Blue

        # Create commands with different types and section IDs
        self.command_1 = Command(
            Command.COMMAND_TYPE_FULL_SECTION,
            Command.SECTION_ID_A,
            bytearray([0x01, 0x02]),
            self.pixel_array_1
        )

        self.command_2 = Command(
            Command.COMMAND_TYPE_FULL_SECTION,
            Command.SECTION_ID_A,
            bytearray([0x03, 0x04]),
            self.pixel_array_2
        )

        self.command_3 = Command(
            Command.COMMAND_TYPE_SINGLE_SEGMENT,
            Command.SECTION_ID_B,
            bytearray([0x05]),
            self.pixel_array_3
        )

    def test_add_commands_with_same_type_and_section(self):
        # Add two commands with the same type and section ID
        result = self.command_1 + self.command_2
        self.assertEqual(len(result), 1)
        combined_command = result[0]
        self.assertEqual(combined_command.type,
                         Command.COMMAND_TYPE_FULL_SECTION)
        self.assertEqual(combined_command.section_id, Command.SECTION_ID_A)
        self.assertEqual(combined_command.segment_ids,
                         self.command_1.segment_ids)
        self.assertEqual(combined_command.pixels.length,
                         self.pixel_array_1.length)
        self.assertEqual(
            combined_command.pixels.get_pixel(0),
            Pixel(255, 255, 0)  # Average of red and green
        )

    def test_add_commands_with_different_types(self):
        # Add two commands with different types
        result = self.command_1 + self.command_3
        # Cannot combine commands with different types
        self.assertEqual(len(result), 0)

    def test_add_commands_with_no_shared_segments(self):
        # Add two commands with no shared segment IDs
        command_a = Command(
            Command.COMMAND_TYPE_SINGLE_SEGMENT,
            Command.SECTION_ID_B,
            bytearray([0x01]),
            self.pixel_array_1
        )
        command_b = Command(
            Command.COMMAND_TYPE_SINGLE_SEGMENT,
            Command.SECTION_ID_B,
            bytearray([0x02]),
            self.pixel_array_2
        )
        result = command_a + command_b
        # Both commands are returned separately
        self.assertEqual(len(result), 2)

    def test_add_commands_with_shared_segments(self):
        # Add two commands with shared segment IDs
        command_a = Command(
            Command.COMMAND_TYPE_SINGLE_SEGMENT,
            Command.SECTION_ID_B,
            bytearray([0x01, 0x02]),
            self.pixel_array_1
        )
        command_b = Command(
            Command.COMMAND_TYPE_SINGLE_SEGMENT,
            Command.SECTION_ID_B,
            bytearray([0x02, 0x03]),
            self.pixel_array_2
        )
        result = command_a + command_b
        print(
            f"Command A: Type={command_a.type}, Section={command_a.section_id}, Segments={list(command_a.segment_ids)}, Pixels={command_a.pixels}")
        print(
            f"Command B: Type={command_b.type}, Section={command_b.section_id}, Segments={list(command_b.segment_ids)}, Pixels={command_b.pixels}")
        for i, cmd in enumerate(result):
            print(
                f"Result Command {i}: Type={cmd.type}, Section={cmd.section_id}, Segments={list(cmd.segment_ids)}, Pixels={cmd.pixels}")
        # Commands for only A, only B, and shared segments
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].segment_ids, bytearray([0x01]))  # Only in A
        self.assertEqual(result[1].segment_ids, bytearray([0x03]))  # Only in B
        self.assertEqual(result[2].segment_ids, bytearray([0x02]))  # Shared
        self.assertEqual(
            result[2].pixels.get_pixel(0),
            Pixel(127, 127, 0)  # Average of red and green
        )


if __name__ == "__main__":
    unittest.main()
