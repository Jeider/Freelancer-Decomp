"""Verify staged Valensia transforms, mesh sharing, collision and preserved sources."""
import ast
from collections import Counter
import json
from pathlib import Path
import re
import struct as S
import subprocess
import sys

import numpy as np
from scipy.spatial import cKDTree
import valensia_optimize as v


def templates(source):
    result = {}
    for cls in ast.parse(source).body:
        if isinstance(cls, ast.ClassDef):
            for member in cls.body:
                if isinstance(member, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TEMPLATE' for t in member.targets):
                    result[cls.name] = ast.literal_eval(member.value)
    return result


def cloud_equal(a, b, tolerance=.004):
    assert len(a) == len(b), (len(a), len(b))
    assert cKDTree(a).query(b)[0].max() < tolerance
    assert cKDTree(b).query(a)[0].max() < tolerance


def main():
    manifest = json.loads((v.OUT/'manifest.json').read_text())
    stage = v.OUT/'stage'
    for relative, digest in manifest['payload'].items():
        assert v.sha256((stage/relative).read_bytes()).hexdigest() == digest, relative
    source = templates((v.GAME/v.TEMPLATE).read_text(encoding='utf-8-sig'))
    assert (stage/v.ORIGINAL_TEMPLATE).read_bytes() == (v.GAME/v.TEMPLATE).read_bytes()
    target = templates((stage/v.TEMPLATE).read_text(encoding='utf-8-sig'))
    for name, text in source.items():
        assert target[name+'Original'] == text, name
    assert (stage/'DATA'/v.LIVE.replace('.ini', 'Original.ini')).read_bytes() == (v.GAME/'DATA'/v.LIVE).read_bytes()
    source['or_hq_live'] = (v.GAME/'DATA'/v.LIVE).read_text(encoding='utf-8-sig')
    target['or_hq_live'] = (stage/'DATA'/v.LIVE).read_text(encoding='utf-8-sig')
    arch = {v.one(v.fields(block), 'nickname'): v.fields(block) for block in v.blocks((v.GAME/'DATA/SOLAR/solararch.ini').read_text(encoding='utf-8-sig'))
            if block.lower().startswith('[solar]')}
    assets, removed_all = {}, set()
    count, hull_count, max_error = 0, 0, 0.
    for label, report in manifest['reports'].items():
        old = {p.name:p for p in v.b.placements_from_template(source[label])}
        new = {p.name:p for p in v.b.placements_from_template(target[label])}
        old_blocks = {v.one(v.fields(x), 'nickname'):x for x in v.blocks(source[label])}
        new_blocks = {v.one(v.fields(x), 'nickname'):x for x in v.blocks(target[label])}
        members = [n for g in report['components'] for n in g['members']]
        assert len(members) == len(set(members))
        untouched = set(old)-set(members)
        for nick in untouched:
            assert old_blocks[nick] == new_blocks[nick], nick
        assert [x for x in v.blocks(source[label]) if not x.startswith('[Object]')] == [x for x in v.blocks(target[label]) if not x.startswith('[Object]')]
        # The live system already has duplicate shipyard nicknames outside this station.
        assert len(v.b.placements_from_template(source[label])) == report['before']
        assert len(v.b.placements_from_template(target[label])) == report['after']
        assert Counter(x for x in v.blocks(source[label]) if v.one(v.fields(x), 'nickname') not in members) == Counter(x for x in v.blocks(target[label]) if v.one(v.fields(x), 'nickname') not in members)
        removed_all.update(set(old)-set(new))
        for group in report['components']:
            nick = group['archetype']
            first = old[group['members'][0]]
            assert new[first.name].archetype == nick
            rotation = v.euler_matrix(*first.rotate)
            source_arch = first.archetype
            if source_arch not in assets:
                assets[source_arch] = v.load_asset(v.GAME/'DATA', arch[source_arch])
            _, visual, hulls, _, _ = assets[source_arch]
            root = v.b.load_model(stage/f'DATA/SOLAR/OPTIMIZED/valensia_opt/{nick}.cmp')[1]
            assert {k:v.b.one(n, 'VMeshData').blob for k,n in v.b.library_meshes(root).items()} == {k:v.b.one(n, 'VMeshData').blob for k,n in v.b.library_meshes(visual).items()}
            joint = v.b.one(root, 'Fix').blob
            loaded = {ident: v.leaves(dict(chunks)[b'surf']) for ident, chunks in v.parts((stage/f'DATA/SOLAR/OPTIMIZED/valensia_opt/{nick}.sur').read_bytes())}
            aggregate = loaded[v.utf.crc('Root')]
            assert len(aggregate) == group['hulls']
            assert sorted(np.array(group['bounds'][1])-group['bounds'][0])[1]/2 <= 150.001
            assert max(np.array(group['bounds'][1])-group['bounds'][0]) <= 600.001
            for i, name in enumerate(group['members']):
                item = old[name]
                partname = 'Root' if i == 0 else f'part{i:02d}'
                matrix = np.eye(3) if i == 0 else np.array(S.unpack_from('<9f', joint, 176*(i-1)+140)).reshape(3,3)
                offset = np.zeros(3) if i == 0 else np.array(S.unpack_from('<3f', joint, 176*(i-1)+128))
                original_points = np.concatenate([h.points for h in hulls])
                expected = original_points @ v.euler_matrix(*item.rotate).T+item.pos
                actual = (original_points @ matrix.T+offset) @ rotation.T+first.pos
                max_error = max(max_error, float(np.abs(actual-expected).max()))
                assert np.allclose(actual, expected, rtol=0, atol=.004), name
                placed_hulls = [h for h in aggregate if h.hull_id == v.utf.crc(partname)]
                assert len(placed_hulls) == len(hulls)
                # Face adjacency/opposite-face bytes remain unchanged, including two-sided triangles.
                assert Counter(h.raw[16:] for h in placed_hulls) == Counter(h.raw[16:] for h in hulls)
                cloud_equal(np.concatenate([h.points for h in placed_hulls]), original_points @ matrix.T+offset)
                if i:
                    local = loaded[v.utf.crc(partname)]
                    cloud_equal(np.concatenate([h.points for h in local]), original_points)
                node = v.b.one(root, f'{nick}_{i:02d}.3db')
                for child in visual.children:
                    if child.name.lower() in ('vmeshlibrary', 'exporter version'): continue
                    def signature(n): return n.name, n.blob, [signature(c) for c in n.children]
                    assert signature(v.b.one(node, child.name)) == signature(child)
                hull_count += len(hulls)
            count += 1
    # Check references outside object definitions (missions, parent links, scripts).
    pattern = v.OUT/'removed_nicknames.txt'
    pattern.write_text('\n'.join(sorted(removed_all)), encoding='utf-8')
    scan = subprocess.run(['rg', '-n', '-i', '-F', '-f', str(pattern), str(v.GAME/'DATA'),
                           str(v.GAME/'Assets/Pythonlancer'), '-g', '*.ini', '-g', '*.py'], capture_output=True)
    assert scan.returncode in (0, 1), scan.stderr.decode(errors='replace')
    unexpected = [line for line in scan.stdout.decode(errors='replace').splitlines()
                  if not re.search(r':\d+:\s*nickname\s*=', line, re.I)]
    assert not unexpected, '\n'.join(unexpected[:30])
    result = dict(manifest_sha256=v.sha256((v.OUT/'manifest.json').read_bytes()).hexdigest(),
                  components=count, preserved_hulls=hull_count, maximum_transform_error=max_error,
                  originals_preserved=True, untouched_objects_identical=True, external_references_checked=True)
    (v.OUT/'checks.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__': main()
