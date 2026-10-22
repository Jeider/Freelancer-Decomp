"""Compare the MultiLevel structure of each LOD-bundle model before and after the LOD install
(diagnostics): original levels, switch distances, which meshes each level references."""
import json
import struct as S
from pathlib import Path
import generate_station_lods as gen

DATA = Path('D:/games/FL_MOD/DATA')


def describe(data):
    _, roots = gen.read_tree(data)
    root = roots[0]
    lib = {gen.crc(n.name): n.name for n in gen.child(root, 'VMeshLibrary').children}
    ml = next((n for n in root.children if n.name.lower() == 'multilevel'), None)
    if ml is None:
        return 'no MultiLevel'
    parts = []
    for n in ml.children:
        if n.name.lower().startswith('level'):
            ref = gen.child(gen.child(n, 'VMeshPart'), 'VMeshRef').blob
            parts.append(f'{n.name}={lib.get(S.unpack_from("<I", ref, 4)[0], "?")}')
        elif n.blob is not None:
            vals = S.unpack_from('<%df' % (len(n.blob) // 4), n.blob)
            parts.append(f'{n.name}={[round(v) for v in vals]}')
    return ', '.join(parts)


rows = []
for folder in ('industrial_lods', 'component_lods'):
    bundle = Path('bin') / folder
    m = json.loads((bundle / 'manifest.json').read_text())
    receipt = json.loads((bundle / 'installation.json').read_text(encoding='utf-8-sig'))
    rows += [(r['file'], Path(receipt['Backup']) / r['file']) for r in m['models']]
rows.append(('SOLAR/MISC/space_trade_station_part.3db',
             DATA / 'SOLAR/MISC/.before_trade_station_lods_20261022_110538/space_trade_station_part.3db'))
for file, backup in rows:
    print(file.split('/')[-1])
    print('  before:', describe(backup.read_bytes()))
    print('  now:   ', describe((DATA / file).read_bytes()))
