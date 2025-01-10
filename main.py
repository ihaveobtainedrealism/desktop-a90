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


app_volumes = {}

def mute_audio():
    global app_volumes
    sessions = AudioUtilities.GetAllSessions()

    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        process = session.Process

        if process:
            app_name = process.name()

            if app_name != "python.exe":  # we will only leave our a-90 app unmuted
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

            if app_name in app_volumes and app_name != "python.exe":
                original_volume = app_volumes[app_name]
                volume.SetMasterVolume(original_volume, None)


pydirectinput.PAUSE = 0.01


pygame.init()
pygame.mixer.init()

screenshot = pyautogui.screenshot()

resolution = screenshot.size

idle_sprite = Image.open("Sprites/A-90_IDLE.png")
block_sprite = Image.open("Sprites/A-90_BLOCK.png")
active_sprite = Image.open("Sprites/A-90_ACTIVE.png")
jumpscare_sprite = Image.open("Sprites/A-90_JUMPSCARE.png")
jumpscare_active_sprite = Image.open("Sprites/A-90_JUMPSCARE_ACTIVE.png")

static = tk.Tk()
static.geometry(f"{resolution[0]}x{resolution[1]}")
static.geometry("+0+0")
static.resizable(False, False)
static.attributes('-topmost', True)
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

    for i in range(1, 11):
        if not os.path.exists(f"Static/Dark/static{i}.png"):
            create_static(f"Static/Dark/static{i}", 5, colors1)
        image = Image.open(f'Static/Dark/static{i}.png')
        sprite = ImageTk.PhotoImage(image)
        dark_static.append(sprite)

    for i in range(1, 11):
        if not os.path.exists(f"Static/Bright/static{i}.png"):
            create_static(f"Static/Bright/static{i}", 5, colors2)
        image = Image.open(f'Static/Bright/static{i}.png')
        sprite = ImageTk.PhotoImage(image)
        bright_static.append(sprite)

    static_image = tk.Label(static, width=resolution[0], height=resolution[1], image=dark_static[0])
    static_image.pack()
    static.withdraw()

    def update_static():
        index = 0

        while True:
            if static_brightness == "Dark":
                random_static = dark_static[index]
            elif static_brightness == "Bright":
                random_static = bright_static[index]
            else:
                random_static = ""

            static_image.configure(image=random_static)

            index = (index + 1) % len(dark_static)

            sleep(0.025)

    thread = Thread(target=update_static, daemon=True)
    thread.start()


static.after(0, initialize_static)

warning = pygame.mixer.Sound("Audio/warning.mp3")
warning.set_volume(0.5)

jumpscare = pygame.mixer.Sound("Audio/jumpscare.ogg")
jumpscare.set_volume(0.5)


def spawn_a90():
    random_x = randint(0, resolution[0] - 240)
    random_y = randint(0, resolution[1] - 240)

    def create_a90():
        global static_image
        global static_brightness

        mute_audio()

        a_90 = tk.Toplevel(static)
        a_90.geometry(f"200x200+{random_x}+{random_y}")
        a_90.resizable(False, False)
        a_90.wm_attributes("-topmost", True)
        a_90.overrideredirect(True)
        a_90.configure()
        a_90.wm_attributes("-transparentcolor", a_90['bg'])
        a_90["cursor"] = "none"

        idle_photo = ImageTk.PhotoImage(idle_sprite)
        block_photo = ImageTk.PhotoImage(block_sprite)
        active_photo = ImageTk.PhotoImage(active_sprite)
        jumpscare_photo = ImageTk.PhotoImage(jumpscare_sprite)
        active_jumpscare_photo = ImageTk.PhotoImage(jumpscare_active_sprite)

        idle = tk.Label(a_90, bg=a_90['bg'], image=idle_photo, borderwidth=0, highlightthickness=0)
        idle.image = idle_photo
        idle.pack(fill=tk.BOTH, expand=True)

        a_90.update()
        warning.play()

        screen_width = resolution[0]
        screen_height = resolution[1]
        window_width = 200
        window_height = 200
        center_x = (screen_width - window_width) // 2
        center_y = (screen_height - window_height) // 2

        static_brightness = "Dark"


        def move_to_center():
            a_90.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
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
            shake_x = randint(-2, 2)
            shake_y = randint(-2, 2)

            window_width = 700
            window_height = 700

            center_x = (screen_width - window_width) // 2
            center_y = (screen_height - window_height) // 2

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

                    current_window = pygetwindow.getActiveWindow()
                    if current_window and current_window.title == "Roblox":
                        # if you get jumpscared while you're in a roblox window, reset character :troll:
                        pydirectinput.press("esc")
                        pydirectinput.press("r")
                        pydirectinput.press("enter")


        def play_jumpscare():
            jumpscare.play()

            window_width = 700
            window_height = 700

            a_90.geometry(f"{window_width}x{window_height}")
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

            restore_audio()

        static.after(500, move_to_center)

    static.after(0, create_a90)


def key_functions(key):
    global static

    if key.name == "right alt":
        static.after(0, spawn_a90)
    elif key.name == "f4":
        os._exit(0)


keyboard.on_press(key_functions)


def random_spawn():
    random_time = randint(30000, 120000)  # 30 - 120s

    print(f"A-90 Spawning in: {random_time / 1000}s")

    static.after(random_time, lambda: random_spawn())
    static.after(random_time, spawn_a90)

static.after(0, random_spawn)

static.mainloop()
