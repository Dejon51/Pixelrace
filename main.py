import time
import msvcrt
import sys
import winsound
import threading

def bmptoarray(filename):
    with open(filename, "rb") as f:
        if f.read(2) != b'BM': # checks first two letters and returns nothing if it isnt a valid bmp
            print(f"{filename} Isn't a valid bmp")
            return None, None, None

        f.seek(10) # skips to pixel offset
        pixel_offset = int.from_bytes(f.read(4), 'little') 

        f.seek(18)
        width = int.from_bytes(f.read(4), 'little')
        height = int.from_bytes(f.read(4), 'little') # gets width and height

        f.seek(pixel_offset)

        row_size = (width * 3 + 3) & ~3
        padding = row_size - (width * 3)

        pixels = []

        for _ in range(height):
            for _ in range(width):
                b, g, r = f.read(3)
                pixels.append([r, g, b, "██"])  # flat append
            f.read(padding)

        #  flip rows
        width_height = width
        flat_height = height

        # reverse row in flat array
        row_len = width
        pixels = [
            px
            for row in range(height - 1, -1, -1)
            for px in pixels[row * row_len:(row + 1) * row_len]
        ]

        return pixels, width_height, flat_height

# -------------------------------------------------------- Divider to seperate bmp code from draw code


def overlay_layers(layer1, layer2, mask=(255,255,255)):
    result = []

    for px1, px2 in zip(layer1, layer2): # combines the items of an array to create many tuples
        r2, g2, b2, _ = px2

        # treat pure white as transparent
        if (r2, g2, b2) == mask:
            result.append(px1)
        else:
            result.append(px2)

    return result

def offset(layer, width, offsetx, offsety):
    length = len(layer)
    height = length // width

    new_layer = [[255, 255, 255, "██"] for _ in range(length)]

    for i in range(length):
        x = i % width
        y = i // width

        x_new = x + offsetx
        y_new = y + offsety

        if 0 <= x_new < width and 0 <= y_new < height:
            new_i = y_new * width + x_new
            new_layer[new_i] = layer[i]

    return new_layer

def scale(layer, width, scalex, scaley):
    length = len(layer)
    height = length // width

    new_width = int(width * scalex)
    new_height = int(height * scaley)
    new_length = new_width * new_height

    new_layer = [[255, 255, 255, "██"] for _ in range(new_length)]

    for i in range(length):
        x = i % width
        y = i // width

        x_new = int(x * scalex)
        y_new = int(y * scaley)

        if 0 <= x_new < new_width and 0 <= y_new < new_height:
            new_i = y_new * new_width + x_new
            new_layer[new_i] = layer[i]

    return new_layer, new_width, new_height

def scale2(layer, width, scalex, scaley):
    length = len(layer)
    height = length // width

    new_width = int(width * scalex)
    new_height = int(height * scaley)
    new_length = new_width * new_height

    new_layer = [[255, 255, 255, "██"] for _ in range(new_length)]

    for y in range(height):
        for x in range(width):
            pixel = layer[y * width + x]

            # destination block boundaries
            x_start = int(x * scalex)
            x_end = int((x + 1) * scalex)

            y_start = int(y * scaley)
            y_end = int((y + 1) * scaley)

            for yy in range(y_start, y_end):
                if 0 <= yy < new_height:
                    for xx in range(x_start, x_end):
                        if 0 <= xx < new_width:
                            new_layer[yy * new_width + xx] = pixel

    return new_layer, new_width, new_height

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

def get_pixel_pos(layer, width, target_rgb):
    positions = []

    for i, pixel in enumerate(layer):
        r, g, b, _ = pixel

        if (r, g, b) == target_rgb:
            x = i % width
            y = i // width
            positions.append((x, y))

    return positions

# image manipulation ---------------------------------------------------------------

def clear_call():
    print("\033[H", end="")

def draw_call(draw_canvas, canvas_length):
    parts = []
    for i in range(len(draw_canvas)):
        r, g, b, ch = draw_canvas[i]
        parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m")
        if (i + 1) % canvas_length == 0:
            parts.append("\n")

    sys.stdout.write("".join(parts))
    sys.stdout.flush()

