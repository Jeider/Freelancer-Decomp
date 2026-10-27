"""Audited human solar libraries; never infer humanity from the solar_ prefix alone."""
from pathlib import Path
import re

HUMAN_LIBRARIES = {
    'solar_mat_dockable01.mat', 'solar_mat_dockable02.mat', 'solar_mat_dockable03.mat',
    'solar_mat_misc01.mat', 'solar_mat_misc02.mat', 'solar_mat_tink.mat',
    'solar_mat_ring.mat', 'solar_mat_hole.mat', 'solar_mat_tlr.mat',
    'solar_mat_space_dmg.mat', 'solar_mat_space_tank.mat', 'solar_mat_shield.mat',
    'solar_mat_s_inv.mat', 'solar_mat_co_base.mat', 'freeport7.mat',
}

def artificial_material(name, texture):
    # co_base and dockable01 also contain rock/ice, dockable03 contains trees.
    label=(name+'|'+texture).lower()
    return not any(word in label for word in ('nomad','nmd','dyson','lair','asteroid',
        'ast_', 'rock', 'ice', 'lava', 'forest', 'grass', 'tree_', 'glass', 'window',
        'space_girder01_op'))

def human_solars(game):
    catalog=(game/'DATA/SOLAR/solararch.ini').read_text(encoding='latin1')
    models=set()
    for block in re.split(r'^\[',catalog,flags=re.M):
        if not block.lower().startswith('solar]'): continue
        props={}
        for line in block.splitlines()[1:]:
            line=line.split(';',1)[0].strip()
            if '=' not in line: continue
            key,value=(s.strip().lower().replace('\\','/') for s in line.split('=',1))
            props.setdefault(key,[]).append(value)
        model=props.get('da_archetype',[''])[0]
        if not model.startswith('solar/') or any(s in model for s in ('nomad','nmd','dyson','lair','asteroid')): continue
        if any(Path(p).name in HUMAN_LIBRARIES for p in props.get('material_library',[])):
            models.add(model)
    return models
