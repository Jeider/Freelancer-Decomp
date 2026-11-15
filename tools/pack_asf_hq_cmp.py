"""Pack the hardpoint ASF HQ into one CMP: core plus the baked tail meshes.

Tail vertices are already in core space, so every joint is identity.
Collision stays in the existing asf_hq.sur. This pack does not write it.
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_station_lods as utf
import bake_compound as bake
import bake_one_part as part

MISC = Path(r'D:\Games\FL_MOD\DATA\SOLAR\misc')
CORE = MISC / 'asf_hq_core.3db'
TAILS = (
    'asf_hq_tail_front_1',
    'asf_hq_tail_front_2',
    'asf_hq_tail_back_1',
    'asf_hq_tail_back_2',
    'asf_hq_tail_left',
    'asf_hq_tail_right',
    'asf_hq_tail_front_3',
    'asf_hq_tail_back_3',
)
ROOT_NAME = 'Root'


def read(path):
    _, roots = utf.read_tree(Path(path).read_bytes())
    return roots[0]


def main():
    core = read(CORE)
    library = bake.clone(bake.one(core, 'VMeshLibrary'))
    shell = utf.Node('asf_hq_shell.3db')
    shell.children = [bake.clone(child) for child in core.children if child.name.lower() != 'vmeshlibrary']
    compound = utf.Node('\\')
    compound.children = [library, shell]
    entries = [part.part_entry('Root', ROOT_NAME, 0, shell.name)]
    fix = bytearray()
    for index, stem in enumerate(TAILS, 1):
        node = read(MISC / f'{stem}.3db')
        for mesh in bake.one(node, 'VMeshLibrary').children:
            library.children.append(bake.clone(mesh))
        file_name = f'{stem}.3db'
        visual = utf.Node(file_name)
        visual.children = [bake.clone(child) for child in node.children if child.name.lower() != 'vmeshlibrary']
        compound.children.append(visual)
        obj = f'tail{index:02d}'
        entries.append(part.part_entry('Part_' + obj, obj, len(entries), file_name))
        fix.extend(part.fix_record(ROOT_NAME, obj, np.eye(3), np.zeros(3)))
    cons = utf.Node('Cons')
    cons.children = [utf.Node('Fix', bytes(fix))]
    cmpnd = utf.Node('Cmpnd')
    cmpnd.children = [cons, *entries]
    compound.children.append(cmpnd)
    header = [0x20465455, 0x101, 0, 0, 0, 44, 0, 0, 0, 0, 0, 0, 0, 0]
    raw = utf.write_tree(header, [compound])
    (MISC / 'asf_hq.cmp').write_bytes(raw)
    print({'cmp': len(raw), 'parts': len(entries)})


if __name__ == '__main__':
    main()