# Drawing stuff -------------------------------------------------------------------------------------


def intro():
    pixels, intro_w, intro_h = bmptoarray("intro.bmp")
    piexls, intro_w, intro_h = scale2(pixels, intro_w, 2, 2)

    background, bg_w, bg_h = bmptoarray(".\\intro\\title_background.bmp")
    background, bg_w, bg_h = scale2(background, bg_w, 2, 2)

    clear_call()
    draw_call(pixels, intro_w)

    for frame in range(16):
        time.sleep(0.06)

        fg_pixels, fg_w, fg_h = bmptoarray(f".\\intro\\frame{frame}.bmp")
        fg_pixels, fg_w, fg_h = scale2(fg_pixels, fg_w, 2, 2)

        combined = overlay_layers(background, fg_pixels)

        clear_call()
        draw_call(combined, bg_w)

    clear_call()
    draw_call(background, bg_w)

    bg_pixels, bg_width, bg_height = bmptoarray("generated_track.bmp")
    return (bg_pixels, bg_width, bg_height)



# Car class
class Car:
    def __init__(self, images, direction=0, color=(255,255,255)):
        self.direction = direction
        self.color = color
        self.images = images
        # Store the layer and width for each direction
        self.layers = [img[0] for img in images]
        self.widths = [img[1] for img in images]
        self.length = len(self.layers[0])
        self.layer = self.layers[0]
        self.width = self.widths[0]
        self.new_layer = self.layer.copy()
        
    def setDirection(self, direction):
        self.direction = direction
        self.layer = self.layers[self.direction]
        self.width = self.widths[self.direction]
        self.setColor(self.color)
        
    def setColor(self, color):
        self.color = color
        self.new_layer = []
        for i in range(len(self.layer)):
            r, g, b, ch = self.layer[i]
            if (r, g, b) == (22, 23, 13):
                self.new_layer.append([color[0], color[1], color[2], ch])
            else:
                self.new_layer.append([r, g, b, ch])
                
    def returnCar(self):
        return self.new_layer


# Load car direction images
car_directions = [
    bmptoarray(".\\assets\\fcar.bmp"), 
    bmptoarray(".\\assets\\sfcar.bmp"),
    bmptoarray(".\\assets\\rcar.bmp"),
    bmptoarray(".\\assets\\lfcar.bmp"),
    bmptoarray(".\\assets\\bcar.bmp"),
    bmptoarray(".\\assets\\lrcar.bmp"),
    bmptoarray(".\\assets\\lcar.bmp"),
    bmptoarray(".\\assets\\fscar.bmp")
]
# 0 is up, 1 is up right, 2 is right, 3 is down right, 4 is down, 5 is down left, 6 is left, 7 is up left

def play_sound():
    filename = ".\\assets\\output.wav"
    winsound.PlaySound(filename, winsound.SND_SYNC | winsound.SND_ASYNC)


