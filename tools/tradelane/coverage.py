"""Calibrate the outer-tube coverage mask against the actual G noise channel."""
import numpy as np


def hash_value(x, y, z, seed):
    h = np.uint32(seed) ^ (x*np.uint32(0x9e3779b9)) ^ (y*np.uint32(0x85ebca6b)) ^ (z*np.uint32(0xc2b2ae35))
    h ^= h >> 16
    h *= np.uint32(0x7feb352d)
    h ^= h >> 15
    h *= np.uint32(0x846ca68b)
    h ^= h >> 16
    return (h >> 8).astype(np.float64)/16777215


def value(grid, seed):
    coords = np.indices((64, 64, 64), dtype=np.uint32)
    cell = coords//(64//grid)
    f = (coords % (64//grid)).astype(float)/(64//grid)
    f = f*f*f*(f*(f*6-15)+10)
    out = np.zeros((64, 64, 64))
    for x in range(2):
        for y in range(2):
            for z in range(2):
                weight = (f[0] if x else 1-f[0])*(f[1] if y else 1-f[1])*(f[2] if z else 1-f[2])
                out += weight*hash_value((cell[0]+x)%grid, (cell[1]+y)%grid, (cell[2]+z)%grid, seed)
    return out


tex = np.floor((.65*value(4, 0x1237abcd)+.35*value(8, 0x2348bcde))*255+.5)/255
p = np.random.default_rng(731).random((3, 250000))*64
cell = p.astype(int)
f = p-cell
samples = np.zeros(p.shape[1])
for x in range(2):
    for y in range(2):
        for z in range(2):
            samples += tex[(cell[0]+x)%64, (cell[1]+y)%64, (cell[2]+z)%64]*(f[0] if x else 1-f[0])*(f[1] if y else 1-f[1])*(f[2] if z else 1-f[2])
lo, hi = 0., 1.
for _ in range(32):
    mid = (lo+hi)/2
    t = np.clip((samples-(mid-.02))/.04, 0, 1)
    coverage = np.mean(t*t*(3-2*t))
    if coverage > .25:
        lo = mid
    else:
        hi = mid
print(f'Mask smoothstep({mid-.02:.6f}, {mid+.02:.6f}, G): mean coverage {coverage:.6f}')
