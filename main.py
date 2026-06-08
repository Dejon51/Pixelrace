import json
import os
import sys
import threading
import time
import winsound
from datetime import datetime
import msvcrt

# constants for game

RUNS_FILE = "runs.json"
VIEW_W = 200
VIEW_H = 100
ACCELERATION = 2
FRICTION = 0.90
MAX_SPEED = 12
FINISH_COOLDOWN = 2.0
FLASH_DURATION = 3.0

SPAWN_COLORS = {
    (34, 177, 76): 0,   # UP
    (34, 177, 75): 2,   # RIGHT
    (34, 177, 74): 4,   # DOWN
    (34, 177, 73): 6,   # LEFT
}

# Directions of acceleration
ACCEL_VECTORS = {
    0: (0, -1),
    1: (0.707, -0.707),
    2: (1, 0),
    3: (0.707, 0.707),
    4: (0, 1),
    5: (-0.707, 0.707),
    6: (-1, 0),
    7: (-0.707, -0.707),
}

# font took me very long

FONT = {
    '0': ["###", "# #", "# #", "# #", "###"], '1': [" # ", " # ", " # ", " # ", " # "],
    '2': ["###", "  #", "###", "#  ", "###"], '3': ["###", "  #", "###", "  #", "###"],
    '4': ["# #", "# #", "###", "  #", "  #"], '5': ["###", "#  ", "###", "  #", "###"],
    '6': ["###", "#  ", "###", "# #", "###"], '7': ["###", "  #", "  #", "  #", "  #"],
    '8': ["###", "# #", "###", "# #", "###"], '9': ["###", "# #", "###", "  #", "###"],
    ':': [" # ", "   ", " # ", "   ", " # "], '.': ["   ", "   ", "   ", "   ", " # "],
    ' ': ["   ", "   ", "   ", "   ", "   "], '-': ["   ", "   ", "###", "   ", "   "],
    '+': ["   ", " # ", "###", " # ", "   "],
    'A': [" # ", "# #", "###", "# #", "# #"], 'B': ["## ", "# #", "## ", "# #", "## "],
    'C': ["###", "#  ", "#  ", "#  ", "###"], 'D': ["## ", "# #", "# #", "# #", "## "],
    'E': ["###", "#  ", "###", "#  ", "###"], 'F': ["###", "#  ", "###", "#  ", "#  "],
    'G': ["###", "#  ", "# #", "# #", "###"], 'H': ["# #", "# #", "###", "# #", "# #"],
    'I': ["###", " # ", " # ", " # ", "###"], 'J': ["###", "  #", "  #", "# #", "###"],
    'K': ["# #", "# #", "## ", "# #", "# #"], 'L': ["#  ", "#  ", "#  ", "#  ", "###"],
    'M': ["# #", "###", "###", "# #", "# #"], 'N': ["#  ", "## ", "# #", "# #", "# #"],
    'O': ["###", "# #", "# #", "# #", "###"], 'P': ["## ", "# #", "## ", "#  ", "#  "],
    'Q': ["###", "# #", "# #", "###", "  #"], 'R': ["## ", "# #", "## ", "# #", "# #"],
    'S': ["###", "#  ", "###", "  #", "###"], 'T': ["###", " # ", " # ", " # ", " # "],
    'U': ["# #", "# #", "# #", "# #", "###"], 'V': ["# #", "# #", "# #", "# #", " # "],
    'W': ["# #", "# #", "# #", "###", "# #"], 'X': ["# #", "# #", " # ", "# #", "# #"],
    'Y': ["# #", "# #", "###", " # ", " # "], 'Z': ["###", "  #", " # ", "#  ", "###"],
    '!': [" # ", " # ", " # ", "   ", " # "], '?': ["###", "  #", " ##", "   ", " # "],
    '>': ["#  ", " # ", "  #", " # ", "#  "], '<': ["  #", " # ", "#  ", " # ", "  #"],
    '=': ["   ", "###", "   ", "###", "   "], '/': ["  #", "  #", " # ", "#  ", "#  "],
    '\\': ["#  ", "#  ", " # ", "  #", "  #"], '_': ["   ", "   ", "   ", "   ", "###"],
    '(': ["  #", " # ", " # ", " # ", "  #"], ')': ["#  ", " # ", " # ", " # ", "#  "],
    '[': ["## ", "#  ", "#  ", "#  ", "## "], ']': [" ##", "  #", "  #", "  #", " ##"],
    '{': ["  #", " # ", "## ", " # ", "  #"], '}': ["#  ", " # ", " ##", " # ", "#  "],
    ',': ["   ", "   ", "   ", " # ", "#  "], ';': ["   ", " # ", "   ", " # ", "#  "],
    '"': ["# #", "# #", "   ", "   ", "   "], "'": [" # ", " # ", "   ", "   ", "   "],
}

