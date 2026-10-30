"""Prepare optional one-shot trade-lane animations. Never writes to the game."""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
sys.path.insert(0, str(ROOT / 'tools'))
from generate_station_lods import Node, read_tree, write_tree, child

NAMES = ('Sc_activate left', 'Sc_activate right')
# Verified against HpLeftLane/HpRightLane positions and Cmpnd/Cons/Rev origins.
JOINTS = ('tlr2_lod1', 'tlr1_lod1')
DURATION = 6.0
RAMP = 1.5
FPS = 30


def angle(t):
    """Integrated smoothstep velocity: zero velocity/acceleration at both ends."""
    speed = math.tau / (DURATION - RAMP)
    if t < RAMP:
        u = t / RAMP
        return speed * RAMP * (u**3 - .5*u**4)
    if t > DURATION - RAMP:
        return math.tau - angle(DURATION - t)
    return speed * (t - RAMP/2)


def frames():
    result = []
    for i in range(int(DURATION*FPS)+1):
        a = angle(i/FPS)
        # EngBase's revolute channel interpolates across +/-pi via the short arc.
        result.append(math.atan2(math.sin(a), math.cos(a)))
    result[0] = result[-1] = 0.0
    return result


def branch(name, children):
    n = Node(name)
    n.children = children
    return n


def patch_model(data):
    header, roots = read_tree(data)
    scripts = child(child(roots[0], 'Animation'), 'Script')
    for name, joint in zip(NAMES, JOINTS):
        scripts.children = [n for n in scripts.children if n.name != name]
        values = frames()
        channel = branch('Channel', [
            Node('Header', struct.pack('<IfI', len(values), 1/FPS, 1)),
            Node('Frames', struct.pack('<%df' % len(values), *values))])
        scripts.children.append(branch(name, [branch('Joint map 0', [
            Node('Parent name', b'Root\0'),
            Node('Child name', joint.encode('ascii') + b'\0'), channel])]))
    return write_tree(header, roots)


def edit_section(data, header, nickname, transform):
    text = data.decode('cp1251')
    pattern = re.compile(r'(?ms)^\[' + re.escape(header) + r'\][^\r\n]*\r?\n.*?(?=^\[|\Z)')
    count = 0
    def replace(match):
        nonlocal count
        block = match.group()
        if re.search(r'(?mi)^nickname\s*=\s*' + re.escape(nickname) + r'\s*$', block):
            count += 1
            return transform(block)
        return block
    result = pattern.sub(replace, text)
    assert count == 1, (header, nickname, count)
    return result.encode('cp1251')


def patch_solar(data):
    def transform(block):
        block = re.sub(r'(?mi)^(?:left|right)_ring_anim\s*=.*\r?\n', '', block)
        newline = '\r\n' if '\r\n' in block else '\n'
        return re.sub(r'(?mi)^(nickname\s*=\s*Trade_Lane_Ring)[ \t]*\r?$',
                      lambda m: m[1] + newline + 'left_ring_anim = ' + NAMES[0] + newline +
                      'right_ring_anim = ' + NAMES[1] + ('\r' if newline == '\r\n' else ''), block)
    return edit_section(data, 'Solar', 'Trade_Lane_Ring', transform)


def patch_loadout(data):
    return edit_section(data, 'Loadout', 'trade_lane_ring_main', lambda block:
        re.sub(r'(?mi)^equip\s*=\s*legal_tradelane_animation[ \t]*\r?\n', '', block))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    stage = ROOT/'src/obj/tradelane_anim_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
    transforms = {
        'DATA/SOLAR/DOCKABLE/tlr_root.3db': patch_model,
        'DATA/SOLAR/DOCKABLE/tlr_legal_lod5.cmp': patch_model,
        'DATA/SOLAR/solararch.ini': patch_solar,
        'DATA/SOLAR/loadouts.ini': patch_loadout,
    }
    paths = ['bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/Common.dll', 'bin/Common.pdb']
    for rel in paths + list(transforms):
        target = stage/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel in transforms:
            target.write_bytes(transforms[rel]((GAME/rel).read_bytes()))
        else:
            shutil.copy2(ROOT/rel, target)
    paths += list(transforms)
    manifest = {'game': str(GAME), 'files': [
        {'relative': rel, 'original': sha(GAME/rel), 'prepared': sha(stage/rel)} for rel in paths],
        'dependencies': [{'relative': rel, 'sha256': sha(GAME/rel)} for rel in
                         ['bin/DALib.dll', 'bin/EngBase.dll', 'bin/dacom.dll']]}
    (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    shutil.copy2(Path(__file__).with_name('install.ps1'), stage/'install.ps1')
    print(stage)
    print('6 seconds, 181 frames, one turn; geometry and existing scripts preserved. Game unchanged.')


if __name__ == '__main__':
    main()
