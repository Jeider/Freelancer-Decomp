"""Stage/install static RPG contacts, Content.dll and a standalone Pythonlancer generator."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from generate import generate, SPOT, FIDGET, CLICK_SCRIPT

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "src/obj/rpg_contacts/install"
PAYLOAD = ("bin/Content.dll", "bin/Content.pdb", "DATA/RPG/contacts.ini",
           "DATA/RPG/rh_biz_contact.ini", "DATA/RPG/dialogue_choice.thn", "DATA/RPG/space.ini",
           "bin/freelancer.exe", "bin/freelancer.pdb", "Assets/Pythonlancer/tools/rpg_contacts.py")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def validate_assets(game):
    system = (game / "DATA/UNIVERSE/SYSTEMS_MOD/RH_BIZMARK/rh_biz.ini").read_text(encoding="utf-8-sig")
    assert "nickname = rh_biz_01\n" in system and "dock_with = rh_biz_01_base" in system, "Missing Bismarck docking ring"
    loadouts = (game / "DATA/SHIPS/loadout_msn.ini").read_text(encoding="utf-8-sig")
    assert "nickname = ms3_hassler\n" in loadouts, "Missing mission 3 Hassler loadout"
    # Check the actual room used by this mod, not a similarly named retail base.
    room = game / "DATA/UNIVERSE/SYSTEMS_MOD/RH_BIZMARK/Room/biz_01_bar.ini"
    assert "rh_01_bar_hardpoint_01.thn" in room.read_text().lower(), "Room layout changed"
    layout = game / "DATA/SCRIPTS/BASES/Rh_01_Bar_hardpoint_01.thn"
    assert SPOT.encode() in layout.read_bytes(), "Placement is absent from room THN"
    for marker in (b"Zs/NPC/mFloor2/01/PCU/Camera", b"Zs/NPC/mFloor2/01/P/Stand"):
        assert marker in layout.read_bytes(), "Missing player choice camera/placement"
    assert (game / "DATA" / FIDGET.replace("\\", "/")).is_file(), "Missing fidget"
    assert (game / "DATA" / CLICK_SCRIPT.replace("\\", "/")).is_file(), "Missing click cutscene"
    mbases = (game / "DATA/MISSIONS/mbases.ini").read_text(encoding="utf-8-sig")
    base = mbases.lower().split("nickname = rh_biz_01_base", 1)[1].split("[mbase]", 1)[0]
    assert not any(SPOT.lower() in line for line in base.splitlines() if line.strip().startswith("fixture")), "Placement already has a fixture"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=Path("D:/games/FL_MOD"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    validate_assets(game)
    if not args.apply:
        generate(STAGE)
        for name in ("Content.dll", "Content.pdb"):
            copy(ROOT / "src/obj/rpg_contacts/build_Release_1/bin" / name, STAGE / "bin" / name)
        for name in ("freelancer.exe", "freelancer.pdb"):
            copy(ROOT / "src/obj/rpg_contacts/build_Release_1_client/bin" / name, STAGE / "bin" / name)
        copy(Path(__file__).with_name("generate.py"), STAGE / PAYLOAD[-1])
        manifest = dict(game=str(game), files=[dict(path=p, before=digest(game/p), after=digest(STAGE/p)) for p in PAYLOAD])
        (STAGE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("Validated placement/fidget and staged", len(PAYLOAD), "files:", STAGE)
        return
    manifest = json.loads((STAGE / "manifest.json").read_text(encoding="utf-8"))
    if Path(manifest["game"]).resolve() != game or tuple(x["path"] for x in manifest["files"]) != PAYLOAD:
        raise RuntimeError("Unexpected manifest")
    processes = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, check=True).stdout.lower()
    for name in (b"freelancer.exe", b"freelancer_window.exe", b"freelancer_en.exe", b"freelancer_window_en.exe", b"flserver.exe"):
        if b'"' + name + b'"' in processes:
            raise RuntimeError("Close Freelancer/FLServer before installation")
    for item in manifest["files"]:
        if digest(game/item["path"]) != item["before"] or digest(STAGE/item["path"]) != item["after"]:
            raise RuntimeError("File changed since staging: " + item["path"])
    backup = ROOT / "src/obj/rpg_contacts/backups" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    for item in manifest["files"]:
        if item["before"] is not None:
            copy(game/item["path"], backup/item["path"])
            if digest(backup/item["path"]) != item["before"]:
                raise RuntimeError("Backup verification failed")
    copy(STAGE/"manifest.json", backup/"manifest.json")
    touched = []
    try:
        for item in manifest["files"]:
            touched.append(item)
            copy(STAGE/item["path"], game/item["path"])
            if digest(game/item["path"]) != item["after"]:
                raise RuntimeError("Install verification failed")
    except Exception:
        for item in reversed(touched):
            if item["before"] is None:
                (game/item["path"]).unlink(missing_ok=True)
            else:
                copy(backup/item["path"], game/item["path"])
        raise
    print("Installed and verified:", game)
    print("Backup:", backup)


if __name__ == "__main__":
    main()
