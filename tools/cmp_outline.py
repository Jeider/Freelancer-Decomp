"""Outline a Freelancer .cmp: compound parts, their files, animation scripts (diagnostics)."""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen


def text(blob):
    return blob.split(b'\0', 1)[0].decode('ascii', 'replace') if blob else ''


def walk(node, depth, out, limit):
    if depth > limit:
        return
    size = '' if node.blob is None else f' [{len(node.blob)} bytes]'
    out.append('  ' * depth + node.name + size)
    for c in node.children:
        walk(c, depth + 1, out, limit)


data = Path(sys.argv[1]).read_bytes()
_, roots = gen.read_tree(data)
root = roots[0]
for n in root.children:
    if n.name.lower() == 'cmpnd':
        for part in n.children:
            fields = {c.name.lower(): c.blob for c in part.children if c.blob is not None}
            print('part', part.name, '->', text(fields.get('file name')), text(fields.get('object name')))
    elif n.name.lower() == 'animation':
        out = []
        walk(n, 0, out, 3)
        print('\n'.join(out))
    elif n.name.lower() == 'cmpnd' or n.name.lower().endswith('.3db'):
        pass
print('top-level:', [n.name for n in root.children][:40])
