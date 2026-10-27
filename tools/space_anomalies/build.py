"""Build and render the standalone lab; never installs files into the game.

Uses the existing Windows/MSVC + June 2010 DirectX SDK. No Python packages needed.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "src/obj/space_anomalies"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", choices=("realistic", "theatrical"), default="realistic")
    parser.add_argument("--quality", choices=("ultra", "epic"), default="epic")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preset", type=int, default=-1, help="0..7 or -1 for all")
    parser.add_argument("--time-offset", type=float, default=0)
    parser.add_argument("--yaw-offset", type=float, default=0)
    parser.add_argument("--flare", type=float, default=-1)
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument("--step", type=float, default=0.1)
    parser.add_argument("--checks", action="store_true", help="also render time/orbit changes, repeatability and magnetar flare")
    parser.add_argument("--append-log", action="store_true", help="preserve earlier results when updating one preset")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    realistic=args.style=="realistic"
    OUT=BASE/"realistic" if realistic else BASE
    args.width=args.width or (3840 if realistic else 1600)
    args.height=args.height or (2160 if realistic else 900)
    args.output=args.output or OUT/"renders"
    OUT.mkdir(parents=True, exist_ok=True)
    executable = OUT / "render.exe"
    recipe={"style":args.style,"quality":args.quality}
    recipe_path=OUT/"build_recipe.json"
    if args.no_build and (not recipe_path.exists() or json.loads(recipe_path.read_text())!=recipe):
        raise SystemExit("This executable was not built for the selected style/quality. Build explicitly when compilation is authorized.")
    if not args.no_build:
        presets = json.loads((Path(__file__).with_name("presets.realistic.json" if realistic else "presets.json")).read_text(encoding="utf-8"))
        rows = []
        for p in presets:
            values = [json.dumps(p["id"]), json.dumps(p["shader"]), str(p["variant"])]
            values += [f"{float(p[k])}f" for k in ("time", "inclination", "yaw", "exposure", "distance", "flare")]
            values.append(f"{float(p.get('sensor',0))}f")
            rows.append("    {" + ",".join(values) + "}")
        settings=f"static constexpr bool Realistic={'true' if realistic else 'false'};\nstatic constexpr int EpicQuality={2 if args.quality=='epic' else 1};\n"
        (OUT / "presets.generated.h").write_text(settings+"static const Preset Presets[] = {\n" + ",\n".join(rows) + "\n};\n", encoding="utf-8")
        candidates = sorted(Path("C:/Program Files/Microsoft Visual Studio").glob("*/Community/VC/Tools/MSVC/*"))
        vc = Path(os.environ["ANOMALIES_MSVC"]) if "ANOMALIES_MSVC" in os.environ else candidates[-1]
        sdk = Path(os.environ.get("ANOMALIES_WINSDK", "C:/Program Files (x86)/Windows Kits/10"))
        version = sorted(p.name for p in (sdk / "Include").iterdir() if (p / "um/Windows.h").exists())[-1]
        dx = Path(os.environ.get("DXSDK_DIR", "C:/DXSDK_Jun10"))
        env = os.environ.copy()
        env["INCLUDE"] = ";".join(map(str, [vc / "include", sdk / f"Include/{version}/ucrt", sdk / f"Include/{version}/shared", sdk / f"Include/{version}/um", dx / "Include", OUT]))
        env["LIB"] = ";".join(map(str, [vc / "lib/x86", sdk / f"Lib/{version}/ucrt/x86", sdk / f"Lib/{version}/um/x86"]))
        dll = ROOT / "bin/d3dx9_43.dll"
        if dll.exists():
            shutil.copy2(dll, OUT / dll.name)
        subprocess.run([str(vc / "bin/Hostx64/x86/cl.exe"), "/nologo", "/O2", "/std:c++17", "/W3", "/EHsc", "/MT", str(Path(__file__).with_name("render.cpp")), f"/Fe{executable}", "/link", "user32.lib", "d3d9.lib", str(dx / "Lib/x86/d3dx9.lib")], cwd=OUT, env=env, check=True)
        recipe_path.write_text(json.dumps(recipe,indent=2),encoding="utf8")
    if args.build_only:
        return
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    render_env=os.environ.copy()
    render_env['FREELANCER_SHADER_CACHE_DIR']=str(OUT/'shader_cache')
    with (args.output / "render.log").open("ab" if args.append_log else "wb") as log:
        result = subprocess.run([str(executable), str(args.output), str(args.width), str(args.height), str(args.preset), str(args.time_offset), str(args.yaw_offset), str(args.flare), str(args.frames), str(args.step), str(int(args.checks))], cwd=ROOT, env=render_env, stdout=log, stderr=subprocess.STDOUT)
    print((args.output/'render.log').read_text(encoding='utf8',errors='replace'),end='')
    result.check_returncode()


if __name__ == "__main__":
    main()
