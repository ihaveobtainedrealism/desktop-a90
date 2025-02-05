from random import choice
from PIL import Image

from pyautogui import screenshot

import png
from PIL.Image import Resampling

screenshot = screenshot()
resolution = screenshot.size


def create_static(name, downscale, colors):
    width = round(resolution[0] / downscale)
    height = round(resolution[1] / downscale)

    img = []

    for y in range(height):
        row = ()

        for x in range(width):
            random_color = choice(colors)

            row = row + random_color

        img.append(row)

    with open(f'{name}.png', 'wb') as f:
        w = png.Writer(width, height, greyscale=False)

        try:
            w.write(f, img)
        except png.ProtocolError as error:
            print(error)
            pass

    im = Image.open(f"{name}.png")
    im_resized = im.resize((resolution[0], resolution[1]), Resampling.BOX)
    im_resized.save(f"{name}.png", "PNG")
