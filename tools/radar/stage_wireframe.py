"""Opt Lair's existing wireframe models into the radar; preserve other INI bytes."""
from collections import Counter
from pathlib import Path
import json
import re
import struct
import sys

from stage_solars import sections, values, sha
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from generate_station_lods import read_tree, child, crc

GAME = Path('D:/games/FL_MOD')
OUT = ROOT/'src/obj/radar_wireframe'


def nodes(node):
    yield node
    for item in node.children:
        yield from nodes(item)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    system = GAME/'DATA/UNIVERSE/SPECIAL/LAIR/lair.ini'
    solar = GAME/'DATA/SOLAR/solararch.ini'
    original = solar.read_bytes()
    objects = Counter(values(b).get('archetype') for k, _, _, b in sections(system.read_bytes()) if k == 'object')
    selected, skipped, edits, fixtures = {}, {}, [], []
    dependencies = {str(system.relative_to(GAME)): sha(system.read_bytes())}
    for kind, start, _, block in sections(original):
        data = values(block)
        name = data.get('nickname')
        if kind != 'solar' or name not in objects:
            continue
        model = GAME/'DATA'/data['da_archetype'].replace('\\', '/')
        raw = model.read_bytes()
        dependencies[str(model.relative_to(GAME))] = sha(raw)
        tree = list(nodes(read_tree(raw)[1][0]))
        meshes = {crc(m.name): child(m, 'VMeshData').blob for n in tree
                  if n.name.lower() == 'vmeshlibrary' for m in n.children}
        wires = [n.blob for n in tree if n.name.lower() == 'vwiredata' and len(n.blob) > 16]
        if not wires:
            skipped[name] = dict(instances=objects[name], model=data['da_archetype'])
            continue
        edges = 0
        for i, wire in enumerate(wires):
            header, mesh_id, base, unique, count, maximum = struct.unpack_from('<II4H', wire)
            assert header == 16 and count % 2 == 0 and len(wire) == 16 + 2 * count
            mesh = meshes[mesh_id]
            fixture = OUT/(name+'_'+str(i)+'.wire')
            fixture.write_bytes(struct.pack('<II', len(mesh), len(wire)) + mesh + wire)
            fixtures.append(fixture.name)
            edges += count//2
        selected[name] = dict(instances=objects[name], model=data['da_archetype'], parts=len(wires), edges=edges)
        if 'radar_wireframe' in data:
            assert data['radar_wireframe'].lower() == 'true', 'Existing override: '+name
            continue
        nickname = re.search(rb'(?mi)^nickname\s*=[^\r\n]*\r?\n', block)
        newline = b'\r\n' if nickname[0].endswith(b'\r\n') else b'\n'
        edits.append((start + nickname.end(), b'radar_wireframe = true' + newline))
    assert set(selected) | set(skipped) == set(objects)
    prepared = original
    for offset, insertion in reversed(edits):
        prepared = prepared[:offset] + insertion + prepared[offset:]
    # Removing only these insertions must recover the exact source.
    recovered = prepared
    for offset, insertion in edits:
        recovered = recovered[:offset] + recovered[offset+len(insertion):]
    assert recovered == original
    (OUT/'solararch.ini').write_bytes(prepared)
    (OUT/'fixtures.txt').write_text('\n'.join(fixtures)+'\n')
    report = dict(selected=selected, skipped=skipped, original=sha(original), prepared=sha(prepared), dependencies=dependencies)
    (OUT/'stage.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'PASS: {len(selected)} Lair archetypes / {sum(v["instances"] for v in selected.values())} objects opted in; '
          f'{len(skipped)} archetypes without wires unchanged; {len(fixtures)} native wire parts staged for checks')


if __name__ == '__main__':
    main()
