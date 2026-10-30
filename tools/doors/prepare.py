"""Finite door clips and opt-in archetype. Stages only; never edits mission triggers."""
from pathlib import Path
import copy
import struct
import re
import sys
ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
sys.path.insert(0, str(ROOT/'tools'))
from generate_station_lods import read_tree, write_tree, child

MODEL = 'DATA/SOLAR/DOCKABLE/lair_door01.cmp'
SOLAR = 'DATA/SOLAR/solararch.ini'
CLIPS = {'sc_open_forever': 'sc_door_open', 'sc_close_forever': 'sc_door_close'}

def patch_model(data):
    header, roots = read_tree(data)
    scripts = child(child(roots[0], 'Animation'), 'Script')
    for source, name in CLIPS.items():
        script = copy.deepcopy(child(scripts, source))
        script.name = name
        for joint in script.children:
            channel = child(joint, 'Channel')
            h, f = child(channel,'Header'), child(channel,'Frames')
            count, step, flags = struct.unpack('<IfI', h.blob)
            assert step == -1 and flags == 1 and len(f.blob) == count*8
            frames = list(struct.iter_unpack('<ff', f.blob))
            assert frames[-1][0] > 1000000 and frames[-2][0] < 60
            assert frames[-1][1] == frames[-2][1], 'tail changes pose'
            frames.pop()
            h.blob = struct.pack('<IfI', len(frames), step, flags)
            f.blob = b''.join(struct.pack('<ff',*x) for x in frames)
        scripts.children = [s for s in scripts.children if s.name != name]
        scripts.children.append(script)
    return write_tree(header,roots)

def patch_solar(data):
    text = data.decode('cp1251')
    blocks = list(re.finditer(r'(?ms)^\[Solar\][^\r\n]*\r?\n.*?(?=^\[|\Z)',text))
    source = next(m.group() for m in blocks if re.search(r'(?mi)^nickname\s*=\s*lair_anim_door\s*$',m.group()))
    new = re.sub(r'(?mi)^nickname\s*=.*$', 'nickname = lair_proximity_door', source).replace('\r\n','\n')
    new = re.sub(r'(?mi)^(open_anim|open_sound|close_sound|jump_out_hp|docking_sphere|loadout)\s*=.*\n','',new)
    new = new.rstrip() + '''
proximity_door = true
door_scan_radius = 800
door_release_radius = 1100
door_close_delay = 3
anim_open = sc_door_open
anim_close = sc_door_close
door_open_sound = lair_door_open
door_close_sound = lair_door_close

'''
    old = next((m for m in blocks if re.search(r'(?mi)^nickname\s*=\s*lair_proximity_door\s*$',m.group())),None)
    if '\r\n' in text: new = new.replace('\n','\r\n')
    if old: text = text[:old.start()] + new + text[old.end():]
    else: text += '\r\n' + new
    return text.encode('cp1251')

if __name__ == '__main__':
    out = ROOT/'src/obj/doors/assets'
    for rel, patch in ((MODEL,patch_model),(SOLAR,patch_solar)):
        dest=out/rel; dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(patch((GAME/rel).read_bytes()))
    print('Prepared sc_door_open / sc_door_close (3.333333 seconds), lair_proximity_door. Game untouched.')
