"""Stage RPG dialogue recording sheets and THN prototypes using Pythonlancer.

TTS is explicit through voices; no game installation or StoryMission registration.
Every fragment contains exactly one spoken line. Runtime integration is pending.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import wave
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path("D:/Games/FL_MOD/Assets/Pythonlancer")
LOCAL_SOURCE = Path(__file__).resolve().parents[1]
if (LOCAL_SOURCE / "templates/cutscenes").is_dir():
    DEFAULT_SOURCE = LOCAL_SOURCE


def load_spec(path):
    spec = json.loads(path.read_text(encoding="utf-8"))
    mission = spec["id"]
    if not re.fullmatch(r"rm[0-9]{4}", mission):
        raise ValueError("Expected rmNNNN group ID")
    ids = set()
    pools = {}
    for fragment in spec["fragments"]:
        name = fragment["id"]
        if not re.fullmatch(mission + r"_frag[0-9]{4}", name) or name in ids:
            raise ValueError(f"Invalid or duplicate fragment: {name}")
        ids.add(name)
        if fragment["role"] not in ("player", "vendor"):
            raise ValueError(f"Unknown role in {name}")
        if not all(fragment.get(lang, "").strip() for lang in ("ru", "en")):
            raise ValueError(f"Missing translation in {name}")
        pools.setdefault(fragment["pool"], set()).add(fragment["role"])
    for name, node in spec["nodes"].items():
        if pools.get(node["pool"]) != {"vendor"}:
            raise ValueError(f"Invalid vendor pool in {name}")
        if not node.get("terminal") and node.get("choices") not in spec["choice_sets"]:
            raise ValueError(f"Missing choices in {name}")
    for name, choices in spec["choice_sets"].items():
        if not 1 <= len(choices) <= 4 or len(set(choices)) != len(choices):
            raise ValueError(f"Invalid choice count in {name}")
        for key in choices:
            if key not in spec["choices"]:
                raise ValueError(f"Unknown choice {key}")
    for name, choice in spec["choices"].items():
        if pools.get(choice["pool"]) != {"player"}:
            raise ValueError(f"Choice {name} needs a separate spoken player fragment")
        targets = list(choice.get("outcomes", {}).values())
        if "goto" in choice:
            targets.append(choice["goto"])
        if not targets or any(target not in spec["nodes"] for target in targets):
            raise ValueError(f"Invalid transitions in {name}")
    if spec["start"] not in spec["nodes"] or spec["rules"]["first_greeting"] not in ids:
        raise ValueError("Invalid start/greeting")
    return spec


def line_name(fragment):
    return f'{fragment["id"]}_l001_{fragment["role"]}'


def write_text(output, relative, content):
    path = output / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def recordings(spec, output):
    for language in ("ru", "en"):
        sheet = io.StringIO(newline="")
        writer = csv.writer(sheet)
        writer.writerow(["fragment", "role", "pool", "filename", "text"])
        for fragment in spec["fragments"]:
            writer.writerow([fragment["id"], fragment["role"], fragment["pool"],
                             line_name(fragment) + ".wav", fragment[language]])
        write_text(output, f'recordings/{spec["id"]}/{language}/lines.csv', sheet.getvalue())
    write_text(output, "dialogue.design.json", json.dumps(spec, ensure_ascii=False, indent=2) + "\n")


def measure(path):
    # Read final PCM WAV assets, never infer production duration from text or MP3 size.
    with wave.open(str(path), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"Invalid WAV duration: {path}")
    return duration


def use_pythonlancer(source):
    os.chdir(source)
    sys.path.insert(0, str(source))
    sys.dont_write_bytecode = True
    # A staged tools.rpg_cutscenes entry may already have loaded a tools package
    # from the payload. Let its sibling imports resolve against the selected source.
    package = sys.modules.get("tools")
    if package is not None and str(source / "tools") not in package.__path__:
        package.__path__.append(str(source / "tools"))


def voice_package(spec, source, vendor_name):
    """Adapt the RPG catalog to AudioFolder's existing cutscene voice workflow."""
    use_pythonlancer(source)
    from audio.sound import VoiceLine, CutsceneSound
    from story import actors

    vendor = getattr(actors, vendor_name, None)
    if not isinstance(vendor, type) or not issubclass(vendor, actors.Actor) or not vendor.is_male():
        raise ValueError(f"Expected an existing male actor class from story/actors.py: {vendor_name}")

    class Package:
        def get_cutscene_folder(self):
            return spec["id"]

        def get_sounds(self):
            return [CutsceneSound(
                VoiceLine(1, actors.Trent if fragment["role"] == "player" else vendor,
                          ru=fragment["ru"], en=fragment["en"]),
                line_name(fragment), self) for fragment in spec["fragments"]]

    return Package()


