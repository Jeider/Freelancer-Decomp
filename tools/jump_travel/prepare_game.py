"""Bake workspace DATA_EXTRA assets for the approved jump-cloud renderer."""
from pathlib import Path
import struct
import re
import numpy as np
from make_cloud_layer import generate

root = Path(__file__).resolve().parents[2]
assets = root / 'DATA_EXTRA/FX/JUMP_CLOUD'
assets.mkdir(parents=True, exist_ok=True)
generate(assets / 'modulation.png')
path_source = (root / 'src/freelancer/Client/jump_cloud_path.h').read_text()
def parameter(name):
    return float(re.search(r'constexpr float ' + name + r'=([\d.]+)f;', path_source)[1])
z = np.arange(8192, dtype=np.float64) * 2 - 128
s = z / parameter('PathSegment')
n, u = np.floor(s), s - np.floor(s)
points = np.zeros((8192, 4), dtype='<f2')
for channel, amplitude, frequency, phase in [(0, parameter('PathWidth'), 1.1, 0), (1, parameter('PathHeight'), .83, .5)]:
    a, b, c, d = [amplitude * np.sin((n + i) * frequency + phase) for i in (-1, 0, 1, 2)]
    points[:, channel] = .5 * (2*b + (-a+c)*u + (2*a-5*b+4*c-d)*u*u + (-a+3*b-3*c+d)*u*u*u)
points[:, 3] = 1
header = [124, 0x100F, 1, 8192, 8192*8, 0, 1] + [0]*11
header += [32, 4, 113, 0, 0, 0, 0, 0]  # D3DFMT_A16B16G16R16F
header += [0x1000, 0, 0, 0, 0]
assert len(header) == 31
(assets / 'path.dds').write_bytes(b'DDS ' + struct.pack('<31I', *header) + points.tobytes())
print('Prepared modulation.png and path.dds in workspace DATA_EXTRA')
