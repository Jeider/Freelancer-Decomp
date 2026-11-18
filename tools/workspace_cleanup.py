"""Explicit, workspace-only cleanup of generated builds and character experiments.

Plan first; apply exactly that inventory. Never touch the game or source trees.
Staged DATA files are removed through Pythonlancer's DataFolder API.
"""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'out/workspace_cleanup'
ALLOWED = (ROOT / 'out', ROOT / 'src/obj')
CHARACTERS = {
    'all_hair', 'body_smoothing_audit', 'character_hair_audit', 'character_rounding',
    'comm_hat', 'customization', 'darcy_hair', 'hair_lighting', 'hair_rollout',
    'hatcher_hair', 'juni_hair', 'kaitlyn_concept', 'nomad_character', 'nomad_search',
    'reichman_body_analysis', 'reichman_body_test', 'reichman_body_test_v2',
    'reichman_body_test_v3', 'hatcher_body_full_smooth', 'hatcher_body_round_bracers',
    'hatcher_body_slim_bracers', 'hatcher_body_smooth', 'hatcher_body_test',
}
SOURCE_EXT = {'.py', '.cpp', '.c', '.h', '.hpp', '.inl', '.hlsl', '.ps1', '.cmd',
              '.bat', '.vcxproj', '.sln', '.props', '.targets'}
BUILD_EXT = {'.iobj', '.ipdb', '.pch', '.ilk', '.idb', '.tlog', '.res', '.exp'}
PROTECTED = ('out/nomad_character/alien', 'out/nomad_character/city',
             'out/workspace_cleanup', 'src/obj/customization/SAVE',
             # Another agent is actively rebuilding bodies from these inputs.
             'out/character_rounding',
             'out/hatcher_body_smooth/original', 'out/hatcher_body_smooth/report.json',
             'out/reichman_body_test/original', 'out/reichman_body_test/report.json',
             'out/nomad_character/game_body_v3/manifest.json',
             'src/obj/production')
BUILD_STEMS = {p.stem.lower() for p in (ROOT / 'bin').glob('*.pdb')}
BUILD_STEMS.update(('equipresources', 'infocards', 'misctext', 'misctextinfo2',
                    'nameresources', 'offerbriberesources', 'resources', 'serverresources'))


def within(path, parent):
    return path == parent or path.is_relative_to(parent)


def safe(path):
    path = Path(path)
    resolved = path.resolve(strict=True)
    if not any(resolved != root and resolved.is_relative_to(root) for root in ALLOWED):
        raise ValueError(f'Outside allowed output trees: {path}')
    current = path
    while current != ROOT:
        if current.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f'Reparse point: {current}')
        current = current.parent
    return resolved


def tracked():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True,
                            capture_output=True).stdout
    return {s.decode('utf8').casefold() for s in result.split(b'\0') if s}


def reason(path):
    rel = path.relative_to(ROOT).as_posix()
    if any(rel == p or rel.startswith(p + '/') for p in PROTECTED):
        return None
    if path.suffix.lower() in SOURCE_EXT:
        return None
    parts = path.relative_to(ROOT).parts
    if (parts[0] == 'out' and parts[1] in CHARACTERS) or rel.startswith('src/obj/customization/'):
        return 'character_results'
    if path.stem.lower() in BUILD_STEMS and path.suffix.lower() in ('.dll', '.exe', '.pdb', '.lib', '.exp'):
        return 'build_copies'
    if any(part.lower().startswith(('backup', 'rollback', 'original', 'reference'))
           or part.lower() in ('save', 'engine_rollback', 'pythonlancer_preservation')
           for part in parts):
        return None
    if rel.startswith('out/base_interiors/rh_biz_01_base/bar/'):
        if parts[4] in {f'prototype_v{i}' for i in range(1, 8)}:
            return 'superseded_interior_previews'
    ext = path.suffix.lower()
    if ext == '.obj':
        with path.open('rb') as stream:
            header = stream.read(4)
        # Binary COFF only: do not delete user-supplied Wavefront OBJ models.
        if header[:2] in (b'\x4c\x01', b'\x64\x86', b'\x64\xaa') or header == b'\0\0\xff\xff':
            return 'compiler_intermediates'
    elif ext == '.pdb':
        with path.open('rb') as stream:
            header = stream.read(32)
        if header.startswith(b'Microsoft C/C++ MSF'):
            return 'build_debug_symbols'
    elif ext in BUILD_EXT:
        return 'compiler_intermediates'
    elif ext in ('.pyc', '.blend1', '.blend2'):
        return 'regenerable_cache'
    return None


