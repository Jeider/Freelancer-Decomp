"""Bake original, seamless crystal fractures/frost data (not a colour texture).

RGB holds independent layers at different depths. A holds an uneven frost field.
No third-party artwork or dependencies; deterministic DDS with a full mip chain.
"""
from pathlib import Path
import math
import struct

SIZE = 512
ROOT = Path(__file__).resolve().parents[1]


def hash01(x, y, seed):
    v = ((x * 0x1f123bb5) ^ (y * 0x05491333) ^ (seed * 0x45d9f3b)) & 0xffffffff
    v ^= v >> 16
    v = (v * 0x45d9f3b) & 0xffffffff
    v ^= v >> 16
    return (v & 0xffffff) / 16777215.0


def fracture_layer(cells, seed):
    points = {(x, y): (hash01(x, y, seed), hash01(x, y, seed + 17))
              for y in range(cells) for x in range(cells)}
    out = bytearray(SIZE * SIZE)
    for y in range(SIZE):
        py = y * cells / SIZE
        iy = math.floor(py)
        for x in range(SIZE):
            px = x * cells / SIZE
            ix = math.floor(px)
            first = second = 1.e9
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    cx, cy = ix + dx, iy + dy
                    ox, oy = points[cx % cells, cy % cells]
                    d = (px - cx - ox) ** 2 + (py - cy - oy) ** 2
                    if d < first:
                        first, second = d, first
                    elif d < second:
                        second = d
            edge = math.sqrt(second) - math.sqrt(first)
            # Thin sharp fissure plus a wider frozen halo. Mipmaps suppress sparkle.
            strength = math.exp(-edge * 55) * .72 + math.exp(-edge * 13) * .28
            out[y * SIZE + x] = round(255 * strength)
    return out


def smooth_noise(x, y, cells, seed):
    px, py = x * cells / SIZE, y * cells / SIZE
    ix, iy = math.floor(px), math.floor(py)
    fx, fy = px - ix, py - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = hash01(ix % cells, iy % cells, seed)
    b = hash01((ix + 1) % cells, iy % cells, seed)
    c = hash01(ix % cells, (iy + 1) % cells, seed)
    d = hash01((ix + 1) % cells, (iy + 1) % cells, seed)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def generate(path):
    layers = [fracture_layer(11, 7), fracture_layer(17, 37), fracture_layer(23, 83)]
    pixels = bytearray(SIZE * SIZE * 4)
    for y in range(SIZE):
        for x in range(SIZE):
            i = y * SIZE + x
            frost = smooth_noise(x, y, 5, 121) * .70 + smooth_noise(x, y, 37, 99) * .30
            pixels[i*4:i*4+4] = bytes((layers[2][i], layers[1][i], layers[0][i], round(frost * 255)))
    levels = [pixels]
    size = SIZE
    while size > 1:
        nxt = bytearray(size * size)
        half = size // 2
        for y in range(half):
            for x in range(half):
                for channel in range(4):
                    nxt[(y*half+x)*4+channel] = round(sum(pixels[((y*2+dy)*size+x*2+dx)*4+channel]
                        for dy in (0, 1) for dx in (0, 1)) / 4)
        pixels = nxt
        levels.append(pixels)
        size = half
    header = [124, 0x2100f, SIZE, SIZE, SIZE*4, 0, len(levels)] + [0]*11
    header += [32, 0x41, 0, 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000]
    header += [0x401008, 0, 0, 0, 0]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'DDS ' + struct.pack('<31I', *header) + b''.join(levels))
    print(f'{path}: {SIZE}x{SIZE}, {len(levels)} mips, {path.stat().st_size} bytes')


if __name__ == '__main__':
    generate(ROOT / 'DATA_EXTRA/TEXTURES/ice_layers.dds')
