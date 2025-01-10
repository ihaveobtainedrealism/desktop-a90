from random import choice
from PIL import Image

import png
from PIL.Image import Resampling


def create_static(name, downscale, colors):
    width = round(1920 / downscale)
    height = round(1080 / downscale)

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
    im_resized = im.resize((1920, 1080), Resampling.BOX)
    im_resized.save(f"{name}.png", "PNG")
