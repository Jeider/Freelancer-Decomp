"""Derive a conservative normal map from ku_tgk's original diffuse and stage its MAT.

Requires numpy and Pillow. Never modifies game files. The diffuse contains baked
light: this is a band-limited relief estimate, not recovered physical geometry.
"""
import argparse
import hashlib
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_station_lods as utf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/asteroid_normals'
MAT = 'DATA/SOLAR/ASTEROIDS_MOD/KU_TGK/ast_ku_tgk.mat'
NORMAL = 'ku_tgk_rock_normal.tga'


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.children)


def leaf_map(nodes, parent=''):
    result = {}
    for n in nodes:
        path = parent + '/' + n.name
        if n.blob is not None:
            result[path] = n.blob
        result.update(leaf_map(n.children, path))
    return result


def normal_dds(normal):
    """Uncompressed BGRA8: portable D3D9 format, linear data, renormalized mips."""
    h, w, _ = normal.shape
    levels = []
    while True:
        normal = normal / np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-8)
        assert np.isfinite(normal).all() and normal[:, :, 2].min() > 0
        rgb = np.rint((normal * .5 + .5) * 255).clip(0, 255).astype(np.uint8)
        rgba = np.concatenate((rgb[:, :, ::-1], np.full((*rgb.shape[:2], 1), 255, np.uint8)), axis=2)
        levels.append(rgba.tobytes())
        if normal.shape[0] == 1:
            break
        normal = normal.reshape(normal.shape[0]//2, 2, normal.shape[1]//2, 2, 3).mean(axis=(1, 3))
    header = [124, 0x2100F, h, w, w*4, 0, len(levels)] + [0]*11
    header += [32, 0x41, 0, 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000]
    header += [0x401008, 0, 0, 0, 0]
    assert len(header) == 31
    return b'DDS ' + struct.pack('<31I', *header) + b''.join(levels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    args = parser.parse_args()
    source = (args.game_root / MAT).read_bytes()
    header, tree = utf.read_tree(source)
    textures = next(n for n in walk(tree) if n.name.lower() == 'texture library')
    diffuse = utf.child(utf.child(textures, 'rock3c.tga'), 'MIPS').blob
    image = Image.open(io.BytesIO(diffuse)).convert('RGB').resize((1024, 1024), Image.Resampling.LANCZOS)
    rgb = np.asarray(image, dtype=np.float32) / 255
    luminance = rgb @ np.array([.2126, .7152, .0722], np.float32)
    height = np.log1p(luminance * 4)
    # Periodic Gaussian filtering matches the authored wrapping UVs. Remove broad
    # baked illumination and DXT1 block noise before differentiating the height.
    spectrum = np.fft.rfft2(height)
    fy = np.fft.fftfreq(1024)[:, None]
    fx = np.fft.rfftfreq(1024)[None, :]
    def blur(sigma):
        return np.fft.irfft2(spectrum * np.exp(-2*np.pi*np.pi*sigma*sigma*(fx*fx+fy*fy)), s=height.shape)
    height = blur(1.2) - blur(24) + .35*(blur(3) - blur(12))
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * .5
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * .5
    slope = np.hypot(dx, dy)
    gain = .8 / max(float(np.percentile(slope, 95)), 1e-6)
    attenuation = np.minimum(1, 1.5 / np.maximum(slope * gain, 1e-8))
    normal = np.stack((-dx*gain*attenuation, -dy*gain*attenuation, np.ones_like(height)), axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    dds = normal_dds(normal)
    # Replace only our own generated entry on repeat runs; original leaf payloads
    # (all materials, texture flags, original DDS mip chains) stay byte-identical.
    before = leaf_map(tree)
    textures.children = [n for n in textures.children if n.name.lower() != NORMAL.lower()]
    node = utf.Node(NORMAL)
    node.children = [utf.Node('MIPS', dds)]
    textures.children.append(node)
    result = utf.write_tree(header, tree)
    _, parsed = utf.read_tree(result)
    after = leaf_map(parsed)
    for path, blob in before.items():
        if '/' + NORMAL + '/' not in path:
            assert after[path] == blob, f'Unexpected asset change: {path}'
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'assets' / MAT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    (OUT / 'normal.dds').write_bytes(dds)
    (OUT / 'base.dds').write_bytes(diffuse)
    Image.fromarray(np.rint((normal*.5+.5)*255).astype(np.uint8)).save(OUT / 'normal.png')
    Image.fromarray(np.rint(np.clip(height*.7+.5, 0, 1)*255).astype(np.uint8)).save(OUT / 'height.png')
    # Extract the actual three mesh triangle streams for the GPU fixture.
    for suffix in 'abc':
        path = args.game_root / f'DATA/SOLAR/ASTEROIDS_MOD/KU_TGK/ast_ktgk_nrml_{suffix}.3db'
        _, nodes = utf.read_tree(path.read_bytes())
        mesh = next(n.blob for n in walk(nodes) if n.name == 'VMeshData')
        _, _, groups, indices, fvf, vertices = struct.unpack_from('<II4H', mesh)
        assert groups == 1 and fvf == 0x112
        material, start, _, count, _ = struct.unpack_from('<I4H', mesh, 16)
        assert material == utf.crc('mat_ktgk_' + suffix)
        vertex_base = 16 + groups*12 + indices*2
        corners = [struct.unpack_from('<8f', mesh, vertex_base+(start+i)*32)
                   for i in struct.unpack_from(f'<{count}H', mesh, 16+groups*12)]
        center = [(max(v[k] for v in corners)+min(v[k] for v in corners))*.5 for k in range(3)]
        extent = max(abs(v[k]-center[k]) for v in corners for k in range(3))
        (OUT / f'mesh_{suffix}.bin').write_bytes(b''.join(struct.pack('<8f',
            *[(v[k]-center[k])/extent for k in range(3)], *v[3:]) for v in corners))
    report = dict(source_sha256=hashlib.sha256(source).hexdigest(),
                  diffuse_sha256=hashlib.sha256(diffuse).hexdigest(),
                  normal_sha256=hashlib.sha256(dds).hexdigest(),
                  resolution=1024, mip_levels=11, format='A8R8G8B8, linear RGB normals',
                  normal_bytes=len(dds), preserved_leaves=len(before),
                  mean_z=float(normal[:, :, 2].mean()), strength=.65,
                  material_binding=['mat_ktgk_a', 'mat_ktgk_b', 'mat_ktgk_c'])
    (OUT / 'generation.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