def play(bg_pixels, bg_width):
    height = len(bg_pixels) // bg_width

    VIEW_W = 200
    VIEW_H = 100

    UP    = (34, 177, 76)
    RIGHT = (34, 177, 75)
    DOWN  = (34, 177, 74)
    LEFT  = (34, 177, 73)

    color_to_dir = {
        UP: 0,
        RIGHT: 2,
        DOWN: 4,
        LEFT: 6
    }

    pixel_x, pixel_y = 0, 0
    start_direction = 0
    found = False

    for color in color_to_dir.keys():
        result = get_pixel_pos(bg_pixels, bg_width, color)
        if result:
            pixel_x, pixel_y = result[0]
            start_direction = color_to_dir[color]
            found = True
            break

    if not found:
        pixel_x, pixel_y = 0, 0
        start_direction = 0

    car = Car(car_directions, start_direction, (0, 255, 0))

    car.direction = start_direction
    car.setDirection(start_direction)
    car.setColor((0, 255, 0))

    # ---------------- POSITION / PHYSICS ----------------
    car_x = pixel_x - 25
    car_y = pixel_y - 14

    velocity_x = 0.0
    velocity_y = 0.0

    car_scale = 1

    acceleration = 2
    friction = 0.90
    max_speed = 9

    needs_redraw = True

    while True:
        # ---------------- INPUT ----------------
        if msvcrt.kbhit():
            key = msvcrt.getch()

            if key not in (b'\xe0', b'\x00'):
                key = key.lower()

            if key == b'\x1b':
                break

            elif key in (b'\xe0', b'\x00'):
                key = msvcrt.getch()

                if key == b'H':
                    car.direction = (car.direction - 1) % 8

                elif key == b'P':
                    car.direction = (car.direction + 1) % 8

            elif key == b'w':
                if car.direction == 0:
                    velocity_y -= acceleration
                elif car.direction == 1:
                    velocity_y -= acceleration * 0.707
                    velocity_x += acceleration * 0.707
                elif car.direction == 2:
                    velocity_x += acceleration
                elif car.direction == 3:
                    velocity_y += acceleration * 0.707
                    velocity_x += acceleration * 0.707
                elif car.direction == 4:
                    velocity_y += acceleration
                elif car.direction == 5:
                    velocity_y += acceleration * 0.707
                    velocity_x -= acceleration * 0.707
                elif car.direction == 6:
                    velocity_x -= acceleration
                elif car.direction == 7:
                    velocity_y -= acceleration * 0.707
                    velocity_x -= acceleration * 0.707

            elif key == b's':
                if car.direction == 0:
                    velocity_y += acceleration
                elif car.direction == 1:
                    velocity_y += acceleration * 0.707
                    velocity_x -= acceleration * 0.707
                elif car.direction == 2:
                    velocity_x -= acceleration
                elif car.direction == 3:
                    velocity_y -= acceleration * 0.707
                    velocity_x -= acceleration * 0.707
                elif car.direction == 4:
                    velocity_y -= acceleration
                elif car.direction == 5:
                    velocity_y -= acceleration * 0.707
                    velocity_x += acceleration * 0.707
                elif car.direction == 6:
                    velocity_x += acceleration
                elif car.direction == 7:
                    velocity_y += acceleration * 0.707
                    velocity_x += acceleration * 0.707

            elif key == b'a':
                car.direction = (car.direction - 1) % 8
                car.setDirection(car.direction)
                needs_redraw = True

            elif key == b'd':
                car.direction = (car.direction + 1) % 8
                car.setDirection(car.direction)
                needs_redraw = True

        # ---------------- PHYSICS ----------------
        velocity_x *= friction
        velocity_y *= friction

        speed = (velocity_x**2 + velocity_y**2) ** 0.5
        if speed > max_speed:
            velocity_x = (velocity_x / speed) * max_speed
            velocity_y = (velocity_y / speed) * max_speed

        if abs(velocity_x) < 0.01:
            velocity_x = 0
        if abs(velocity_y) < 0.01:
            velocity_y = 0

        car_x += velocity_x
        car_y += velocity_y

        if velocity_x != 0 or velocity_y != 0:
            needs_redraw = True

        # ---------------- CAMERA ----------------
        cam_x = int(car_x-75)
        cam_y = int(car_y-40)

        if car_x < -15:
            car_x = -15
        if car_x > bg_width-34:
            car_x = bg_width-34
        if car_y < -3:
            car_y = -3
        if car_y > bg_height-22:
            car_y = bg_height-22

        # max_cam_x = bg_width - VIEW_W 
        # max_cam_y = (len(bg_pixels) // bg_width) - VIEW_H

        # cam_x = max(-20, min(cam_x, max_cam_x))
        # cam_y = max(-20, min(cam_y, max_cam_y))

        # crop world to camera view
        view_pixels, _, _ = crop(
            bg_pixels,
            bg_width,
            cam_x,
            cam_y,
            VIEW_W,
            VIEW_H
        )

        # ---------------- DRAW CAR ----------------
        if needs_redraw:
            car_layer = car.returnCar()
            car_width = car.width

            if car_scale != 1.0:
                car_layer, car_width, _ = scale(car_layer, car.width, car_scale, car_scale)

            canvas = [[255, 255, 255, "██"] for _ in range(VIEW_W * VIEW_H)]

            car_len = len(car_layer)
            car_h = car_len // car_width

            for i in range(car_len):
                x = i % car_width
                y = i // car_width

                world_x = int(car_x) + x
                world_y = int(car_y) + y

                screen_x = world_x - cam_x
                screen_y = world_y - cam_y

                if 0 <= screen_x < VIEW_W and 0 <= screen_y < VIEW_H:
                    idx = screen_y * VIEW_W + screen_x
                    canvas[idx] = car_layer[i]

            combined = overlay_layers(view_pixels, canvas)

            clear_call()
            draw_call(combined, VIEW_W)

            needs_redraw = False

        time.sleep(0.01)