def make_renderer(source):
    # Pythonlancer imports/templates depend on cwd. Imports are deliberately limited
    # to the reusable scene library; single.py executes a command on import.
    use_pythonlancer(source)
    from audio.sound import VoiceLine, CutsceneSound
    from story import actors
    from story.cutscenes.scene import Scene
    from story.cutscenes.content import (MAIN, BG, BG_GROUP, Character, Autoplay,
                                         SetCameraEvent, SoundEvent, MotionEvent)
    from story.cutscenes import sequence
    from managers.jinja_manager import JinjaTemplateManager

    templates = JinjaTemplateManager()

    class Vendor(actors.Actor):
        NAME = "vendor"
        TYPE = actors.ACTOR_MALE

    class Player(actors.Trent):
        NAME = "player"

    class BoundCharacter(Character):
        def __init__(self, root, actor, binding, duration):
            # Reuse Character.motion/facial and Autoplay, without Compound, Blender
            # points, costume spawning, or unused head/eye IK entities.
            self.root, self.actor = root, actor
            self.name = f"Char_{actor.NAME}"
            self.binding = binding
            self.camera = self
            self.sequence_step = 0
            self.facial_indexes = 1
            self.anim_sequence = copy.deepcopy(sequence.SEQUENCE_MALE_STAND_FSTHIPB[:1])
            self.sequence_len = len(self.anim_sequence)
            for step in self.anim_sequence:
                for motion in step:
                    motion["override_duration"] = duration
            root.add_entity(self)

        def set(self, group):
            SetCameraEvent(root=self.root, group=group, camera_name=self.root.camera_name)

        def get_thorn(self):
            # Requires strict existing-actor binding in the future RPG runtime.
            # REFERENCE is intentionally absent: SpawnDeformable rejects it.
            return ('{entity_name="' + self.name + '",type=DEFORMABLE,'
                    'template_name="",flags=LIT_DYNAMIC,lt_grp=0,srt_grp=0,'
                    'userprops={Actor="' + self.binding + '",category="Character"}}')

    class FragmentSound(CutsceneSound):
        def get_duration(self, russian=True):
            return self.measured_duration

        def get_nickname(self):
            return f"DX_{self.name}_{self.language}"

    class FragmentScene(Scene):
        def __init__(self, spec, fragment, language, duration, preview):
            self.tpl_manager = templates
            self.russian = language == "ru"
            self.start_time = 0
            self.entities, self.events, self.groups = {}, [], {}
            self.add_group(BG, group_type=BG_GROUP)
            self.add_group(MAIN)
            self.fragment = fragment
            # Camera segment availability must be verified for the actual room/spot.
            self.camera_name = "camera/PCU" if fragment["role"] == "player" else "camera/NCU"
            actor = Player if fragment["role"] == "player" else Vendor
            line = VoiceLine(1, actor, ru=fragment["ru"], en=fragment["en"])
            self.sound = FragmentSound(line, line_name(fragment), self)
            self.sound.measured_duration, self.sound.language = duration, language
            character = BoundCharacter(self, actor, spec["binding"][fragment["role"]], duration)
            self.get_group(MAIN).append_time(0.15)
            Autoplay(self, group=MAIN)
            # Upstream SoundEvent defaults to 20 seconds. Use actual sound length.
            for _, event in self.events:
                if isinstance(event, SoundEvent):
                    event.duration = duration
            # End in a known neutral pose; retain the generic facial tail (+1 sec).
            MotionEvent(root=self, group=MAIN, object_name=character.name,
                        anim="Sc_MLBODY_STND_IDLE_000LV_XB_04", duration=1,
                        loop=True, trans_time=0.25)
            self.get_group(MAIN).append_time(1)
            self.duration = self.get_group(MAIN).get_time()
            self.preview = preview
            if preview:
                self.events = [(t, event) for t, event in self.events if not isinstance(event, SoundEvent)]

        def lookup_multiple_sounds(self, start, end):
            return [self.sound]

        def lookup_single_sound(self, index):
            return self.sound

        def get_content(self):
            camera = ('{entity_name="' + self.camera_name + '",type=CAMERA,template_name="",'
                      'spatialprops={pos={0,0,0},orient={{1,0,0},{0,1,0},{0,0,1}}},'
                      'cameraprops={fovh=30,hvaspect=1.333333,nearplane=0.1,farplane=10000}}')
            entities = ['{entity_name="Monitor_1",type=MONITOR,template_name=""}', camera]
            entities += [entity.get_thorn() for entity in self.entities.values()]
            if not self.preview:
                entities.append(self.sound.get_thorn())
            events = [event.get_thorn(time) for time, event in sorted(self.events, key=lambda item: item[0])]
            warning = "SILENT PREVIEW: estimated timing" if self.preview else "WAV-timed asset prototype"
            return (f"-- {warning}; RPG binding/fragment runtime integration required\n"
                    f"duration={self.duration:.6f}\nentities={{\n" + ",\n".join(entities) +
                    "\n}\nevents={\n" + ",\n".join(events) + "\n}\n")

    return FragmentScene


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "preview", "compile", "voices"])
    parser.add_argument("--group", default="rm0001", help="RPG group, e.g. rm0001")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--pythonlancer", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, help="Default: Pythonlancer/results/rpg/<group>/<command>/<language>")
    parser.add_argument("--audio-root", type=Path, help="Optional WAV root: <root>/rm0001/{ru,en}/*.wav; otherwise game DATA/AUDIO/MOD[_ENG]")
    parser.add_argument("--language", choices=["ru", "en", "both"], default="both")
    parser.add_argument("--vendor-actor", help="For voices: male actor class in story/actors.py; player always uses Trent")
    parser.add_argument("--dry-run", action="store_true", help="For voices: export the plan without calling a voice backend")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"rm[0-9]{4}", args.group):
        parser.error("--group must be rmNNNN")
    source = args.pythonlancer.resolve()
    adjacent = Path(__file__).with_name(args.group + ".json")
    spec_path = args.spec or (adjacent if adjacent.exists() else source / "story/rpg" / (args.group + ".json"))
    spec = load_spec(spec_path.resolve())
    output = (args.output or source / "results/rpg" / spec["id"] / args.command / args.language).resolve()
    languages = ("ru", "en") if args.language == "both" else (args.language,)
    audio_root = args.audio_root.resolve() if args.audio_root else None
    result_root = (source / "results/rpg").resolve()
    if (output == source or source in output.parents) and not output.is_relative_to(result_root):
        parser.error("Inside Pythonlancer, stage only under results/rpg")
    if args.dry_run and args.command != "voices":
        parser.error("--dry-run is only supported for voices")
    if args.command == "voices":
        if not args.vendor_actor:
            parser.error("voices requires --vendor-actor (class name in story/actors.py)")
        package = voice_package(spec, source, args.vendor_actor)
        plan = {"group": spec["id"], "vendor_actor": args.vendor_actor, "player_actor": "Trent",
                "dry_run": args.dry_run, "languages": {}}
        for language in languages:
            destination = source.parent / ("AUDIO_CUTSCENE_RU" if language == "ru" else "AUDIO_CUTSCENE_EN") / spec["id"]
            plan["languages"][language] = [{"filename": str(destination / (sound.name + ".mp3")),
                "actor": sound.line.actor.__name__, "text": sound.line.ru if language == "ru" else sound.line.en}
                for sound in package.get_sounds()]
        recordings(spec, output)
        write_text(output, "voice_plan.json", json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
        if not args.dry_run:
            from tools.audio_folder import AudioFolder
            for language in languages:
                AudioFolder.generate_cutscene_sounds(package, russian=language == "ru")
        print(f'{spec["id"]}: voice {"plan only" if args.dry_run else "generation complete"}; {output}')
        return
    jobs = []
    if args.command != "prepare":
        for language in languages:
            for fragment in spec["fragments"]:
                directory = (audio_root / spec["id"] / language if audio_root else
                             source.parent.parent / "DATA/AUDIO" / ("MOD" if language == "ru" else "MOD_ENG") / spec["id"])
                path = directory / (line_name(fragment) + ".wav")
                duration = (max(1.0, len(fragment[language].split()) / 2.4)
                            if args.command == "preview" else measure(path))
                jobs.append((fragment, language, duration, path))
    # Complete input validation and in-memory rendering before writing any outputs.
    rendered = []
    if jobs:
        renderer = make_renderer(source)
        for fragment, language, duration, path in jobs:
            scene = renderer(spec, fragment, language, duration, args.command == "preview")
            rendered.append((fragment, language, duration, path, scene, scene.get_content()))
    recordings(spec, output)
    manifest = {"schema": 1, "group": spec["id"], "mode": args.command,
                "runtime_integration_required": True, "installable": False, "fragments": []}
    for fragment, language, duration, path, scene, content in rendered:
        relative = f'DATA/SCRIPTS/RPG/{spec["id"]}/{language}/{fragment["id"]}.thn'
        write_text(output, relative, content)
        manifest["fragments"].append({"id": fragment["id"], "language": language,
            "path": relative, "role": fragment["role"], "pool": fragment["pool"],
            "speech_seconds": duration, "scene_seconds": scene.duration,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "wav_sha256": hashlib.sha256(path.read_bytes()).hexdigest() if args.command == "compile" else None})
    if args.command == "compile":
        for language in languages:
            folder = "MOD" if language == "ru" else "MOD_ENG"
            sounds, subtitles = [], []
            for fragment, lang, _, path, scene, _ in rendered:
                if lang != language:
                    continue
                filename = path.name
                relative = f"{folder}\\{spec['id']}\\{filename}"
                sounds.append(f"[Sound]\nnickname = {scene.sound.get_nickname()}\ntype = voice\n"
                              f"attenuation = 0\nfile = audio\\{relative}\nis_2d = true\n")
                subtitles.append(f'<Static AudioFile="{relative}" TextArea="Cinematic">'
                                 f'{escape(fragment[language])}</Static>')
            write_text(output, f'DATA/AUDIO/rpg_{spec["id"]}_{language}.ini', "\n".join(sounds))
            write_text(output, f'subtitles/{spec["id"]}_{language}.xml',
                       '<?xml version="1.0" encoding="UTF-8"?>\n<Subtitles>\n' +
                       "\n".join(subtitles) + "\n</Subtitles>\n")
    write_text(output, "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f'{spec["id"]}: {len(spec["fragments"])} recording lines per language, '
          f'{len(rendered)} THN files; mode={args.command}; runtime integration pending')


if __name__ == "__main__":
    main()
