"""Remove generated LODs: restore original models, keeping repaired near-mesh data."""
import hashlib
import json
import struct as S
from pathlib import Path
from generate_station_lods import read_tree, write_tree, child, crc
from generate_industrial_lods import geometry
from repair_panel_normals import leaves
from rebuild_uv_safe_lods import uv_signature

DATA = Path('D:/games/FL_MOD/DATA')
OUT = Path('bin/lods_removed')
TRADE = 'SOLAR/MISC/space_trade_station_part.3db'
TRADE_BACKUP = DATA / 'SOLAR/MISC/.before_trade_station_lods_20261022_110538/space_trade_station_part.3db'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def model_list():
    items = []
    for folder in ('industrial_lods', 'component_lods'):
        bundle = Path('bin') / folder
        m = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8-sig'))
        receipt = json.loads((bundle / 'installation.json').read_text(encoding='utf-8-sig'))
        for r in m['models']:
            items.append((r['file'], Path(receipt['Backup']) / r['file']))
    items.append((TRADE, TRADE_BACKUP))
    return items


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.children)


def process(file, backup):
    cur_bytes = (DATA / file).read_bytes()
    org_bytes = backup.read_bytes()
    _, croots = read_tree(cur_bytes)
    oheader, oroots = read_tree(org_bytes)
    croot, oroot = croots[0], oroots[0]

    ref = child(child(child(child(croot, 'MultiLevel'), 'Level0'), 'VMeshPart'), 'VMeshRef').blob
    key = S.unpack_from('<I', ref, 4)[0]
    cmesh = next(n for n in child(croot, 'VMeshLibrary').children if crc(n.name) == key)
    omesh = next(n for n in child(oroot, 'VMeshLibrary').children if n.name == cmesh.name)
    assert crc(omesh.name) == key
    cdata, odata = child(cmesh, 'VMeshData'), child(omesh, 'VMeshData')
    assert uv_signature(geometry(odata.blob)) == uv_signature(geometry(cdata.blob)), file

    changed = odata.blob != cdata.blob
    odata.blob = cdata.blob
    cref = child(cmesh, 'VMeshRef') if any(c.name == 'VMeshRef' for c in cmesh.children) else None
    # counts from current VMeshRef(s) that reference this mesh
    curcounts = None
    for n in walk(croots):
        if n.name == 'VMeshRef' and n.blob and len(n.blob) >= 20 and S.unpack_from('<I', n.blob, 4)[0] == key:
            curcounts = S.unpack_from('<6H', n.blob, 8)
            break
    diff = False
    for n in walk(oroots):
        if n.name == 'VMeshRef' and n.blob and len(n.blob) >= 20 and S.unpack_from('<I', n.blob, 4)[0] == key:
            old = S.unpack_from('<6H', n.blob, 8)
            if curcounts and old != curcounts:
                diff = True
                print('  COUNT DIFF', file, old, '->', curcounts)
                b = bytearray(n.blob)
                S.pack_into('<6H', b, 8, *curcounts)
                n.blob = bytes(b)
    out = write_tree(oheader, oroots)

    ol = dict((p, b) for p, _, b in leaves(org_bytes)[1])
    nl = dict((p, b) for p, _, b in leaves(out)[1])
    assert list(ol) == list(nl), file
    meshpath = None
    for p in ol:
        if ol[p] != nl[p]:
            leaf = p.rsplit('/', 1)[-1]
            if leaf == 'VMeshData':
                assert p.split('/')[-2] == cmesh.name, (file, p)
            else:
                assert leaf == 'VMeshRef' and diff, (file, p)
    assert b'_auto.lod' not in out
    assert all('_auto.lod' not in p for p in nl)

    dest = OUT / file
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(out)
    row = dict(file=file, original_sha256=sha(org_bytes), current_sha256=sha(cur_bytes),
               output_sha256=sha(out), near_mesh=cmesh.name, near_data_changed=changed,
               count_diff=diff)
    print(f'{file}: near={cmesh.name} near_changed={changed} count_diff={diff} out={sha(out)[:12]}')
    return row


def main():
    items = model_list()
    assert len(items) == 30, len(items)
    assert len({f for f, _ in items}) == 30
    rows = [process(f, b) for f, b in items]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'manifest.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print('done', len(rows), 'changed near:', sum(r['near_data_changed'] for r in rows))


if __name__ == '__main__':
    main()
