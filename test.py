import tkinter as tk

root = tk.Tk()
root.geometry("300x200")

keys = set()

def press(e):
    keys.add(e.keysym.lower())

def release(e):
    keys.discard(e.keysym.lower())

root.bind("<KeyPress>", press)
root.bind("<KeyRelease>", release)
root.focus_set()

x, y = 100, 100

canvas = tk.Canvas(root, width=300, height=200, bg="black")
canvas.pack()

player = canvas.create_rectangle(x, y, x+20, y+20, fill="white")

def loop():
    global x, y

    speed = 3

    if "w" in keys:
        y -= speed
    if "s" in keys:
        y += speed
    if "a" in keys:
        x -= speed
    if "d" in keys:
        x += speed

    canvas.coords(player, x, y, x+20, y+20)

    root.after(16, loop)  # ~60 FPS

loop()
root.mainloop()