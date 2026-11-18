"""Read the exported CMP and preview component-owned HUD wire contours."""
import json
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rh_pir_elite_build as b


def main():
    f = b.f
    cmp = b.ASSETS / 'rh_pir_elite.cmp'
    _, nodes = f.mesh.read_tree(cmp.read_bytes())
    transforms, _ = f.audit.transforms(nodes, ('Sc_extend wing', 0))
    libs = {f.mesh.crc(p.split('/')[-2]): f.audit.decode(n.blob)[0]
            for p, n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    wires = {}
    for file, owner in f.component_map(nodes).items():
        wire = f.mesh.child(f.mesh.child(f.mesh.child(nodes[0], file), 'VMeshWire'), 'VWireData').blob
        _, crc, bias, nv, ni, total = struct.unpack_from('<II4H', wire)
        ids = np.frombuffer(wire, '<u2', offset=16)
        rotation, offset = transforms[file.lower()]
        wires[owner] = (libs[crc][bias + ids, :3] @ rotation.T + offset).reshape(-1, 2, 3)
    scale = 2
    canvas = Image.new('RGB', (2100 * scale, 1500 * scale), '#091722')
    draw = ImageDraw.Draw(canvas)
    def label(x, y, value, size=28, color='white'):
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size * scale)
        draw.text((x * scale, y * scale), value, font=font, fill=color, anchor='mm')
    cases = [
        ('Вид сбоку — кабина, шея, корпус', (2, 1), None, None),
        ('Левое крыло выделено отдельно', (0, 2), 'Rh_port_wing_lod1', None),
        ('Средняя часть tail отделена', (2, 1), None, 'Rh_tail_lod1'),
        ('Левое крыло отделено', (0, 2), None, 'Rh_port_wing_lod1'),
    ]
    for i, (title, projection, highlight, hidden) in enumerate(cases):
        left, top = 70 + (i % 2) * 1010, 190 + (i // 2) * 600
        bounds = np.concatenate([lines[..., projection].reshape(-1, 2) for lines in wires.values() if len(lines)])
        low, high = bounds.min(0), bounds.max(0)
        center = (low + high) * .5
        pixels = min(900 / (high[0] - low[0]), 470 / (high[1] - low[1]))
        direction = np.array([1, 1 if projection == (0, 2) else -1])
        def screen(points):
            return ((points - center) * direction * pixels + [left + 450, top + 280]) * scale
        for owner, lines in wires.items():
            if not len(lines):
                continue
            projected = lines[..., projection]
            if owner == hidden:
                continue
            # Coincident front/back edges are drawn once in each orthographic view.
            unique = {tuple(sorted(tuple(np.round(p, 5)) for p in edge)): edge for edge in projected}
            color = '#ffdc36' if owner == highlight else '#78d9ed' if owner == 'Root' else '#c1edf5'
            for edge in unique.values():
                draw.line([tuple(p) for p in screen(edge)], fill=color,
                          width=(4 if owner == highlight else 2) * scale)
        label(left + 450, top, title)
    label(1050, 80, 'RH PIR ELITE • контуры из экспортированного CMP', 38)
    label(1050, 1430, 'Офлайн-проверка в раскрытой позе. В игре HUD использует текущую позу деталей.',
          24, '#9eb6c6')
    canvas.resize((2100, 1500), Image.Resampling.LANCZOS).save(b.OUT / 'wire_preview.png')
    (b.OUT / 'wire_preview.json').write_text(json.dumps({'cmp_sha256': f.digest(cmp),
        'source': 'Decoded exported VWireData; unfolded animation transforms',
        'cases': cases}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(b.OUT / 'wire_preview.png')


if __name__ == '__main__':
    main()
