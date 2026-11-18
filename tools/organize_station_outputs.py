"""Move station workspaces under out/stations without rebuilding or installing."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
DEST = OUT / 'stations'
NAMES = (
    'bake_compound', 'forbes_mega', 'optimized_stations', 'potsdam_mega',
    'potsdam_panels', 'station_batch', 'station_docking', 'station_docks',
    'stuttgart_mega', 'terraform_mega', 'ulster_megabase', 'ulster_shortbase',
    'ulster_shortsplit', 'valensia_mega', 'valensia_optimization',
)


def safe(path, root):
    path = Path(path)
    resolved = path.resolve()
    assert resolved.is_relative_to(root) and resolved != root, path
    for parent in (path, *path.parents):
        if parent.exists():
            assert not parent.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, parent
    return resolved


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(folder):
    result = {}
    safe(folder, OUT)
    for directory, children, files in os.walk(folder, followlinks=False):
        for name in children:
            path = safe(Path(directory) / name, OUT)
            result[path.relative_to(folder).as_posix() + '/'] = None
        for name in files:
            path = safe(Path(directory) / name, OUT)
            before = path.stat()
            sha = digest(path)
            after = path.stat()
            assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), path
            result[path.relative_to(folder).as_posix()] = dict(
                bytes=after.st_size, mtime_ns=after.st_mtime_ns, sha256=sha)
    return result


def rewritten(raw):
    for name in NAMES:
        encoded = name.encode()
        for separator in (b'/', b'\\\\', b'\\'):
            old = b'out' + separator + encoded
            raw = re.sub(re.escape(old) + rb'(?![A-Za-z0-9_])',
                         lambda match: b'out' + separator + b'stations' + separator + encoded, raw)
        pattern = rb'''(["']out["']\s*/\s*)(["'])''' + encoded + rb'''\2'''
        raw = re.sub(pattern, lambda match: match[1] + match[2] + b'stations' + match[2] +
                     b' / ' + match[2] + encoded + match[2], raw)
    return raw


def source_edits():
    paths = subprocess.run(['rg', '-l', '-0', '|'.join(NAMES), 'tools', 'docs',
                            '-g', '*.py', '-g', '*.md', '-g', '*.txt', '-g', '*.cpp',
                            '-g', '*.h', '-g', '*.ps1', '-g', '*.cmd'],
                           cwd=ROOT, check=True, capture_output=True).stdout
    edits = {}
    for name in paths.decode('utf-8').split('\0'):
        if not name:
            continue
        path = safe(ROOT / name, ROOT)
        if path == Path(__file__).resolve():
            continue
        before = path.read_bytes()
        after = rewritten(before)
        if before != after:
            if path.suffix == '.py':
                ast.parse(after, filename=str(path))
            edits[path] = (before, after)
    return edits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    assert not DEST.exists(), 'Destination already exists; do not merge or overwrite'
    snapshots = {}
    for name in NAMES:
        source = safe(OUT / name, OUT)
        target = safe(DEST / name, OUT)
        assert source.is_dir() and not target.exists(), name
        snapshots[name] = inventory(source)
    edits = source_edits()
    entries = [entry for tree in snapshots.values() for entry in tree.values() if entry is not None]
    print(f'{len(NAMES)} directories; {len(entries)} files; '
          f'{sum(entry["bytes"] for entry in entries) / 1048576:.1f} MiB; '
          f'{len(edits)} source/document path updates', flush=True)
    print('\n'.join(str(path.relative_to(ROOT)) for path in edits), flush=True)
    if not args.apply:
        return
    for name, expected in snapshots.items():
        assert inventory(OUT / name) == expected, 'Workspace changed: ' + name
    for path, (before, _) in edits.items():
        assert path.read_bytes() == before, 'Source changed: ' + str(path)
    DEST.mkdir()
    moved, written = [], []
    try:
        for name in NAMES:
            source, target = safe(OUT / name, OUT), safe(DEST / name, OUT)
            source.rename(target)
            moved.append(name)
        for path, (_, after) in edits.items():
            written.append(path)
            path.write_bytes(after)
        for name, expected in snapshots.items():
            assert inventory(DEST / name) == expected, 'Moved contents changed: ' + name
            assert not (OUT / name).exists(), name
    except BaseException:
        for path in reversed(written):
            assert path.read_bytes() == edits[path][1], 'Changed during rollback: ' + str(path)
            path.write_bytes(edits[path][0])
        for name in reversed(moved):
            source, target = safe(DEST / name, OUT), safe(OUT / name, OUT)
            assert not target.exists(), target
            source.rename(target)
        raise
    report = dict(moves={f'out/{name}': f'out/stations/{name}' for name in NAMES},
                  files=snapshots, source_updates={str(path.relative_to(ROOT)): dict(
                      before=hashlib.sha256(before).hexdigest(), after=hashlib.sha256(after).hexdigest())
                      for path, (before, after) in edits.items()})
    (DEST / 'organization.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Moved; all file hashes, sizes, timestamps and subdirectories verified. No copies or installs.')


if __name__ == '__main__':
    main()
