"""Verify/install the embedded shader animation, clear RP9 cache, clean this build."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/shader_startup'
BUILD = OUT / 'build'
GAME = Path('D:/Games/FL_MOD/bin')
FILES = ('RP9.dll', 'RP9.pdb', 'freelancer.exe', 'freelancer.pdb')
MANIFEST = OUT / 'animation_install.json'
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path, root):
    path, root = Path(path), Path(root).resolve()
    resolved = path.resolve()
    assert resolved.is_relative_to(root), path
    for entry in (path, *path.parents):
        if entry.exists():
            assert not (entry.stat(follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT), entry
    return resolved


def idle():
    processes = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH']).lower()
    assert not any(b'"' + name + b'"' in processes for name in
                   (b'freelancer.exe', b'flserver.exe', b'freelancer_window.exe')), 'Close game/server before installation'


def verify_resource(path):
    # LOAD_LIBRARY_AS_DATAFILE never executes the game or its DLL initializers.
    k = c.WinDLL('kernel32', use_last_error=True)
    k.LoadLibraryExW.argtypes = [c.c_wchar_p, c.c_void_p, c.c_uint]
    k.LoadLibraryExW.restype = c.c_void_p
    k.FindResourceW.argtypes = [c.c_void_p, c.c_wchar_p, c.c_void_p]
    k.FindResourceW.restype = c.c_void_p
    k.LoadResource.argtypes = [c.c_void_p, c.c_void_p]
    k.LoadResource.restype = c.c_void_p
    k.SizeofResource.argtypes = [c.c_void_p, c.c_void_p]
    k.SizeofResource.restype = c.c_uint
    k.LockResource.argtypes = [c.c_void_p]
    k.LockResource.restype = c.c_void_p
    k.FreeLibrary.argtypes = [c.c_void_p]
    module = k.LoadLibraryExW(str(path), None, 2)
    assert module, c.get_last_error()
    try:
        resource = k.FindResourceW(module, 'FREELANCER_SHADER_ANIMATION', 10)
        assert resource, 'Client is missing the animation resource'
        pointer = k.LockResource(k.LoadResource(module, resource))
        data = c.string_at(pointer, k.SizeofResource(module, resource))
        assert hashlib.sha256(data).hexdigest() == digest(ROOT / 'src/freelancer/resources/shader_startup/junko.frames')
        return len(data)
    finally:
        k.FreeLibrary(module)


def verify_imports(names=('RP9.dll', 'freelancer.exe')):
    compiler, env = compiler_env()
    def dump(option, path):
        return subprocess.check_output([str(compiler / 'dumpbin.exe'), option, str(path)], env=env, text=True)
    exports_cache = {}
    def exports(path):
        if path not in exports_cache:
            exports_cache[path] = {name: int(ordinal) for ordinal, name in re.findall(
                r'^\s+(\d+)\s+[0-9A-F]+\s+(?:[0-9A-F]+\s+)?(\S+)', dump('/exports', path), re.M)}
        return exports_cache[path]
    dependencies, count = {}, 0
    for name in names:
        new = BUILD / 'bin' / name
        before, after = exports(GAME / name), exports(new)
        assert all(after.get(key) == value for key, value in before.items()), 'Changed exports: ' + name
        dependency = None
        for line in dump('/imports', new).splitlines():
            match = re.match(r'^    (\S+\.dll)\s*$', line, re.I)
            if match:
                dependency = match[1]
                continue
            match = re.match(r'^\s+[0-9A-F]+\s+(\?\S+|[A-Za-z_]\S*)\s*$', line)
            if not match or not dependency:
                continue
            candidate = BUILD / 'bin' / dependency
            path = candidate if dependency.lower() == 'rp9.dll' and candidate.exists() else GAME / dependency
            if path.exists():
                assert match[1] in exports(path), (name, dependency, match[1])
                count += 1
                if path.parent == GAME:
                    dependencies[path.name] = digest(path)
    common = json.loads((BUILD / 'imports/source.json').read_text())
    assert digest(GAME / 'Common.dll') == common['sha256']
    return dependencies, count


def cache_path():
    override = os.environ.get('FREELANCER_SHADER_CACHE_DIR')
    return Path(override) if override else Path(os.environ['LOCALAPPDATA']) / 'Freelancer-Decomp/RP9/ShaderCache'


def cache_files(folder):
    folder = safe(folder, folder)
    if not folder.exists():
        return []
    return [safe(path, folder) for path in folder.iterdir()
            if re.fullmatch(r'[0-9a-f]{64}\.bin', path.name) and path.is_file()]


def prepare():
    resource_size = verify_resource(BUILD / 'bin/freelancer.exe')
    dependencies, count = verify_imports()
    checks = (OUT / 'animation/animation_check.txt').read_text()
    assert 'PASS animated and plain windows' in checks and 'FAIL' not in checks
    folder = safe(cache_path(), cache_path())
    cached = cache_files(folder)
    manifest = {'files': {name: {'before': digest(GAME / name), 'after': digest(BUILD / 'bin' / name)} for name in FILES},
                'dependencies': dependencies, 'verified_imports': count, 'embedded_bytes': resource_size,
                'cache': str(folder), 'cache_count': len(cached), 'cache_bytes': sum(p.stat().st_size for p in cached)}
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Ready: {len(FILES)} binaries/symbols, {count} resolved imports, {resource_size} embedded bytes; clear {len(cached)} shader cache files')


def cleanup():
    # Only this isolated build tree and the demo's compiler intermediates.
    candidates = []
    for directory, children, files in os.walk(safe(BUILD, OUT), followlinks=False):
        for child in children:
            safe(Path(directory) / child, BUILD)
        for name in files:
            path = safe(Path(directory) / name, BUILD)
            if path.suffix.lower() not in ('.log', '.json', '.def'):
                candidates.append(path)
    candidates += [OUT / 'animation/demo.obj', OUT / 'animation/animation.res']
    total = 0
    for path in candidates:
        safe(path, OUT)
        if path.exists():
            before = path.stat()
            total += before.st_size
            assert path.stat().st_mtime_ns == before.st_mtime_ns
            path.unlink()
    return total


def apply():
    idle()
    manifest = json.loads(MANIFEST.read_text())
    for name, expected in manifest['dependencies'].items():
        assert digest(GAME / name) == expected, 'Dependency changed: ' + name
    previous = {}
    for name in FILES:
        target, source = safe(GAME / name, GAME), safe(BUILD / 'bin' / name, BUILD)
        previous[name] = target.read_bytes()
        assert hashlib.sha256(previous[name]).hexdigest() == manifest['files'][name]['before'], 'Installed file changed: ' + name
        assert digest(source) == manifest['files'][name]['after'], 'Build changed: ' + name
    written = []
    try:
        for name in FILES:
            written.append(name)
            (GAME / name).write_bytes((BUILD / 'bin' / name).read_bytes())
        for name in FILES:
            assert digest(GAME / name) == manifest['files'][name]['after'], name
        verify_resource(GAME / 'freelancer.exe')
    except BaseException:
        for name in written:
            (GAME / name).write_bytes(previous[name])
        raise
    # Installation is verified; rollback copies existed only in memory.
    previous.clear()
    idle()
    folder = Path(manifest['cache'])
    assert safe(cache_path(), cache_path()) == folder.resolve(), 'Shader cache location changed'
    cached = cache_files(folder)
    removed_bytes = sum(p.stat().st_size for p in cached)
    for path in cached:
        safe(path, folder).unlink()
    assert not cache_files(folder), 'Shader cache was repopulated during installation'
    manifest['cache_removed'] = len(cached)
    manifest['cache_removed_bytes'] = removed_bytes
    manifest['build_cleanup_bytes'] = cleanup()
    (OUT / 'animation_installed.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Installed and hash-verified {len(FILES)} files; embedded resource verified; cleared {len(cached)} cache files; cleaned {manifest["build_cleanup_bytes"]} build bytes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else prepare()