def inventory():
    known = tracked()
    entries = []
    for root in ALLOWED:
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [n for n in dirs if not (Path(directory, n).lstat().st_file_attributes
                                               & stat.FILE_ATTRIBUTE_REPARSE_POINT)]
            for name in files:
                path = Path(directory, name)
                rel = path.relative_to(ROOT).as_posix()
                if rel.casefold() in known:
                    continue
                if path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    continue
                category = reason(path)
                if category:
                    info = path.stat()
                    entries.append(dict(path=rel, bytes=info.st_size,
                                        mtime_ns=info.st_mtime_ns, reason=category))
    return entries


def totals(entries):
    sizes = collections.Counter()
    for entry in entries:
        sizes[entry['reason']] += entry['bytes']
    return dict(files=len(entries), bytes=sum(sizes.values()),
                gib=round(sum(sizes.values()) / 1024 ** 3, 3),
                categories_gib={k: round(v / 1024 ** 3, 3) for k, v in sizes.items()})


def data_folder_class():
    source = Path('D:/Games/FL_MOD/Assets/Pythonlancer/tools/data_folder.py')
    spec = importlib.util.spec_from_file_location('cleanup_data_folder', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    REPORT.mkdir(parents=True, exist_ok=True)
    manifest = REPORT / 'plan.json'
    if not args.apply:
        entries = inventory()
        plan = dict(root=str(ROOT), free_bytes=shutil.disk_usage(ROOT).free,
                    summary=totals(entries), entries=entries)
        manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps(plan['summary'], indent=2))
        return
    plan = json.loads(manifest.read_text(encoding='utf8'))
    assert Path(plan['root']) == ROOT
    known = tracked()
    # Validate every final absolute path and unchanged file before any deletion.
    for entry in plan['entries']:
        path = safe(ROOT / entry['path'])
        info = path.stat()
        assert entry['path'].casefold() not in known
        assert reason(path) == entry['reason'], path
        assert (info.st_size, info.st_mtime_ns) == (entry['bytes'], entry['mtime_ns']), path
    DataFolder = data_folder_class()
    removed, failed, parents = [], [], set()
    free_before = shutil.disk_usage(ROOT).free
    with (REPORT / 'removed.jsonl').open('w', encoding='utf8') as journal:
        for entry in plan['entries']:
            path = safe(ROOT / entry['path'])
            try:
                data_root = next((p for p in path.parents if p.name.lower() == 'data'), None)
                if data_root:
                    DataFolder(root=data_root.parent).remove_data_file(path.relative_to(data_root))
                else:
                    path.unlink()
                removed.append(entry)
                parents.update(p for p in path.parents if any(p != r and p.is_relative_to(r) for r in ALLOWED))
                journal.write(json.dumps(entry, ensure_ascii=False) + '\n')
            except OSError as exc:
                failed.append(dict(path=entry['path'], error=str(exc)))
    # Empty directories only, never recursive deletion; protected roots stay.
    for directory in sorted(parents, key=lambda p: len(p.parts), reverse=True):
        rel = directory.relative_to(ROOT).as_posix()
        if any(rel == p or rel.startswith(p + '/') for p in PROTECTED):
            continue
        if directory.exists() and not any(directory.iterdir()):
            safe(directory)
            data_root = next((p for p in directory.parents if p.name.lower() == 'data'), None)
            if data_root:
                DataFolder(root=data_root.parent).remove_empty_data_directory(directory.relative_to(data_root))
            else:
                directory.rmdir()
    result = dict(root=str(ROOT), removed=totals(removed), failures=failed,
                  free_before_bytes=free_before, free_after_bytes=shutil.disk_usage(ROOT).free,
                  game_modified=False)
    (REPORT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
