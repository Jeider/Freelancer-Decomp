"""Outline any Freelancer UTF file (.sph/.mat/.txm/.3db): node tree with leaf sizes and short
text/float previews (diagnostics). usage: utf_outline.py <file> [max depth]"""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen


def preview(blob):
    if not blob:
        return ''
    text = blob.split(b'\0', 1)[0]
    if text and all(32 <= c < 127 for c in text) and len(text) >= 3:
        return ' "' + text.decode()[:60] + '"'
    if len(blob) % 4 == 0 and len(blob) <= 64:
        vals = S.unpack_from('<%df' % (len(blob) // 4), blob)
        ints = S.unpack_from('<%dI' % (len(blob) // 4), blob)
        if all(abs(v) < 1e7 and (v == 0 or abs(v) > 1e-6) for v in vals):
            return ' ' + str([round(v, 4) for v in vals])
        return ' ' + str([hex(i) for i in ints])
    return ''


def walk(node, depth, limit):
    if depth > limit:
        return
    size = '' if node.blob is None else f' [{len(node.blob)}]' + preview(node.blob)
    print('  ' * depth + node.name + size)
    for c in node.children:
        walk(c, depth + 1, limit)


_, roots = gen.read_tree(Path(sys.argv[1]).read_bytes())
for r in roots:
    walk(r, 0, int(sys.argv[2]) if len(sys.argv) > 2 else 4)
