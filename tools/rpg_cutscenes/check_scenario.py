"""Check the staged/installed recording scenario; never call TTS or write DATA."""
import argparse
import csv
import json
import os
from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import types


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, default=Path("D:/Games/FL_MOD/Assets/Pythonlancer"))
    args = parser.parse_args()
    source, dependencies = args.source.resolve(), args.dependencies.resolve()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(source), str(dependencies)]
    from managers.rpg_voice import RpgVoiceManager
    from story.rpg.script import RpgScript
    from files.rpg_recordings import non_data_path
    from tools.voice_output import output_path
    manager = RpgVoiceManager(source, source / "story/rpg/rm0001.json")
    count = len(manager.script.fragments)
    assert count == 32
    data = manager.script.data
    assert data['nodes']['offer']['pool'] == 'licensed_offer'
    assert data['nodes']['requirements']['pool'] == 'licensed_requirements'
    assert 'tutorial' in data['choice_sets']['main']
    for topic in ('boarding', 'coupling', 'delivery'):
        assert data['choices'][topic]['goto'] == topic
        assert data['nodes'][topic]['choices'] == 'tutorial_return'
        assert 'action' not in data['choices'][topic]
    assert manager.script.data["rules"]["wagon_options"] == [2, 5, 10, 20]
    assert {manager.script.data["choices"][f"choose_{n}"]["pool"] for n in (2, 5, 10, 20)} == {
        "choose_2", "choose_5", "choose_10", "choose_20"}
    scratch = Path(__file__).resolve().parents[2] / "out/rpg_cutscenes/scenario_checks"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as name:
        root = Path(name)
        manager.prepare(root / "recordings")
        for language in ("ru", "en"):
            with (root / "recordings" / language / "lines.csv").open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            assert len(rows) == count and len({row["filename"] for row in rows}) == count
            assert rows[0]["fragment"] == "rm0001_frag0001"
            assert rows[3]["filename"] == "rm0001_frag0004_l001_player.wav"
            assert all(row["text"] == fragment[language] for row, fragment in zip(rows, manager.script.fragments))
        plan = manager.voices(root / "dry", ("ru", "en"), "Hassler", dry_run=True)
        assert "tools.voice_api" not in sys.modules and "tools.audio_folder" not in sys.modules
        assert "core" not in sys.modules and "managers.script" not in sys.modules
        for language, rows in plan["languages"].items():
            assert len(rows) == count
            for fragment, row in zip(manager.script.fragments, rows):
                assert row["actor"] == ("Trent" if fragment["role"] == "player" else "Hassler")
                assert Path(row["filename"]).parent.name == "rm0001"
                assert Path(row["filename"]).name == output_path(manager.script.line_name(fragment) + ".mp3").name
        try:
            manager.prepare(root / "DATA/RPG")
        except ValueError:
            pass
        else:
            raise AssertionError("DATA write was allowed")
        assert not (root / "DATA").exists()
        try:
            manager.voices(root / "invalid", ("ru",), "NonexistentActor", dry_run=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Unknown voice accepted")
        assert not (root / "invalid").exists()
        default = manager.voices(root / "default_actor", ("ru", "en"), dry_run=True)
        assert default['vendor_actor'] == 'RpgTradeDirector'
        for rows in default['languages'].values():
            assert {row['actor'] for row in rows} == {'RpgTradeDirector', 'Trent'}

        # Exercise orchestration with a recording spy instead of any network backend.
        calls = []
        class AudioFolder:
            @classmethod
            def generate_cutscene_sounds(cls, group, russian):
                assert Path.cwd() == source
                assert group.get_cutscene_folder() == "rm0001"
                sounds = group.get_sounds()
                assert len(sounds) == count
                assert len({sound.get_filename() for sound in sounds}) == count
                assert sounds[0].get_destination() == "audio\\MOD\\RPG\\rm0001"
                calls.append(russian)
        fake = types.ModuleType("tools.audio_folder")
        fake.AudioFolder = AudioFolder
        sys.modules["tools.audio_folder"] = fake
        cwd = Path.cwd()
        from tools.voicestudio import VoiceStudioClone
        with patch.object(VoiceStudioClone, 'source_file', return_value=Path('reference.wav')):
            manager.voices(root / "mock_record", ("ru", "en"), "Hassler")
        assert calls == [True, False] and Path.cwd() == cwd
        assert not list(root.rglob("*.thn")) and not list(root.rglob("*.mp3"))
    print("PASS: 32 RU/EN lines, licence explanation, separate spoken tutorial branch, stable filenames, native voice adapter, "
          "no DATA/THN/TTS, lazy backend, recording dispatch and cwd restoration")


if __name__ == "__main__":
    main()
