# thumbnail_generator.py
from PIL import Image, ImageDraw, ImageFont
import os

def generate_thumbnail(text, output_path="thumbnail.jpg"):
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    text = text[:50]
    textwidth, textheight = draw.textsize(text, font=font)
    x = (width - textwidth) / 2
    y = (height - textheight) / 2

    draw.text((x, y), text, font=font, fill="white")
    image.save(output_path)
    return output_path

