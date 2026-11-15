"""Install only the reviewed Valensia payload; never runs Pythonlancer generation."""
import argparse
from datetime import datetime
import json
import valensia_optimize as v


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((v.OUT/'manifest.json').read_text())
    assert (v.OUT/'checks.json').exists(), 'Run check_valensia.py first'
    assert (v.OUT/'native_check.ok').exists(), 'Run native SUR verification first'
    digest = v.sha256((v.OUT/'manifest.json').read_bytes()).hexdigest()
    assert json.loads((v.OUT/'checks.json').read_text())['manifest_sha256'] == digest
    assert (v.OUT/'native_check.ok').read_text() == digest
    for name, digest in manifest['sources'].items():
        assert v.sha256((v.GAME/name).read_bytes()).hexdigest() == digest, 'Source changed: '+name
    contents, before = {}, {}
    for name, digest in manifest['payload'].items():
        content = (v.OUT/'stage'/name).read_bytes()
        assert v.sha256(content).hexdigest() == digest, 'Staged payload changed: '+name
        target = v.GAME/name
        old = target.read_bytes() if target.exists() else None
        assert name in manifest['sources'] or old is None or old == content, 'New target already exists: '+name
        if old != content:
            contents[name], before[name] = content, old
    print('Files to install:', len(contents))
    if not args.apply: return
    backup = v.OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    save, live = v.data_folder(v.GAME, backup), v.data_folder(v.GAME, v.GAME)
    for name, content in before.items():
        if content is None: continue
        if name.startswith('DATA/'):
            save.sync_data_file(name[5:], content)
        else:
            path = backup/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    backup.mkdir(parents=True, exist_ok=True)
    (backup/'transaction.json').write_text(json.dumps({n:None if c is None else v.sha256(c).hexdigest() for n,c in before.items()}, indent=2))
    touched = []
    try:
        for name, content in contents.items():
            touched.append(name)
            if name.startswith('DATA/'):
                live.sync_data_file(name[5:], content)
            else:
                assert name in (v.TEMPLATE, v.ORIGINAL_TEMPLATE)
                (v.GAME/name).write_bytes(content)
        for name, digest in manifest['payload'].items():
            assert v.sha256((v.GAME/name).read_bytes()).hexdigest() == digest, name
    except Exception:
        for name in reversed(touched):
            if name.startswith('DATA/'):
                if before[name] is None: live.remove_data_file(name[5:])
                else: live.sync_data_file(name[5:], before[name])
            else:
                if before[name] is None: (v.GAME/name).unlink()
                else: (v.GAME/name).write_bytes(before[name])
        raise
    (v.OUT/'installed.json').write_text(json.dumps(dict(backup=str(backup), files=len(contents)), indent=2))
    print('Installed; backup:', backup)


if __name__ == '__main__': main()
