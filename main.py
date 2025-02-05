import tkinter as tk

from random import randint
from time import sleep
from threading import Thread

from PIL import Image, ImageTk

import os
import pygame
import pyautogui
import pydirectinput
import keyboard
import pygetwindow
import input_listener

from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

from png_creator import create_static


reset_character = True  # if you get jumpscared while in a Roblox window, it'll reset your character
mute_when_spawning = True  # temporarily mute all other apps whenever A-90 spawns (accurate !!)

mute_exceptions = [  # apps that won't get muted when a-90 spawns
    "python",  # don't remove !!
    "obs",
    "medal"
    # you can add more apps here if you need to
]

app_volumes = {}

def mute_audio():
    global app_volumes
    sessions = AudioUtilities.GetAllSessions()

    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        process = session.Process

        if process:
            app_name = process.name().lower()

            if not any(app in app_name for app in mute_exceptions):  # we will only leave our a-90 app unmuted
                if volume.GetMasterVolume() != 0.0:
                    app_volumes[app_name] = volume.GetMasterVolume()
                    volume.SetMasterVolume(0.0, None)


def restore_audio():
    global app_volumes
    sessions = AudioUtilities.GetAllSessions()

    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        process = session.Process

        if process:
            app_name = process.name()

            if app_name in app_volumes and not any(app_name in i for i in mute_exceptions):
                original_volume = app_volumes[app_name]
                volume.SetMasterVolume(original_volume, None)


pydirectinput.PAUSE = 0.01


pygame.init()
pygame.mixer.init()

screenshot = pyautogui.screenshot()
res_x, res_y = screenshot.size

scale_factor = ((res_x / 1920) + (res_y / 1080)) / 2

idle_sprite = Image.open("Sprites/A-90_IDLE.png")
block_sprite = Image.open("Sprites/A-90_BLOCK.png")
active_sprite = Image.open("Sprites/A-90_ACTIVE.png")
jumpscare_sprite = Image.open("Sprites/A-90_JUMPSCARE.png")
jumpscare_active_sprite = Image.open("Sprites/A-90_JUMPSCARE_ACTIVE.png")

static = tk.Tk()
static.geometry(f"{res_x}x{res_y}")
static.geometry("+0+0")
static.resizable(False, False)
static.attributes("-topmost", True)
static.attributes("-fullscreen", True)
static.attributes("-disabled", True)
static.configure(bg="black")
static.overrideredirect(True)
static["cursor"] = "none"

static.deiconify()

colors1 = [  # colors that will be used in dark static generation
    (25, 0, 0),
    (30, 0, 0),
    (50, 0, 0),
    (0, 0, 0)
]

colors2 = [  # colors that will be used in bright static generation
    (75, 0, 0),
    (80, 0, 0),
    (100, 0, 0),
    (125, 0, 0),
    (150, 0, 0)
]

dark_static = []
bright_static = []

static_brightness = "Dark"
static_image = None

def initialize_static():
    global static_image

    downscale = max(1, round(5 * scale_factor))

    for i in range(1, 11):
        if not os.path.exists(f"Static/Dark/static{i}.png"):
            print(f"Generating dark static{i}")
            create_static(f"Static/Dark/static{i}", downscale, colors1)
        else:
            with Image.open(f"Static/Dark/static{i}.png") as img:
                x, y = img.size

                if x != res_x or y != res_y:
                    print(f"Generating dark static{i}")

                    create_static(f"Static/Dark/static{i}", downscale, colors1)

        image = Image.open(f'Static/Dark/static{i}.png')
        sprite = ImageTk.PhotoImage(image)
        dark_static.append(sprite)

    for i in range(1, 11):
        if not os.path.exists(f"Static/Bright/static{i}.png"):
            print(f"Generating bright static{i}")
            create_static(f"Static/Bright/static{i}", downscale, colors2)
        else:
            with Image.open(f"Static/Bright/static{i}.png") as img:
                x, y = img.size

                if x != res_x or y != res_y:
                    print(f"Generating bright static{i}")

                    create_static(f"Static/Bright/static{i}", downscale, colors2)

        image = Image.open(f'Static/Bright/static{i}.png')
        sprite = ImageTk.PhotoImage(image)
        bright_static.append(sprite)

    static_image = tk.Label(static, width=res_x, height=res_y, image=dark_static[0])
    static_image.pack()
    static.withdraw()

    def update_static():
        index = 0

        while True:
            try:
                if static_brightness == "Dark":
                    random_static = dark_static[index]
                elif static_brightness == "Bright":
                    random_static = bright_static[index]
                else:
                    random_static = ""

                static_image.configure(image=random_static)

                index = (index + 1) % len(dark_static)

                sleep(0.025)
            except KeyboardInterrupt:
                app_exit()

    thread = Thread(target=update_static, daemon=True)
    thread.start()


static.after(0, initialize_static)

warning = pygame.mixer.Sound("Audio/warning.mp3")
warning.set_volume(0.5)

jumpscare = pygame.mixer.Sound("Audio/jumpscare.ogg")
jumpscare.set_volume(0.5)  # feel free to adjust the volume


