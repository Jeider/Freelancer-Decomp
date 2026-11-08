"""Install RPG authoring tools only; actual audio publication runs separately via DataFolder."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import os

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "out/rpg_cutscenes/pythonlancer_scenario_install"
DEFAULT = Path("D:/Games/FL_MOD/Assets/Pythonlancer")
BEGIN = "# BEGIN RPG CUTSCENE DISPATCH"
END = "# END RPG CUTSCENE DISPATCH"
DISPATCH = '''# BEGIN RPG CUTSCENE DISPATCH
# Keep RPG authoring independent of LancerCore/story startup and voice services.
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "rpg":
    sys.dont_write_bytecode = True
    from tools.rpg_voices import main as rpg_cutscenes_main
    rpg_cutscenes_main(sys.argv[2:])
    raise SystemExit(0)
# END RPG CUTSCENE DISPATCH
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def patched_single(content):
    text = content.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    normalized = text.replace("\r\n", "\n")
    if BEGIN in normalized:
        pattern = re.compile(re.escape(BEGIN) + r"\n.*?" + re.escape(END) + r"\n", re.S)
        normalized, count = pattern.subn(DISPATCH, normalized)
        if count != 1:
            raise ValueError("Unrecognized existing RPG dispatch block")
    else:
        if not normalized.startswith("import sys\n"):
            raise ValueError("Expected single.py to start with import sys; inspect before patching")
        normalized = "import sys\n" + DISPATCH + normalized[len("import sys\n"):]
    return normalized.replace("\n", newline).encode("utf-8")


def stage(destination, scenario=None, only=None):
    payload = OUT / "payload"
    files = {}

    def put(relative, data):
        if only and relative not in only:
            return
        if any(part.lower() == "data" for part in Path(relative).parts):
            raise ValueError("Scenario installation must not include DATA")
        path = payload / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files[relative] = {"before": digest(destination / relative), "after": digest(path)}

    put("single.py", patched_single((destination / "single.py").read_bytes()))
    for path in sorted((HERE / "pythonlancer").rglob("*.py")):
        put(path.relative_to(HERE / "pythonlancer").as_posix(), path.read_bytes())
    # Extend the central writer; never bypass it for staged/live DATA or rollback.
    folder_source = (destination / 'tools/data_folder.py').read_text(encoding='utf-8')
    extension = (HERE / 'data_folder_rpg.inc').read_text(encoding='utf-8')
    if '# BEGIN RPG AUDIO OUTPUT' in folder_source:
        pattern = r'\n    # BEGIN RPG AUDIO OUTPUT\n.*?    # END RPG AUDIO OUTPUT\n'
        folder_source, count = re.subn(pattern, lambda _: extension, folder_source, flags=re.S)
        if count != 1:
            raise ValueError('Unknown RPG DataFolder extension')
    else:
        anchor = '    def get_root(self):\n'
        if folder_source.count(anchor) != 1:
            raise ValueError('Unknown DataFolder source')
        folder_source = folder_source.replace(anchor, extension + '\n' + anchor)
    put('tools/data_folder.py', folder_source.encode('utf-8'))
    # Preserve an already installed, locally edited authoring catalog on updates.
    installed_spec = destination / "story/rpg/rm0001.json"
    spec = json.loads((scenario or (installed_spec if installed_spec.exists() else HERE / "rm0001.json")).read_text(encoding='utf-8'))
    spec.setdefault('casting', {'vendor': 'RpgTradeDirector', 'player': 'Trent'})
    put("story/rpg/rm0001.json", (json.dumps(spec, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    put("docs/rpg_cutscenes.md", (HERE / "RECORDING.md").read_bytes())
    # Test-only package overlays use upstream dependencies without copying them.
    # These files are outside the installation manifest.
    for package in ("tools", "managers", "files", "story"):
        (payload / package / "__init__.py").write_text(
            "from pkgutil import extend_path\n__path__ = extend_path(__path__, __name__)\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(destination), PYTHONDONTWRITEBYTECODE="1")
    # Staged single.py must invoke the new action before any legacy imports.
    for command in ("prepare",):
        generated = OUT / "generated" / command
        subprocess.run([str(destination / ".venv/Scripts/python.exe"), "-B", str(payload / "single.py"),
                        "rpg", command, "--output", str(generated)], cwd=payload, env=env, check=True)
        for path in sorted(generated.rglob("*")):
            if path.is_file():
                put((Path("results/rpg/rm0001") / command / "both" / path.relative_to(generated)).as_posix(), path.read_bytes())
    manifest = {"destination": str(destination), "files": files}
    if only and set(only) != set(files):
        raise ValueError('Unknown installation files: ' + ', '.join(sorted(set(only) - set(files))))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Staged {len(files)} Pythonlancer files; no installed files changed. Manifest: {OUT / 'manifest.json'}")


def apply():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    destination = Path(manifest["destination"]).resolve()
    payload = (OUT / "payload").resolve()
    for relative, hashes in manifest["files"].items():
        if any(part.lower() == "data" for part in Path(relative).parts):
            raise ValueError("Scenario installation must not include DATA")
        target, source = (destination / relative).resolve(), (payload / relative).resolve()
        if not target.is_relative_to(destination) or not source.is_relative_to(payload):
            raise ValueError("File escaped installation root")
        if digest(target) != hashes["before"] or digest(source) != hashes["after"]:
            raise ValueError(f"File changed since staging: {relative}")
    backup = OUT / "backups" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup.mkdir(parents=True)
    for relative, hashes in manifest["files"].items():
        if hashes["before"] is not None:
            path = backup / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination / relative, path)
            if digest(path) != hashes["before"]:
                raise ValueError(f"Backup mismatch: {relative}")
    shutil.copy2(OUT / "manifest.json", backup / "manifest.json")
    touched = []
    try:
        for relative, hashes in manifest["files"].items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            touched.append(relative)
            shutil.copy2(payload / relative, target)
            if digest(target) != hashes["after"]:
                raise ValueError(f"Installed hash mismatch: {relative}; backups: {backup}")
    except Exception:
        for relative in reversed(touched):
            target = (destination / relative).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("Rollback escaped installation root")
            if manifest["files"][relative]["before"] is None:
                target.unlink(missing_ok=True)
            else:
                shutil.copy2(backup / relative, target)
        raise
    print(f"Installed {len(manifest['files'])} files into {destination}. Backups: {backup}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pythonlancer", type=Path, default=DEFAULT)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--scenario", type=Path, help="Explicitly publish a revised scenario instead of preserving the installed catalog")
    parser.add_argument("--only", nargs='+', help="Stage only these installation paths; preserve other concurrent authoring work")
    args = parser.parse_args()
    if args.apply:
        apply()
    else:
        stage(args.pythonlancer.resolve(), args.scenario, args.only)


if __name__ == "__main__":
    main()
