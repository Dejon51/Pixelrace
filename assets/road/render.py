import time
import msvcrt


def bmptoarray(filename):
    with open(filename, "rb") as f:
        if f.read(2) != b'BM':
            print(f"{filename} Isn't a valid bmp")
            return None, None, None

        f.seek(10)
        pixel_offset = int.from_bytes(f.read(4), 'little')

        f.seek(18)
        width = int.from_bytes(f.read(4), 'little')
        height = int.from_bytes(f.read(4), 'little')

        f.seek(pixel_offset)

        row_size = (width * 3 + 3) & ~3
        padding = row_size - (width * 3)

        pixels = []

        for _ in range(height):
            for _ in range(width):
                b, g, r = f.read(3)
                pixels.append([r, g, b, "██"])

            f.read(padding)

        # flip rows
        pixels = [
            px
            for row in range(height - 1, -1, -1)
            for px in pixels[row * width:(row + 1) * width]
        ]

        return pixels, width, height


# -------------------------------------------------------------

def crop(layer, width, start_x, start_y, crop_width, crop_height):
    height = len(layer) // width

    new_layer = []

    for y in range(start_y, start_y + crop_height):
        for x in range(start_x, start_x + crop_width):

            if 0 <= x < width and 0 <= y < height:
                i = y * width + x
                new_layer.append(layer[i])
            else:
                new_layer.append([255, 255, 255, "██"])

    return new_layer, crop_width, crop_height


# -------------------------------------------------------------

def clear_call():
    print("\033[H", end="")


def draw_call(draw_canvas, canvas_width):
    parts = []

    for i in range(len(draw_canvas)):
        r, g, b, ch = draw_canvas[i]

        parts.append(
            f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m"
        )

        if (i + 1) % canvas_width == 0:
            parts.append("\n")

    print("".join(parts), end="", flush=True)




pixels, img_width, img_height = bmptoarray("generated_track.bmp")

view_width = 100
view_height = 50

camera_x = 0
camera_y = 0

# clear screen once
print("\033[2J", end="")

# -------------------------------------------------------------
# CAMERA LOOP

while True:

    frame, fw, fh = crop(
        pixels,
        img_width,
        camera_x,
        camera_y,
        view_width,
        view_height
    )

    clear_call()
    draw_call(frame, fw)

    print("\nWASD = move camera | Q = quit")

    # movement
    if msvcrt.kbhit():

        key = msvcrt.getch().lower()

        if key == b'w':
            camera_y -= 1

        elif key == b's':
            camera_y += 100

        elif key == b'a':
            camera_x -= 100

        elif key == b'd':
            camera_x += 100

        elif key == b'q':
            break

    # keep camera inside image
    camera_x = max(0, min(camera_x, img_width - view_width))
    camera_y = max(0, min(camera_y, img_height - view_height))

    time.sleep(0.01)