"""Remove only the rejected experimental normal texture from the installed MAT."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_station_lods as utf

REPO = Path(__file__).resolve().parents[2]
MAT = 'DATA/SOLAR/ASTEROIDS_MOD/KU_TGK/ast_ku_tgk.mat'
NORMAL = 'ku_tgk_rock_normal.tga'


def leaves(nodes, prefix=''):
    result = {}
    for node in nodes:
        key = prefix + '/' + node.name
        if node.blob is not None:
            result[key] = node.blob
        result.update(leaves(node.children, key))
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    game = parser.parse_args().game_root.resolve(strict=True)
    source = (game / MAT).read_bytes()
    header, tree = utf.read_tree(source)
    before = leaves(tree)
    def prune(nodes):
        for node in nodes:
            if node.name.lower() == 'texture library':
                node.children = [child for child in node.children if child.name.lower() != NORMAL.lower()]
            prune(node.children)
    prune(tree)
    result = utf.write_tree(header, tree)
    after = leaves(utf.read_tree(result)[1])
    expected = {path: blob for path, blob in before.items() if '/' + NORMAL + '/' not in path}
    assert after == expected, 'An unrelated material/texture leaf changed'
    out = REPO / 'src/obj/player_shadow_quality/assets'
    target = out / MAT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    (out / 'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source).hexdigest(),
        removed_bytes=len(source)-len(result), preserved_leaves=len(after)), indent=2))
    print(f'Removed normal texture only; preserved {len(after)} original leaves; freed {len(source)-len(result):,} bytes.')


if __name__ == '__main__':
    main()
