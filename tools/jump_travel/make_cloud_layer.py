"""Bake a seamless modulation layer; generated once, not during rendering."""
from pathlib import Path
import numpy as np
from PIL import Image

def generate(destination):
    size = 512
    rng = np.random.default_rng(20261115)
    result = np.zeros((size, size), dtype=np.float32)
    for columns, rows, weight in [(16, 8, .56), (32, 16, .27), (64, 32, .12), (128, 64, .05)]:
        grid = rng.random((rows, columns), dtype=np.float32)
        y, x = np.mgrid[:size, :size].astype(np.float32)
        x *= columns / size
        y *= rows / size
        ix, iy = x.astype(int), y.astype(int)
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = grid[iy, ix] * (1 - fx) + grid[iy, (ix + 1) % columns] * fx
        b = grid[(iy + 1) % rows, ix] * (1 - fx) + grid[(iy + 1) % rows, (ix + 1) % columns] * fx
        result += weight * (a * (1 - fy) + b * fy)
    values = (np.clip((result - .5) * 1.6 + .5, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(values).convert('RGB').save(destination)

if __name__ == '__main__':
    path = Path(__file__).resolve().parents[2] / 'out/jump_travel/cloud_reference/cloud_modulation.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    generate(path)
