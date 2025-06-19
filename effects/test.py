from utils import Pixel, PixelArray, Command, Colors


def test_pixel_array_addition():
    a = PixelArray(3, pixels=[
        Pixel(30, 0, 0),
        Pixel(0, 30, 0),
        Pixel(0, 0, 30)])
    b = PixelArray(3, pixels=[
        Pixel(0, 10, 100),
        Pixel(10, 0, 10),
        Pixel(10, 10, 0)])

    print("PixelArray A:")
    print(a)
    print("PixelArray B:")
    print(b)

    result = a + b
    print("A + B =")
    print(result)


def test_command_addition():
    px_a = PixelArray(3, pixels=[Colors.RED, Colors.GREEN, Colors.BLUE])
    px_b = PixelArray(3, pixels=[Colors.BLUE, Colors.GREEN, Colors.RED])

    cmd_a = Command(
        Command.COMMAND_TYPE_SINGLE_SEGMENT,
        Command.SECTION_ID_A,
        bytearray([1, 2]),
        px_a
    )

    cmd_b = Command(
        Command.COMMAND_TYPE_SINGLE_SEGMENT,
        Command.SECTION_ID_A,
        bytearray([2, 3]),
        px_b
    )

    print("Command A:")
    print(cmd_a)
    print("Command B:")
    print(cmd_b)

    combined = cmd_a + cmd_b
    print("Combined Result:")
    for c in combined:
        print(c)


if __name__ == "__main__":
    test_pixel_array_addition()
    print("\n---\n")
    test_command_addition()
