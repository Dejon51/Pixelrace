import random

# =========================================================
# BMP LOADER
# =========================================================

def bmptoarray(filename):
    with open(filename, "rb") as f:
        if f.read(2) != b'BM':
            return None, None, None

        f.seek(10)
        pixel_offset = int.from_bytes(f.read(4), 'little')

        f.seek(18)
        width = int.from_bytes(f.read(4), 'little')
        height = int.from_bytes(f.read(4), 'little')

        f.seek(pixel_offset)

        row_size = (width * 3 + 3) & ~3
        padding = row_size - (width * 3)

        temp_rows = []

        for _ in range(height):
            row = []

            for _ in range(width):
                b, g, r = f.read(3)
                row.append([r, g, b, "██"])

            f.read(padding)
            temp_rows.append(row)

        pixels = []

        for row in reversed(temp_rows):
            pixels.extend(row)

        return pixels, width, height


# =========================================================
# ARRAY TO BMP
# =========================================================

def arraytobmp(filename, pixels, width, height):

    row_size = (width * 3 + 3) & ~3
    padding = row_size - (width * 3)

    pixel_data_size = row_size * height
    file_size = 54 + pixel_data_size

    with open(filename, "wb") as f:

        f.write(b'BM')
        f.write(file_size.to_bytes(4, 'little'))
        f.write((0).to_bytes(4, 'little'))
        f.write((54).to_bytes(4, 'little'))

        # DIB HEADER
        f.write((40).to_bytes(4, 'little'))
        f.write(width.to_bytes(4, 'little'))
        f.write(height.to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))
        f.write((24).to_bytes(2, 'little'))

        f.write((0).to_bytes(4, 'little'))
        f.write(pixel_data_size.to_bytes(4, 'little'))

        f.write((0).to_bytes(16))

        # BMP STORES BOTTOM-UP
        for y in range(height - 1, -1, -1):

            for x in range(width):

                i = y * width + x

                r, g, b, _ = pixels[i]

                f.write(bytes([b, g, r]))

            f.write(b'\x00' * padding)


# =========================================================
# BLIT
# =========================================================

def blit(canvas, canvas_width,
         tile, tile_width, tile_height,
         x_offset, y_offset):

    canvas_height = len(canvas) // canvas_width

    for y in range(tile_height):

        for x in range(tile_width):

            cx = x + x_offset
            cy = y + y_offset

            if 0 <= cx < canvas_width and 0 <= cy < canvas_height:

                canvas[cy * canvas_width + cx] = tile[y * tile_width + x]


# =========================================================
# LOAD TILES
# =========================================================

horizontal, tw, th = bmptoarray("horizontal.bmp")
vertical, _, _ = bmptoarray("vertical.bmp")
up_left, _, _ = bmptoarray("up_left.bmp")
up_right, _, _ = bmptoarray("up_right.bmp")
down_left, _, _ = bmptoarray("down_left.bmp")
down_right, _, _ = bmptoarray("down_right.bmp")
up_start, _, _ = bmptoarray("sustart.bmp")
right_start, _, _ = bmptoarray("up_right.bmp")
left_start, _, _ = bmptoarray("down_left.bmp")
down_start, _, _ = bmptoarray("sdstart.bmp")

tiles = {

    "horizontal": horizontal,
    "vertical": vertical,

    "up_left": up_left,
    "up_right": up_right,

    "down_left": down_left,
    "down_right": down_right,

    "up_start": up_start,
    "right_start": right_start,
    "left_start": left_start,
    "down_start": down_start
}


# =========================================================
# TRACK GRID
# =========================================================

TRACK_W = 20
TRACK_H = 20

track = [[None for _ in range(TRACK_W)] for _ in range(TRACK_H)]


# =========================================================
# GENERATE PATH
# =========================================================

x = 0
y = random.randint(0, TRACK_H - 1)

start = (x, y)

path = [(x, y)]

while x < TRACK_W - 1:

    possible = []

    # ALWAYS ALLOW RIGHT
    possible.append((1, 0))

    # UP
    if y > 0:
        possible.append((0, -1))

    # DOWN
    if y < TRACK_H - 1:
        possible.append((0, 1))

    dx, dy = random.choice(possible)

    nx = x + dx
    ny = y + dy

    if (nx, ny) not in path:

        path.append((nx, ny))

        x = nx
        y = ny


finish = (x, y)


# =========================================================
# CONVERT PATH INTO TILES
# =========================================================

for i in range(len(path)):

    x, y = path[i]

    # =====================================================
    # FORCE START TILE
    # =====================================================

    if i == 0:

        nx, ny = path[i + 1]

        dx = nx - x
        dy = ny - y

        if dx == 1:
            track[y][x] = "right_start"

        elif dy == -1:
            track[y][x] = "up_start"

        elif dy == 1:
            track[y][x] = "down_start"

        continue

    # =====================================================
    # NORMAL TILE LOGIC
    # =====================================================

    in_dir = None
    out_dir = None

    # PREVIOUS TILE
    if i > 0:

        px, py = path[i - 1]

        in_dir = (x - px, y - py)

    # NEXT TILE
    if i < len(path) - 1:

        nx, ny = path[i + 1]

        out_dir = (nx - x, ny - y)

    # =====================================================
    # STRAIGHTS
    # =====================================================

    if in_dir == (0, 1) and out_dir == (0, 1):

        tile_name = "vertical"

    elif in_dir == (0, -1) and out_dir == (0, -1):

        tile_name = "vertical"

    elif in_dir == (1, 0) and out_dir == (1, 0):

        tile_name = "horizontal"

    # =====================================================
    # CORNERS
    # =====================================================

    # DOWN -> ?
    elif in_dir == (0, 1) and out_dir == (1, 0):

        tile_name = "down_right"

    elif in_dir == (0, 1) and out_dir == (-1, 0):

        tile_name = "down_left"

    # UP -> ?
    elif in_dir == (0, -1) and out_dir == (1, 0):

        tile_name = "up_right"

    elif in_dir == (0, -1) and out_dir == (-1, 0):

        tile_name = "up_left"

    # RIGHT -> ?
    elif in_dir == (1, 0) and out_dir == (0, 1):

        tile_name = "up_left"

    elif in_dir == (1, 0) and out_dir == (0, -1):

        tile_name = "down_left"

    # LEFT -> ?
    elif in_dir == (-1, 0) and out_dir == (0, 1):

        tile_name = "up_right"

    elif in_dir == (-1, 0) and out_dir == (0, -1):

        tile_name = "down_right"

    # =====================================================
    # FALLBACKS
    # =====================================================

    else:

        if in_dir in [(0, 1), (0, -1)] or \
           out_dir in [(0, 1), (0, -1)]:

            tile_name = "vertical"

        else:

            tile_name = "horizontal"

    track[y][x] = tile_name


# =========================================================
# BUILD BIG CANVAS
# =========================================================

map_width = TRACK_W * tw
map_height = TRACK_H * th

big_canvas = [

    [40, 140, 40, "██"]

    for _ in range(map_width * map_height)
]


# =========================================================
# DRAW TRACK
# =========================================================

for y in range(TRACK_H):

    for x in range(TRACK_W):

        tile_name = track[y][x]

        if tile_name:

            blit(
                big_canvas,
                map_width,

                tiles[tile_name],

                tw,
                th,

                x * tw,
                y * th
            )


# =========================================================
# SAVE BMP
# =========================================================

arraytobmp(
    "generated_track.bmp",
    big_canvas,
    map_width,
    map_height
)

print("generated_track.bmp created")