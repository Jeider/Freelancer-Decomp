"""Bake region colors from the native Kaitlyn atlas. System Python, no Blender."""
import gzip
import json
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[2] / 'out/character_rounding/higa/step_02'
SRC = Path(__file__).resolve().parents[2] / 'out/character_rounding/higa/source/body.json.gz'
PALETTE = {
    'skin': np.array([214, 158, 124], float),
    'black': np.array([38, 34, 32], float),
    'red': np.array([156, 34, 30], float),
    'boot': np.array([24, 24, 28], float),
}


def recolor(rgb, kind):
    lum = float(np.dot(rgb, [0.30, 0.55, 0.15])) / 255
    return np.clip(PALETTE[kind] * (0.42 + 0.85 * lum), 0, 255) / 255


def main():
    body = json.loads(gzip.decompress(SRC.read_bytes()))
    c = np.array([[1.0, 0, 0], [0, 0, -1], [0, 1, 0]])
    points = np.array(body['points']) @ c.T
    normals = np.array(body['normals']) @ c.T
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-9
    faces = np.array([t for g in body['groups'] for t in g['faces']])
    images = {}
    rgb = []
    for group in body['groups']:
        if group['texture'] not in images:
            images[group['texture']] = np.asarray(Image.open(group['texture']).convert('RGB'))
        image = images[group['texture']]
        height, width = image.shape[:2]
        for face in group['faces']:
            center = points[face].mean(0)
            kind = 'boot' if center[2] < -0.17 and abs(center[0]) < 0.17 else 'skin'
            if 0.0 < center[2] < 0.13 and abs(center[0]) < 0.11 and center[1] > 0:
                kind = 'red'
            for vi in face:
                u, v = body['uv'][vi]
                rgb.append(recolor(image[int((1 - v % 1) * (height - 1)), int((u % 1) * (width - 1))], kind))
    rgb = np.array(rgb, dtype=np.float32)
    center = points[faces].mean(1)
    n = normals[faces].mean(1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    x, y, z = center[:, 0], center[:, 1], center[:, 2]
    skirt = (z > -0.30) & (z < 0.14) & (np.abs(x) > 0.09) & (np.abs(x) < 0.19) & (np.abs(y) < 0.12) & (
        (n[:, 0] * np.sign(x) > 0.25) | (n[:, 1] < -0.15))
    chest = (z > 0.30) & (z < 0.47) & (y > 0.02) & (n[:, 1] > 0.35) & (np.abs(x) < 0.11)
    for index in np.flatnonzero(skirt):
        rgb[index * 3:index * 3 + 3] = recolor(rgb[index * 3] * 255, 'black')
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / 'paint.npz', rgb=rgb, skirt=skirt, chest=chest)
    print(int(skirt.sum()), int(chest.sum()), rgb.shape)


if __name__ == '__main__':
    main()
