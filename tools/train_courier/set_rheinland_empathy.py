"""Stage/apply the explicit Rheinland trader empathy change in Pythonlancer source."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('D:/Games/FL_MOD/Assets/Pythonlancer/universe/faction.py')
OUT = ROOT / 'out/train_courier/evacuation/empathy'
OLD = b'''    FactionRelation(
        RheinlandTraders,
        [
            Relation(RheinlandMain, FRIEND_MED),'''
NEW = b'''    FactionRelation(
        RheinlandTraders,
        [
            # Company standing also affects Rheinland, including locomotive losses.
            Relation(RheinlandMain, FRIEND_MED, 1.0, empathy_only_forward=True),'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.apply:
        manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
        before = SOURCE.read_bytes()
        after = (OUT / 'faction.py').read_bytes()
        if str(SOURCE) != manifest['source'] or digest(after) != manifest['after']:
            raise RuntimeError('Unexpected staged source')
        if digest(before) == manifest['after']:
            print('Already applied: tr_grp_rh -> rh_grp empathy = 1.0')
            return
        if digest(before) != manifest['before']:
            raise RuntimeError('Pythonlancer source changed; review and stage again')
        compile(after, str(SOURCE), 'exec')
        SOURCE.write_bytes(after)
        if SOURCE.read_bytes() != after:
            raise RuntimeError('Source verification failed; original retained in topic directory')
        print('Applied and verified: tr_grp_rh -> rh_grp empathy = 1.0')
        print('Pythonlancer source only; installed DATA unchanged.')
        return
    before = SOURCE.read_bytes()
    newline = b'\r\n' if b'\r\n' in before else b'\n'
    old, new = OLD.replace(b'\n', newline), NEW.replace(b'\n', newline)
    if before.count(old) != 1:
        raise RuntimeError('Expected exactly one original Rheinland trader relation')
    after = before.replace(old, new, 1)
    compile(after, str(SOURCE), 'exec')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'faction.before.py').write_bytes(before)
    (OUT / 'faction.py').write_bytes(after)
    diff = ''.join(difflib.unified_diff(
        before.decode('utf-8-sig').splitlines(keepends=True),
        after.decode('utf-8-sig').splitlines(keepends=True),
        fromfile='Pythonlancer/universe/faction.py',
        tofile='Pythonlancer/universe/faction.py'))
    (OUT / 'change.diff').write_text(diff, encoding='utf-8')
    (OUT / 'manifest.json').write_text(json.dumps({
        'source': str(SOURCE), 'before': digest(before), 'after': digest(after),
        'direction': 'tr_grp_rh -> rh_grp', 'empathy': 1.0,
    }, indent=2) + '\n', encoding='utf-8')
    print(diff)


if __name__ == '__main__':
    main()