# ── BMP loading ──────────────────────────────────────────────────────────────

def bmp_to_pixels(filename):
    with open(filename, "rb") as f:
        if f.read(2) != b'BM':
            print(f"{filename} isn't a valid BMP")
            return None, None, None

        f.seek(10)
        pixel_offset = int.from_bytes(f.read(4), 'little')
        
        f.seek(18)
        width = int.from_bytes(f.read(4), 'little')
        height = int.from_bytes(f.read(4), 'little')
        
        f.seek(pixel_offset)

        row_size = (width * 3 + 3) & ~3
        padding = row_size - width * 3

        rows = []
        for _ in range(height):
            row = []
            for _ in range(width):
                b, g, r = f.read(3)
                row.append([r, g, b, "██"])
            f.read(padding)
            rows.append(row)

    pixels = [px for row in reversed(rows) for px in row]
    return pixels, width, height

def get_pixel_positions(pixels, width, target_rgb): # takes in target color returns all the pixels location with those colors
    return [
        (i % width, i // width)
        for i, (r, g, b, _) in enumerate(pixels)
        if (r, g, b) == target_rgb
    ]

# Image manipulation

WHITE = (255, 255, 255)

def white_pixel(): # returns white pixel
    return [255, 255, 255, "██"]

def overlay(base, top, mask=WHITE): # allows you to overlay things and key out a certain rgb color allowing for the illusion of transparency
    return [
        b if (t[0], t[1], t[2]) == mask else t
        for b, t in zip(base, top)
    ]

def scale_up(pixels, width, sx, sy):
    height = len(pixels) // width
    new_w = int(width * sx)
    new_h = int(height * sy)
    new_pixels = [white_pixel() for _ in range(new_w * new_h)]

    for y in range(height):
        for x in range(width):
            px = pixels[y * width + x]
            x0, x1 = int(x * sx), int((x + 1) * sx)
            y0, y1 = int(y * sy), int((y + 1) * sy)
            for yy in range(y0, y1):
                if 0 <= yy < new_h:
                    for xx in range(x0, x1):
                        if 0 <= xx < new_w:
                            new_pixels[yy * new_w + xx] = px

    return new_pixels, new_w, new_h

def crop(pixels, width, x0, y0, cw, ch): # crops image
    height = len(pixels) // width
    result = []
    for y in range(y0, y0 + ch):
        for x in range(x0, x0 + cw):
            if 0 <= x < width and 0 <= y < height:
                result.append(pixels[y * width + x])
            else:
                result.append(white_pixel())
    return result, cw, ch

# Graphics

prev_frame = ""

def clear_screen(): # clears frame
    print("\033[H", end="")

def render(pixels, width): 
    global prev_frame
    parts = []
    for i, (r, g, b, ch) in enumerate(pixels):
        parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m")
        if (i + 1) % width == 0:
            parts.append("\n")
    frame = "".join(parts)
    if frame != prev_frame:
        sys.stdout.write(frame)
        sys.stdout.flush()
        prev_frame = frame

def draw_text(canvas, canvas_w, canvas_h, text, x, y, color): # returns pixels for text
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[' '])
        char_w = max(len(row) for row in glyph)
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == '#':
                    px, py = cx + col_i, y + row_i
                    if 0 <= px < canvas_w and 0 <= py < canvas_h:
                        canvas[py * canvas_w + px] = [*color, "██"]
        cx += char_w + 1