# Run intro
bg_pixels, bg_width, bg_height = intro()


# load menu assets
menu, mwid, _ = bmptoarray(f".\\assets\\menu.bmp")
menu, _, _ = scale2(menu,mwid,2,2)
play_option, _, _ = bmptoarray(f".\\assets\\playoption.bmp")
play_option, _, _ = scale2(play_option,mwid,2,2)

play_option2, _, _ = bmptoarray(f".\\assets\\playoption2.bmp")
play_option2, _, _ = scale2(play_option2,mwid,2,2)

quit_option, _, _ = bmptoarray(f".\\assets\\quitoption.bmp")
quit_option, mwid, _ = scale2(quit_option,mwid,2,2)



# start menu
clear_call()
draw_call(menu, mwid)

# menu state variables
currrent_button = 0
current_screen = menu
animating = False
frame = 0
last_frame_time = 0
frame_delay = 0.1 
needs_redraw = False


# main menu loop
while True:
    # check for keyboard input
    if msvcrt.kbhit():
        key = msvcrt.getch().lower()
        animating = False  # stop animation immediately
        
        # ESC key deselect button
        if key == b'\x1b':
            currrent_button = 0
            current_screen = menu
            needs_redraw = True
            
        # Enter key select current button
        elif key == b'\r':
            if currrent_button == 1:
                clear_call()
                break  # Exit to quit
            elif currrent_button == 2:
                thread = threading.Thread(target=play_sound)
                thread.start()
                play(bg_pixels, bg_width)
                winsound.PlaySound(None, winsound.SND_PURGE) 

                # Return to menu after play
                current_screen = menu
                currrent_button = 0
                needs_redraw = True
                
        # arrow keys or WASD
        elif key in (b'\xe0', b'\x00'):
            key = msvcrt.getch().lower()
            
            # left arrow
            if key == b'K':
                currrent_button = 1
                current_screen = quit_option
                needs_redraw = True
                
            # right arrow
            elif key == b'M':
                currrent_button = 2
                animating = True
                frame = 0
                last_frame_time = time.time()
                current_screen = play_option
                needs_redraw = True
        
        # 'a' key left
        elif key == b'a':
            currrent_button = 1
            current_screen = quit_option
            needs_redraw = True
        
        # 'd' key right
        elif key == b'd':
            currrent_button = 2
            animating = True
            frame = 0
            last_frame_time = time.time()
            current_screen = play_option
            needs_redraw = True

    # do animation
    if animating:
        current = time.time()
        
        if current - last_frame_time >= frame_delay:
            last_frame_time = current
            
            # change between two frames
            if frame % 2 == 0:
                current_screen = play_option
            else:
                current_screen = play_option2
            
            frame += 1
            needs_redraw = True
            
            # stop animation after 1000 frames
            if frame >= 1000:
                animating = False
                current_screen = play_option2

    if needs_redraw:
        clear_call()
        draw_call(current_screen, mwid)
        needs_redraw = False
    
    time.sleep(0.01)