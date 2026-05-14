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

        # Load rows bottom-up as they are in the file
        temp_rows = []
        for _ in range(height):
            row = []
            for _ in range(width):
                b, g, r = f.read(3)
                row.append([r, g, b, "██"])
            f.read(padding)
            temp_rows.append(row)

        # Flip the rows to get top-down order for easy blitting
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
        f.write((40).to_bytes(4, 'little'))
        f.write(width.to_bytes(4, 'little'))
        f.write(height.to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))
        f.write((24).to_bytes(2, 'little'))
        f.write((0).to_bytes(4, 'little'))
        f.write(pixel_data_size.to_bytes(4, 'little'))
        f.write((0).to_bytes(16))

        # Write rows bottom-up
        for y in range(height - 1, -1, -1):
            for x in range(width):
                i = y * width + x
                r, g, b, _ = pixels[i]
                f.write(bytes([b, g, r]))
            f.write(b'\x00' * padding)

# =========================================================
# BLIT
# =========================================================

def blit(canvas, canvas_width, tile, tile_width, tile_height, x_offset, y_offset):
    canvas_height = len(canvas) // canvas_width
    for y in range(tile_height):
        for x in range(tile_width):
            cx = x + x_offset
            cy = y + y_offset
            if 0 <= cx < canvas_width and 0 <= cy < canvas_height:
                canvas[cy * canvas_width + cx] = tile[y * tile_width + x]

# =========================================================
# GENERATE TRACK
# =========================================================

horizontal, tw, th = bmptoarray("horizontal.bmp")
vertical, _, _ = bmptoarray("vertical.bmp")
up_left, _, _ = bmptoarray("up_left.bmp")
up_right, _, _ = bmptoarray("up_right.bmp")
down_left, _, _ = bmptoarray("down_left.bmp")
down_right, _, _ = bmptoarray("down_right.bmp")

tiles = {
    "horizontal": horizontal, "vertical": vertical,
    "up_left": up_left, "up_right": up_right,
    "down_left": down_left, "down_right": down_right
}

TRACK_W, TRACK_H = 20, 20
track = [[None for _ in range(TRACK_W)] for _ in range(TRACK_H)]

x, y = 0, random.randint(0, TRACK_H - 1)
start, path = (x, y), [(x, y)]

while x < TRACK_W - 1:
    possible = [(1, 0)] # Always allow right
    if y > 0: possible.append((0, -1))
    if y < TRACK_H - 1: possible.append((0, 1))
    
    dx, dy = random.choice(possible)
    nx, ny = x + dx, y + dy

    if (nx, ny) not in path:
        path.append((nx, ny))
        x, y = nx, ny

finish = (x, y)

# Logic for tile selection
# =========================================================
# CONVERT PATH INTO TILES (Directional Logic)
# =========================================================

for i in range(len(path)):
    x, y = path[i]
    
    in_dir = None
    if i > 0:
        px, py = path[i - 1]
        in_dir = (x - px, y - py)
    
    out_dir = None
    if i < len(path) - 1:
        nx, ny = path[i + 1]
        out_dir = (nx - x, ny - y)

    # 1. PURE STRAIGHTS (Both directions match or one is missing at ends)
    if in_dir == (0, 1) and out_dir == (0, 1):
        tile_name = "vertical"
    elif in_dir == (0, -1) and out_dir == (0, -1):
        tile_name = "vertical"
    elif in_dir == (1, 0) and out_dir == (1, 0):
        tile_name = "horizontal"
    
    # 2. CORNERS (Your entry -> exit naming scheme)
    # Down then...
    elif in_dir == (0, 1) and out_dir == (1, 0): tile_name = "down_right"
    elif in_dir == (0, 1) and out_dir == (-1, 0): tile_name = "down_left"
    # Up then...
    elif in_dir == (0, -1) and out_dir == (1, 0): tile_name = "up_right"
    elif in_dir == (0, -1) and out_dir == (-1, 0): tile_name = "up_left"
    # Right then...
    elif in_dir == (1, 0) and out_dir == (0, 1): tile_name = "up_left"
    elif in_dir == (1, 0) and out_dir == (0, -1): tile_name = "down_left"
    # Left then...
    elif in_dir == (-1, 0) and out_dir == (0, 1): tile_name = "up_right"
    elif in_dir == (-1, 0) and out_dir == (0, -1): tile_name = "down_right"

    # 3. START / FINISH FALLBACKS
    else:
        # If it's the start/end and moving vertically, use vertical
        if in_dir in [(0, 1), (0, -1)] or out_dir in [(0, 1), (0, -1)]:
            tile_name = "vertical"
        else:
            tile_name = "horizontal"

    track[y][x] = tile_name
# Build Canvas
map_width, map_height = TRACK_W * tw, TRACK_H * th
big_canvas = [[40, 140, 40, "██"] for _ in range(map_width * map_height)]

for y in range(TRACK_H):
    for x in range(TRACK_W):
        name = track[y][x]
        if name:
            blit(big_canvas, map_width, tiles[name], tw, th, x * tw, y * th)

arraytobmp("generated_track.bmp", big_canvas, map_width, map_height)