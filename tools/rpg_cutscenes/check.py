"""Integration checks against the installed Pythonlancer scene implementation."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import wave
from xml.etree import ElementTree

from build import ROOT, DEFAULT_SOURCE, line_name, load_spec


def main():
    spec_path = Path(__file__).with_name("rm0001.json")
    spec = load_spec(spec_path)
    out = ROOT / "out/rpg_cutscenes/check"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        work = Path(temporary)
        audio = work / "audio"
        for lang, seconds in (("ru", 2), ("en", 27)):
            for fragment in spec["fragments"]:
                path = audio / spec["id"] / lang / (line_name(fragment) + ".wav")
                path.parent.mkdir(parents=True, exist_ok=True)
                with wave.open(str(path), "wb") as wav:
                    wav.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
                    wav.writeframes(b"\0\0" * (8000 * seconds))

        def run(mode, target, success=True, extra=()):
            command = [sys.executable, "-B", str(Path(__file__).with_name("build.py")), mode,
                       "--output", str(target), "--audio-root", str(audio), *extra]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            assert (result.returncode == 0) == success, result.stdout + result.stderr
            return result

        compiled = work / "compiled"
        run("compile", compiled)
        manifest = json.loads((compiled / "manifest.json").read_text())
        assert len(manifest["fragments"]) == 42 and not manifest["installable"]
        for record in manifest["fragments"]:
            content = (compiled / record["path"]).read_text()
            expected = 2 if record["language"] == "ru" else 27
            assert record["speech_seconds"] == expected
            assert expected < record["scene_seconds"] < expected + 2
            assert content.count("type=DEFORMABLE") == 1
            assert content.count("START_SOUND") == 1
            assert f"duration={expected}.0" in content
            assert 'type=SCENE' not in content and 'ATTACH_ENTITY' not in content
            assert 'REFERENCE' not in content and 'offscreen' not in content
            assert hashlib.sha256(content.encode()).hexdigest() == record["sha256"]
        for language in ("ru", "en"):
            xml = ElementTree.parse(compiled / f'subtitles/rm0001_{language}.xml')
            assert len(xml.getroot()) == 21
            ini = (compiled / f'DATA/AUDIO/rpg_rm0001_{language}.ini').read_text()
            assert ini.count("[Sound]") == 21

        previews = [work / "preview_a", work / "preview_b"]
        for folder in previews:
            run("preview", folder)
        for path in previews[0].rglob("*.thn"):
            content = path.read_bytes()
            assert content == (previews[1] / path.relative_to(previews[0])).read_bytes()
            assert b"START_SOUND" not in content and b"SILENT PREVIEW" in content

        # Missing WAV must fail before any partial scene or manifest is emitted.
        (audio / "rm0001/ru" / (line_name(spec["fragments"][0]) + ".wav")).unlink()
        run("compile", work / "missing", success=False)
        assert not (work / "missing").exists()

        for mutate in (lambda data: data["fragments"].append(data["fragments"][0]),
                       lambda data: data["choice_sets"]["main"].extend(["back", "leave"])):
            invalid = copy.deepcopy(spec)
            mutate(invalid)
            path = work / "invalid.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            try:
                load_spec(path)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid catalog accepted")

        # Test the same package that AudioFolder will use, without calling TTS.
        voice_output = work / "voices"
        run("voices", voice_output, extra=("--vendor-actor", "Hassler", "--dry-run"))
        plan = json.loads((voice_output / "voice_plan.json").read_text(encoding="utf-8"))
        assert plan["dry_run"]
        for lang, rows in plan["languages"].items():
            assert len(rows) == 21
            for fragment, row in zip(spec["fragments"], rows):
                assert row["actor"] == ("Trent" if fragment["role"] == "player" else "Hassler")
                assert Path(row["filename"]).name == line_name(fragment) + ".mp3"
                assert Path(row["filename"]).parent.name == "rm0001"
                assert row["text"] == fragment[lang]
        run("voices", work / "invalid_voice", success=False,
            extra=("--vendor-actor", "MissingActorClass", "--dry-run"))
        assert not (work / "invalid_voice").exists()

        from install_pythonlancer import patched_single, DISPATCH
        original = (DEFAULT_SOURCE / "single.py").read_bytes()
        patched = patched_single(original)
        assert patched_single(patched) == patched
        if b"# BEGIN RPG CUTSCENE DISPATCH" not in original:
            newline = b"\r\n" if b"\r\n" in original else b"\n"
            assert patched.replace(DISPATCH.encode().replace(b"\n", newline), b"", 1) == original

    print("PASS: real Pythonlancer Autoplay, 42 fragments, independent 2s/27s WAV timing, "
          "one actor/line per THN, deterministic silent preview, XML/INI, missing WAV and invalid graph, "
          "voice backend package/paths without TTS, idempotent single.py dispatch")
    print("Not tested: THN engine loading, room cameras/bindings, runtime Esc or mission/reputation effects")


if __name__ == "__main__":
    main()
