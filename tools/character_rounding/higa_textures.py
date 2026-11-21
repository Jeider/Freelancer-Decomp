"""Author Freelancer-style diffuse maps for the Higa costume. No game writes."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'out/character_rounding/higa/step_01/textures'
SRC = Path(__file__).resolve().parents[2] / 'out/character_rounding/higa/textures'
OUT.mkdir(parents=True, exist_ok=True)


def save(name, image):
    path = OUT / name
    image.convert('RGB').save(path)
    return path


def recolor(source, tint, contrast=1.15):
    image = Image.open(source).convert('RGB')
    lum = np.asarray(ImageEnhance.Contrast(image).enhance(contrast).convert('L'), dtype=np.float32) / 255
    tint = np.array(tint, dtype=np.float32)
    colored = np.clip(lum[..., None] * tint * 1.35, 0, 255).astype(np.uint8)
    return Image.fromarray(colored, 'RGB')


def main():
    head = Image.open(SRC / '2253559819cfe383.png').convert('RGB')
    w, h = head.size
    neck = head.crop((int(w * .38), int(h * .72), int(w * .62), int(h * .96)))
    neck = ImageEnhance.Color(neck).enhance(1.15)
    arr = np.asarray(neck).astype(np.float32)
    arr *= np.array([1.08, .94, .78])
    save('higa_skin.png', Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((512, 512), Image.Resampling.LANCZOS))
    cloth = SRC / 'e64e46e7cc1f3faf.png'
    save('higa_black.png', recolor(cloth, (42, 38, 34)))
    save('higa_red.png', recolor(cloth, (148, 28, 24)))
    save('higa_gold.png', recolor(cloth, (186, 142, 48), 1.05).filter(ImageFilter.SMOOTH))
    save('higa_silver.png', recolor(cloth, (168, 172, 176), 1.25))
    save('higa_boot.png', recolor(SRC / 'eb1b23cf4ba7a6f5.png', (28, 30, 34), 1.3))
    print('textures', OUT)


if __name__ == '__main__':
    main()