def fill_bar(canvas, width, y0, y1, color): # draws a bar
    for py in range(y0, y1):
        for px in range(width):
            canvas[py * width + px] = [*color, "██"]

# format time

def fmt_time(seconds): # returns time in a stopwatch fashion
    m = int(seconds) // 60
    s = int(seconds) % 60
    ms = int((seconds - int(seconds)) * 1000)
    return f"{m:02d}:{s:02d}.{ms:03d}"

# Storage stuff with json

def load_runs(): # gets all the runs and best ghost
    if not os.path.exists(RUNS_FILE):
        return {"best_time": None, "runs": [], "best_ghost": None}
    try:
        with open(RUNS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"best_time": None, "runs": [], "best_ghost": None}

def save_runs(data): # saves runs in json to file
    try:
        with open(RUNS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def record_run(lap_time, ghost_frames): # records runs for ghost and also saves to file
    data = load_runs()
    data["runs"].append({
        "time": lap_time,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "formatted": fmt_time(lap_time),
    })
    is_new_best = data["best_time"] is None or lap_time < data["best_time"]
    if is_new_best:
        data["best_time"] = lap_time
        data["best_ghost"] = ghost_frames
    save_runs(data)
    return is_new_best

def get_best_time():
    return load_runs().get("best_time") # gets best time out of the json

def get_best_ghost():
    return load_runs().get("best_ghost") # gets best time for ghost

def get_all_runs():
    return load_runs().get("runs", []) # returns a list of all the runs aka time

# Previous run recording

class GhostRecorder: # class records car movement
    def __init__(self, frames=None):
        self.frames = [(float(f[0]), float(f[1]), int(f[2])) for f in frames] if frames else []
        self.recording = frames is None
        self.index = 0

    def record(self, x, y, direction): # records movements of car using X and Y and direction
        if self.recording:
            self.frames.append((float(x), float(y), int(direction)))

    def stop(self): #stops recording movement
        self.recording = False

    def reset(self): # resets ghost
        self.index = 0

    def next_frame(self):
        if not self.frames or self.index >= len(self.frames):
            return None
        frame = self.frames[self.index]
        self.index += 1
        return frame

# car animations

CAR_COLOR_KEY = (22, 23, 13)

CAR_ASSETS = [
    r".\assets\fcar.bmp",
    r".\assets\sfcar.bmp",
    r".\assets\rcar.bmp",
    r".\assets\lfcar.bmp",
    r".\assets\bcar.bmp",
    r".\assets\lrcar.bmp",
    r".\assets\lcar.bmp",
    r".\assets\fscar.bmp",
]

class Car: # class for car takes all assets takes color and direction and outputs the pixels for the car
    def __init__(self, direction=0, color=(0, 255, 0)):
        self.sprites = [bmp_to_pixels(p) for p in CAR_ASSETS]
        self.layers = [s[0] for s in self.sprites]
        self.widths = [s[1] for s in self.sprites]
        self.color = color
        self.direction = direction
        self.tinted = None
        self.set_sprite(direction)

    def set_sprite(self, direction):
        self.direction = direction
        self.base = self.layers[direction]
        self.width = self.widths[direction]
        self.tint()

    def tint(self):
        r, g, b = self.color
        self.tinted = [
            [r, g, b, ch] if (pr, pg, pb) == CAR_COLOR_KEY else [pr, pg, pb, ch]
            for pr, pg, pb, ch in self.base
        ]

    def turn(self, delta):
        self.set_sprite((self.direction + delta) % 8)

    def pixels(self):
        return self.tinted

# GUI drawing

DARK = (15, 15, 15) # constants for all the colors
DARKER = (15, 15, 40)
GREY = (150, 150, 150)
CYAN = (0, 255, 200)
GOLD = (255, 200, 0)
BLUE = (130, 130, 255)

def draw_hud(canvas, w, h, lap_time, best_time, finished, has_ghost): # like finish line overlay except its draw while driving and it shows your time
    fill_bar(canvas, w, 0, 8, DARK)

    time_color = (255, 220, 0) if finished else CYAN
    draw_text(canvas, w, h, "LAP:", 1, 1, GREY)
    draw_text(canvas, w, h, fmt_time(lap_time), 22, 1, time_color)

    if best_time is not None:
        draw_text(canvas, w, h, "BEST:", 76, 1, GREY)
        draw_text(canvas, w, h, fmt_time(best_time), 101, 1, GOLD)

    if has_ghost:
        for py in range(8):
            for px in range(w - 40, w):
                canvas[py * w + px] = [*DARKER, "██"]
        draw_text(canvas, w, h, "GHOST", w - 38, 1, BLUE)

def draw_finish_overlay(canvas, w, h, lap_time, best_time): # draws finish overlay with time and with the word ghost
    fill_bar(canvas, w, h - 10, h, DARK)

    draw_text(canvas, w, h, "TIME:", 1, h - 9, GREY)
    draw_text(canvas, w, h, fmt_time(lap_time), 30, h - 9, GOLD)

    if best_time is not None:
        delta = lap_time - best_time
        if delta < -0.0001:
            delta_str, delta_col, label = f"-{fmt_time(abs(delta))}", (0, 255, 100), "NEW BEST!"
        elif delta > 0.0001:
            delta_str, delta_col, label = f"+{fmt_time(delta)}", (255, 80, 80), "FINISH"
        else:
            delta_str, delta_col, label = "+0.000", (255, 255, 255), "FINISH"

        draw_text(canvas, w, h, label, 100, h - 9, (200, 200, 200))
        draw_text(canvas, w, h, delta_str, 140, h - 9, delta_col)

# ghost draw

GHOST_COLOR = (80, 120, 255)
CAR_SPRITES = [bmp_to_pixels(p) for p in CAR_ASSETS]

def draw_ghost(canvas, w, h, gx, gy, gdir, cam_x, cam_y): # draws car ghost
    layer, gw = CAR_SPRITES[gdir][0], CAR_SPRITES[gdir][1]
    for i, (r, g, b, _) in enumerate(layer):
        if (r, g, b) == WHITE:
            continue
        sx = int(gx) + (i % gw) - cam_x
        sy = int(gy) + (i // gw) - cam_y
        if 0 <= sx < w and 0 <= sy < h:
            idx = sy * w + sx
            existing = canvas[idx]
            canvas[idx] = [
                (existing[0] + GHOST_COLOR[0]) // 2,
                (existing[1] + GHOST_COLOR[1]) // 2,
                (existing[2] + GHOST_COLOR[2]) // 2,
                "██",
            ]

# Movement calculations for nice car drifting

def apply_acceleration(vx, vy, direction, magnitude):
    dx, dy = ACCEL_VECTORS[direction]
    return vx + dx * magnitude, vy + dy * magnitude

def clamp_speed(vx, vy, max_spd): # stops speed from going lower or higher than a certain speed
    speed = (vx**2 + vy**2) ** 0.5
    if speed > max_spd:
        vx, vy = vx / speed * max_spd, vy / speed * max_spd
    return vx, vy

# Intro animation played at start

def play_intro():
    intro_pixels, intro_w, intro_h = bmp_to_pixels("intro.bmp")
    intro_pixels, intro_w, intro_h = scale_up(intro_pixels, intro_w, 2, 2)

    clear_screen()
    render(intro_pixels, intro_w)

    bg_pixels, bg_w, bg_h = bmp_to_pixels(r".\intro\title_background.bmp")
    bg_pixels, bg_w, bg_h = scale_up(bg_pixels, bg_w, 2, 2)

    for frame in range(16):
        time.sleep(0.06)
        fg_pixels, fg_w, fg_h = bmp_to_pixels(rf".\intro\frame{frame}.bmp")
        fg_pixels, fg_w, fg_h = scale_up(fg_pixels, fg_w, 2, 2)
        clear_screen()
        render(overlay(bg_pixels, fg_pixels), bg_w)

    clear_screen()
    render(bg_pixels, bg_w)

    track_pixels, track_w, track_h = bmp_to_pixels("generated_track.bmp")
    return track_pixels, track_w, track_h

# Game booting up 

def play(bg_pixels, bg_width):
    height = len(bg_pixels) // bg_width

    car_x, car_y, direction = 0.0, 0.0, 0
    for color, d in SPAWN_COLORS.items():
        positions = get_pixel_positions(bg_pixels, bg_width, color)
        if positions:
            px, py = positions[0]
            car_x = float(px - 25)
            car_y = float(py - 14)
            direction = d
            break

    finish_line = get_pixel_positions(bg_pixels, bg_width, (163, 73, 164))

    car = Car(direction)
    vx, vy = 0.0, 0.0

    lap_start = time.time()
    last_tick = time.time()
    lap_time = 0.0
    finished = False
    flash_timer = 0.0
    cooldown_start = time.time()

    saved_frames = get_best_ghost()
    ghost_replay = GhostRecorder(saved_frames) if saved_frames else None
    recorder = GhostRecorder() 
    ghost_frame = None
    session_best = get_best_time()
    dirty = True

    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            is_escape = key in (b'\xe0', b'\x00')
            
            if is_escape:
                arrow = msvcrt.getch()
                if arrow == b'K':
                    car.turn(-1)
                    dirty = True
                elif arrow == b'M':
                    car.turn(+1)
                    dirty = True
                elif arrow == b'H':
                    vx, vy = apply_acceleration(vx, vy, car.direction, ACCELERATION)
                elif arrow == b'P':
                    vx, vy = apply_acceleration(vx, vy, car.direction, -ACCELERATION)
            else:
                key = key.lower()
                if key == b'\x1b':
                    break
                elif key == b'a':
                    car.turn(-1)
                    dirty = True
                elif key == b'd':
                    car.turn(+1)
                    dirty = True
                elif key == b'w':
                    vx, vy = apply_acceleration(vx, vy, car.direction, ACCELERATION)
                elif key == b's':
                    vx, vy = apply_acceleration(vx, vy, car.direction, -ACCELERATION)

        vx *= FRICTION
        vy *= FRICTION
        vx, vy = clamp_speed(vx, vy, MAX_SPEED)
        if abs(vx) < 0.01: 
            vx = 0.0
        if abs(vy) < 0.01: 
            vy = 0.0

        car_x = max(-15, min(car_x + vx, bg_width - 34))
        car_y = max(-3, min(car_y + vy, height - 22))
        
        if vx or vy:
            dirty = True

        cam_x = int(car_x - 75)
        cam_y = int(car_y - 40)

        now = time.time()
        dt = now - last_tick
        last_tick = now

        if not finished:
            lap_time = now - lap_start
        else:
            flash_timer -= dt
            if flash_timer <= 0:
                finished = False
                lap_start = time.time()
                lap_time = 0.0
                recorder = GhostRecorder()
                cooldown_start = time.time()
                if ghost_replay:
                    ghost_replay.reset()
                dirty = True

        if not finished:
            recorder.record(car_x, car_y, car.direction)

        if not finished and finish_line and (now - cooldown_start) >= FINISH_COOLDOWN:
            for px, py in finish_line:
                if abs(int(car_x) - px) <= 10 and abs(int(car_y) - py) <= 10:
                    finished = True
                    flash_timer = FLASH_DURATION
                    recorder.stop()
                    is_new_best = record_run(lap_time, recorder.frames)
                    session_best = get_best_time()
                    if is_new_best:
                        ghost_replay = GhostRecorder(recorder.frames)
                    dirty = True
                    break

        ghost_frame = ghost_replay.next_frame() if (ghost_replay and not finished) else None

        if dirty or vx or vy or ghost_frame is not None:
            view, _, _ = crop(bg_pixels, bg_width, cam_x, cam_y, VIEW_W, VIEW_H)
            canvas = list(view)

            if ghost_frame:
                draw_ghost(canvas, VIEW_W, VIEW_H, *ghost_frame, cam_x, cam_y)

            car_w = car.width
            for i, (r, g, b, ch) in enumerate(car.pixels()):
                if (r, g, b) == WHITE:
                    continue
                sx = int(car_x) + (i % car_w) - cam_x
                sy = int(car_y) + (i // car_w) - cam_y
                if 0 <= sx < VIEW_W and 0 <= sy < VIEW_H:
                    canvas[sy * VIEW_W + sx] = [r, g, b, ch]

            draw_hud(canvas, VIEW_W, VIEW_H, lap_time, session_best, finished, ghost_replay is not None)
            if finished:
                draw_finish_overlay(canvas, VIEW_W, VIEW_H, lap_time, session_best)

            clear_screen()
            render(canvas, VIEW_W)
            dirty = False

        time.sleep(0.01)

# switched from static images for a menu to moveable buttons and text

MENU_W, MENU_H = 200, 50
MENU_BG = (10, 10, 18)
DIVIDER_COL = (40, 40, 60)

MENU_OPTIONS = ["PLAY", "MUSIC", "RUNS", "QUIT"]
MUSIC_LABELS = {True: "MUS OFF", False: "MUS ON"}

def draw_menu(canvas, selected, music_off, blink_on): # draws meenu with buttons
    for i in range(len(canvas)):
        canvas[i] = [*MENU_BG, "██"]

    title_x = (MENU_W - len("    PIXELRACE") * 5) // 2
    draw_text(canvas, MENU_W, MENU_H, "    PIXELRACE", title_x, 4, (0, 220, 255))

    fill_bar(canvas, MENU_W, 12, 13, DIVIDER_COL)

    best = get_best_time()
    if best is not None:
        bt_str = f"BEST: {fmt_time(best)}"
        draw_text(canvas, MENU_W, MENU_H, bt_str, (MENU_W - len(bt_str) * 5) // 2, 15, GOLD)

    total_w = len(MENU_OPTIONS) * 30
    start_x = (MENU_W - total_w) // 2
    opt_y = MENU_H // 2 - 3

    for i, label in enumerate(MENU_OPTIONS):
        ox = start_x + i * 30
        if label == "MUSIC":
            label = MUSIC_LABELS[music_off]

        if i == selected:
            box = (0, 180, 255) if blink_on else (0, 100, 180)
            char_w = len(label) * 4
            for py in range(opt_y - 2, opt_y + 9):
                for px in range(ox - 2, ox + char_w + 2):
                    if 0 <= px < MENU_W and 0 <= py < MENU_H:
                        canvas[py * MENU_W + px] = [*box, "██"]
            txt_col = (0, 0, 0)
        else:
            txt_col = (160, 160, 160)

        draw_text(canvas, MENU_W, MENU_H, label, ox, opt_y, txt_col)

    if selected > 0:
        draw_text(canvas, MENU_W, MENU_H, "<", start_x - 8, opt_y, (80, 80, 80))
    if selected < len(MENU_OPTIONS) - 1:
        draw_text(canvas, MENU_W, MENU_H, ">", start_x + len(MENU_OPTIONS) * 30, opt_y, (80, 80, 80))

    draw_text(canvas, MENU_W, MENU_H, "A/D OR ARROWS: SELECT   ENTER: CONFIRM  ESC: BACK", 2, MENU_H - 8, (50, 50, 70))

def draw_runs(canvas, scroll): # Draws timed runs on menu 
    for i in range(len(canvas)):
        canvas[i] = [*MENU_BG, "██"]

    draw_text(canvas, MENU_W, MENU_H, "RUN HISTORY", 4, 2, (0, 220, 255))
    fill_bar(canvas, MENU_W, 9, 10, DIVIDER_COL)

    runs = get_all_runs()
    best_t = get_best_time()
    row_h = 8
    max_rows = (MENU_H - 14) // row_h

    if not runs:
        draw_text(canvas, MENU_W, MENU_H, "NO RUNS YET", 4, 13, (120, 120, 120))
    else:
        for idx in range(max_rows):
            ri = scroll + idx
            if ri >= len(runs):
                break
            run = runs[-(ri + 1)]
            lap_n = len(runs) - ri
            is_best = best_t is not None and abs(run["time"] - best_t) < 0.0001
            color = GOLD if is_best else (180, 180, 180)
            label = f"#{lap_n:02d}  {run['formatted']}  {run['date']}"
            if is_best:
                label += "  <BEST>"
            draw_text(canvas, MENU_W, MENU_H, label, 4, 12 + idx * row_h, color)

    draw_text(canvas, MENU_W, MENU_H, "ESC: BACK", 4, MENU_H - 8, (50, 50, 70))

# Versatile music

def play_music(): # plays versatile music
    winsound.PlaySound(r".\assets\music\versatile.wav", winsound.SND_ASYNC)

# ------------------------------------------------------------

bg_pixels, bg_width, _ = play_intro()

selected = 0
music_off = True
blink_on = True
blink_timer = time.time()
BLINK_RATE = 0.4

screen = "menu"
runs_scroll = 0
dirty = True

canvas = [[*MENU_BG, "██"] for _ in range(MENU_W * MENU_H)]

sys.stdout.write("\033[2J\033[H")
sys.stdout.flush()

while True:
    now = time.time()
    if now - blink_timer >= BLINK_RATE:
        blink_on = not blink_on
        blink_timer = now
        dirty = True

    if msvcrt.kbhit():
        key = msvcrt.getch()
        is_escape = key in (b'\xe0', b'\x00')

        if is_escape:
            arrow = msvcrt.getch()
            if screen == "menu":
                if arrow == b'K':
                    selected = (selected - 1) % 4
                    dirty = True
                elif arrow == b'M':
                    selected = (selected + 1) % 4
                    dirty = True
            elif screen == "runs":
                if arrow == b'H':
                    runs_scroll = max(0, runs_scroll - 1)
                    dirty = True
                elif arrow == b'P':
                    runs_scroll += 1
                    dirty = True
        else:
            key = key.lower()

            if screen == "menu":
                if key == b'a':
                    selected = (selected - 1) % 4
                    dirty = True
                elif key == b'd':
                    selected = (selected + 1) % 4
                    dirty = True
                elif key == b'\r':
                    if selected == 0:
                        prev_frame = ""
                        if not music_off:
                            threading.Thread(target=play_music).start() # Plays music on seperate thread as to not block the single threaded code
                        play(bg_pixels, bg_width)
                        winsound.PlaySound(None, winsound.SND_PURGE) # Stops music
                        sys.stdout.write("\033[2J\033[H")
                        sys.stdout.flush()
                        prev_frame = ""
                        dirty = True
                    elif selected == 1:
                        music_off = not music_off
                        dirty = True
                    elif selected == 2:
                        screen = "runs"
                        runs_scroll = 0
                        dirty = True
                    elif selected == 3:
                        clear_screen()
                        break

            elif screen == "runs":
                if key in (b'\x1b', b'\r'):
                    screen = "menu"
                    dirty = True
                elif key == b'w':
                    runs_scroll = max(0, runs_scroll - 1)
                    dirty = True
                elif key == b's':
                    runs_scroll += 1
                    dirty = True

    if dirty:
        if screen == "menu":
            draw_menu(canvas, selected, music_off, blink_on)
        else:
            draw_runs(canvas, runs_scroll)
        
        clear_screen()
        render(canvas, MENU_W)
        dirty = False

    time.sleep(0.01)