def spawn_a90():
    idle_width = int(res_x * 0.1042)
    idle_height = int(res_y * 0.1852)

    jumpscare_width = int(res_x * 0.3646)
    jumpscare_height = int(res_y * 0.6481)

    center_x = (res_x - idle_width) // 2
    center_y = (res_y - idle_height) // 2

    random_x = randint(0, res_x - 240)
    random_y = randint(0, res_y - 240)

    def create_a90():
        global static_image
        global static_brightness

        if mute_when_spawning:
            mute_audio()

        a_90 = tk.Toplevel(static)
        a_90.geometry(f"{idle_width}x{idle_height}+{random_x}+{random_y}")
        a_90.resizable(False, False)
        a_90.wm_attributes("-topmost", True)
        a_90.overrideredirect(True)
        a_90.configure()
        a_90.wm_attributes("-transparentcolor", a_90['bg'])

        idle_photo = ImageTk.PhotoImage(
            idle_sprite.resize((idle_width, idle_height), Image.NEAREST)
        )
        block_photo = ImageTk.PhotoImage(
            block_sprite.resize((idle_width, idle_height), Image.NEAREST)
        )
        active_photo = ImageTk.PhotoImage(
            active_sprite.resize((idle_width, idle_height), Image.NEAREST)
        )
        jumpscare_photo = ImageTk.PhotoImage(
            jumpscare_sprite.resize((jumpscare_width, jumpscare_height), Image.NEAREST)
        )
        active_jumpscare_photo = ImageTk.PhotoImage(
            jumpscare_active_sprite.resize((jumpscare_width, jumpscare_height), Image.NEAREST)
        )

        idle = tk.Label(a_90, bg=a_90['bg'], image=idle_photo, borderwidth=0, highlightthickness=0)
        idle.image = idle_photo
        idle.pack(fill=tk.BOTH, expand=True)

        a_90.update()
        warning.play()

        static_brightness = "Dark"


        def move_to_center():
            a_90.geometry(f"{idle_width}x{idle_height}+{center_x}+{center_y}")
            static.deiconify()
            a_90.update()
            a_90.lift()

            input_listener.start_mouse_listen()

            static.after(25, show_block)


        def show_block():
            idle.configure(image=block_photo)
            idle.image = block_photo
            a_90.update()

            static.after(470, show_idle)


        def show_idle():
            idle.configure(image=idle_photo)
            idle.image = idle_photo
            a_90.update()

            static.after(160, show_active)


        def show_active():
            global static_brightness

            static_brightness = "Bright"
            idle.configure(image=active_photo)
            idle.image = active_photo
            static_image.configure(image=bright_static[0])
            a_90.update()

            static.after(75, check_conditions)


        def show_jumpscare():
            idle.configure(image=jumpscare_photo)
            idle.image = jumpscare_photo
            static_image.configure(image=bright_static[0])
            a_90.update()


        def show_jumpscare_a():
            idle.configure(image=active_jumpscare_photo)
            idle.image = active_jumpscare_photo
            static_image.configure(image=bright_static[0])
            a_90.update()


        def shake_window():
            shake_x = int(randint(-2, 2) * scale_factor)
            shake_y = int(randint(-2, 2) * scale_factor)

            center_x = (res_x - jumpscare_width) // 2
            center_y = (res_y - jumpscare_height) // 2

            a_90.geometry(f"+{center_x + shake_x}+{center_y + shake_y}")
            a_90.update()


        def jumpscare_shake():
            for i in range(50):
                static.after(20 * i, shake_window)


        def flash():
            global static_brightness

            static_brightness = ""
            static.lift()

            static_image.config(image="")
            static_image.image = None

            for i in range(2):
                if i % 2 == 0:
                    static.after(100 * i, lambda: static_image.configure(bg="white"))
                else:
                    static.after(100 * i, lambda: static_image.configure(bg="red"))

                    if reset_character:
                        current_window = pygetwindow.getActiveWindow()
                        if current_window and current_window.title == "Roblox":
                            pydirectinput.press("esc")
                            pydirectinput.press("r")
                            pydirectinput.press("enter")


        def play_jumpscare():
            jumpscare.play()

            a_90.geometry(f"{jumpscare_width}x{jumpscare_height}")
            a_90.update_idletasks()

            static.after(0, jumpscare_shake)

            for i in range(10):
                if i % 2 == 0:
                    static.after(100 * i, show_jumpscare)
                else:
                    static.after(100 * i, show_jumpscare_a)

            static.after(1200, destroy_a90)
            static.after(1000, flash)


        def check_conditions():
            mouse_delta = input_listener.get_mouse_listen_results()
            keys_pressed = input_listener.is_any_key_pressed()

            do_jumpscare = False

            if keys_pressed:
                do_jumpscare = True

                print(f"keys were held!! {keys_pressed}")
            elif mouse_delta[0] > 70 or mouse_delta[0] < -70 or mouse_delta[1] > 70 or mouse_delta[1] < -70:
                do_jumpscare = True

                print(f"mouse moved too much!! {mouse_delta}")
            if do_jumpscare:
                static.after(0, play_jumpscare)

                return

            static.after(0, destroy_a90)


        def destroy_a90():
            static.withdraw()
            a_90.destroy()

            if mute_when_spawning:
                restore_audio()

        static.after(500, move_to_center)

    static.after(0, create_a90)


def app_exit():
    pygame.quit()

    static.quit()

    print("Terminated")

def key_functions(key):
    if key.name == "right alt":
        static.after(0, spawn_a90)
    elif key.name == "f4":
        app_exit()


keyboard.on_press(key_functions)


def random_spawn():
    random_time = randint(30000, 120000)  # 30 - 120s

    print(f"A-90 Spawning in: {random_time / 1000}s")

    static.after(random_time, lambda: random_spawn())
    static.after(random_time, spawn_a90)

static.after(0, random_spawn)

try:
    static.mainloop()
except KeyboardInterrupt:
    app_exit()
