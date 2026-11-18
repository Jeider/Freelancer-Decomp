"""Merge courier WAVs into the native dispatcher UTF, retaining every other leaf."""
from functools import lru_cache
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
sys.path.insert(0, str(ROOT/'tools'))
from generate_station_lods import Node, read_tree, write_tree


@lru_cache(maxsize=None)
def audio_key(code):
    result = subprocess.run([str(GAME/'createid.exe'), '-h', '-oc', code],
                            cwd=GAME, capture_output=True, text=True)
    # This legacy ID utility returns 1 even when it successfully prints the ID.
    return '0x'+format(int(result.stdout.split(',')[1].strip(), 16), 'X')


def entries(raw):
    header, roots = read_tree(raw)
    assert header[0]==0x20465455 and header[1]==0x101 and header[5]==44
    assert len(roots)==1 and roots[0].blob is None
    nodes = roots[0].children
    assert all(n.blob is not None and not n.children for n in nodes)
    # The original bank repeats some base names. Preserve their order/content;
    # lookup, like the client registry, uses the first matching name.
    result = {}
    for node in nodes:
        result.setdefault(node.name.lower(), node.blob)
    return result


def merge(raw, clips):
    before = entries(raw)
    header, roots = read_tree(raw)
    original_nodes = [(n.name, n.blob) for n in roots[0].children]
    nodes = {n.name.lower():n for n in roots[0].children}
    ids = {code:audio_key(code) for code in clips}
    assert len({key.lower() for key in ids.values()})==len(clips), 'Courier ID collision'
    for code, wav in clips.items():
        assert wav[:4]==b'RIFF' and wav[8:12]==b'WAVE', code
        name = ids[code]
        if name.lower() in nodes:
            for node in roots[0].children:
                if node.name.lower()==name.lower(): node.blob=wav
        else:
            roots[0].children.append(Node(name, blob=wav))
    packed = write_tree(header, roots)
    after = entries(packed)
    changed = {key.lower() for key in ids.values()}
    assert all(after[key]==value for key,value in before.items() if key not in changed)
    assert all(after[ids[code].lower()]==wav for code,wav in clips.items())
    restored = read_tree(packed)[1][0].children
    assert all(node.name==name and (name.lower() in changed or node.blob==blob)
               for node,(name,blob) in zip(restored,original_nodes))
    return packed, dict(ids=ids, previous_leaves=len(before), current_leaves=len(after),
                       preserved_leaves=len(before.keys()-changed))


def check(raw, clips, inherited=()):
    leaves = entries(raw)
    for code, wav in clips.items():
        assert leaves.get(audio_key(code).lower())==wav, 'Missing/stale UTF audio: '+code
    for code in inherited:
        assert leaves[audio_key(code).lower()][:4]==b'RIFF', 'Missing inherited base: '+code
