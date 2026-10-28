"""Build an audited Medium replacement pack for asteroid models; never install it."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from refine import REPO, leaves, decode, refine, pack_mesh, write_model, render


def profile(name):
    if name.startswith(("debris", "mine_", "dummy_", "ast_loot", "ast_belt")):
        return None
    if any(tag in name for tag in ("icecrystal", "ice_spike", "ice_block", "beryl")):
        return "faceted", 0.08, 0.012, True
    if "nomad" in name:
        return "nomad", 0.08, 0.012, True
    if "ice" in name:
        return "ice", 0.20, 0.02, False
    return "rock", 0.35, 0.045, False


def ini_sections(path):
    raw = path.read_bytes()
    if raw.startswith(b"BINI"):
        raise ValueError("BINI requires a separate reader")
    text = raw.decode("utf-8-sig", errors="replace")
    section, entries = "", []
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.startswith("[") and "]" in line:
            if section: yield section, entries
            section, entries = line[1:line.index("]")].lower(), []
        elif "=" in line:
            key, value = line.split("=", 1)
            entries.append((key.strip().lower(), value.strip()))
    if section: yield section, entries


def field_budgets(game, replacements):
    arches = collections.defaultdict(set)
    for source in sorted((game/"DATA/SOLAR").glob("*asteroidarch*.ini")):
        for section, entries in ini_sections(source):
            values = dict(entries)
            if section in ("asteroid", "asteroidmine") and "nickname" in values and "da_archetype" in values:
                arches[values["nickname"].lower()].add(values["da_archetype"].replace("\\", "/").lower())
    cache = {}
    def count(model):
        name = Path(model).name
        if name in replacements: return replacements[name]
        if model not in cache:
            data = (game/"DATA"/model).read_bytes()
            # Conservative upper bound for unchanged multi-mesh debris.
            cache[model] = sum(struct.unpack_from("<II4H", b)[-1] for p, _, b in leaves(data)[1]
                               if p.lower().endswith("/vmeshdata"))
        return cache[model]
    rows = []
    for directory in ("ASTEROIDS", "ASTEROIDS_MOD"):
        for path in sorted((game/"DATA/SOLAR"/directory).rglob("*.ini")):
            total, unknown, entries_found = 0, [], 0
            try:
                for section, entries in ini_sections(path):
                    if section != "cube": continue
                    for key, value in entries:
                        if key != "asteroid": continue
                        entries_found += 1
                        nickname = value.split(",", 1)[0].strip().lower()
                        options = arches.get(nickname, ())
                        if len(options) != 1:
                            unknown.append(nickname); continue
                        try: total += count(next(iter(options)))
                        except (OSError, ValueError): unknown.append(nickname)
                if entries_found:
                    rows.append({"field": str(path.relative_to(game)), "instances": entries_found,
                                 "vertices_upper_bound": total, "unresolved": sorted(set(unknown)),
                                 "within_16bit_limit": None if unknown else total <= 65535})
            except ValueError as e:
                rows.append({"field": str(path.relative_to(game)), "error": str(e)})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", type=Path)
    parser.add_argument("--output", type=Path, default=REPO/"src/obj/procedural_asteroids/retail_medium")
    parser.add_argument("--budget", type=int, default=1280)
    args = parser.parse_args()
    source_root, output = args.models.resolve(), args.output.resolve()
    allowed = (REPO/"src/obj/procedural_asteroids").resolve()
    if not output.is_relative_to(allowed) or source_root.is_relative_to(output):
        raise ValueError("Output must stay in the workspace staging area, separate from the source")
    if not 512 <= args.budget <= 4096:
        raise ValueError("Budget outside Medium limits")
    paths = sorted(source_root.glob("*.3db"))
    if not paths: raise ValueError("No models")
    inputs = {path: path.read_bytes() for path in paths}
    target = output/"DATA/SOLAR/ASTEROIDS/MODELS"
    target.mkdir(parents=True, exist_ok=True)
    manifest = {"source": str(source_root), "scope": "Asteroids in this installation, not authenticated against a pristine retail archive",
                "maximum_triangles_per_model": args.budget, "files": [], "unchanged": [], "errors": [],
                "collision": "Original SUR retained; changed surfaces require live clearance review.",
                "installed": False}
    thumbs = []
    for path, original in inputs.items():
        settings = profile(path.stem.lower())
        if settings is None:
            manifest["unchanged"].append({"name": path.name, "reason": "Debris, mine, loot or belt, not an asteroid"})
            continue
        try:
            category, smooth, relief, hard = settings
            blobs = [b for n, _, b in leaves(original)[1] if n.lower().endswith("/vmeshdata")]
            if len(blobs) != 1: raise ValueError("Expected one mesh")
            h, d, vertices, faces = decode(blobs[0])
            levels = min(2, max(0, int(math.log(args.budget/len(faces), 4))))
            if levels == 0: raise ValueError("Source already too large for Medium subdivision")
            # Match the reviewed rock60 relief; scale siblings get matching patterns.
            seed = 6028
            for strength in (1, 0.5, 0.25, 0.125, 0.0625):
                try:
                    corners, metrics = refine(vertices, faces, levels, seed, smooth*strength, relief*strength,
                                              0.06, allow_open=True, preserve_shading=hard)
                    break
                except ValueError as error:
                    if "folded" not in str(error): raise
            else: raise ValueError("Could not produce an unfolded surface")
            blob = pack_mesh(h, d, vertices, corners)
            private_name = f"procedural_{path.stem}_{hashlib.sha256(blob).hexdigest()[:12]}_medium-{h[4]:x}.vms"
            checksum = write_model(original, blob, private_name, target/path.name)
            metrics.update(name=path.name, profile=category, original_triangles=len(faces),
                           subdivisions=levels, strength_multiplier=strength,
                           smooth=smooth*strength, relief=relief*strength, seed=seed,
                           vertex_colors=bool(h[4]&0x40), uv_channels=(h[4]>>8)&15,
                           render_vertices=decode(blob)[0][-1],
                           original_sha256=hashlib.sha256(original).hexdigest(), prepared_sha256=checksum,
                           relative=f"DATA/SOLAR/ASTEROIDS/MODELS/{path.name}")
            manifest["files"].append(metrics)
            center = (vertices[:, :3].min(axis=0)+vertices[:, :3].max(axis=0))/2
            radius = np.linalg.norm(vertices[:, :3]-center, axis=1).max()
            thumbs.append((path.stem, len(faces), len(corners)//3,
                           render(vertices[faces.flat], center, radius, .65, 210),
                           render(corners, center, radius, .65, 210)))
        except Exception as error:
            manifest["errors"].append({"name": path.name, "error": str(error)})
        if len(manifest["files"]) % 20 == 0:
            print(f'Prepared {len(manifest["files"])} models', flush=True)
    replacements = {item["name"].lower(): item["render_vertices"] for item in manifest["files"]}
    manifest["field_budgets"] = field_budgets(source_root.parents[3], replacements)
    for path, original in inputs.items():
        if path.read_bytes() != original:
            raise ValueError(f"Source changed during preparation: {path}")
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
    small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    for page in range((len(thumbs)+23)//24):
        sheet = Image.new("RGB", (1260, 8*260+40), (24, 29, 37))
        draw = ImageDraw.Draw(sheet)
        draw.text((15, 8), "ORIGINAL / MEDIUM   |   same camera, scale and lighting; no textures", fill=(231, 235, 240), font=font)
        for j, (name, before, after, left, right) in enumerate(thumbs[page*24:(page+1)*24]):
            x, y = (j%3)*420, 40+(j//3)*260
            draw.text((x+10, y+5), name, fill=(225, 230, 236), font=font)
            draw.text((x+10, y+29), f"{before} -> {after} triangles", fill=(151, 164, 181), font=small)
            sheet.paste(left, (x, y+50)); sheet.paste(right, (x+210, y+50))
        sheet.save(output/f"review_{page+1:02}.jpg", quality=92)
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    summary = {"prepared": len(manifest["files"]), "unchanged_non_asteroids": len(manifest["unchanged"]),
               "errors": manifest["errors"], "profiles": dict(collections.Counter(f["profile"] for f in manifest["files"])),
               "max_output_triangles": max(f["triangles"] for f in manifest["files"]),
               "fields_scanned": len(manifest["field_budgets"]),
               "field_overflow": [f for f in manifest["field_budgets"] if f.get("within_16bit_limit") is False],
               "unresolved_fields": sum(bool(f.get("unresolved") or f.get("error")) for f in manifest["field_budgets"])}
    summary["maximum_verified_field_vertices"] = max(
        (f.get("vertices_upper_bound", 0) for f in manifest["field_budgets"] if f.get("within_16bit_limit") is True), default=0)
    (output/"summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if manifest["errors"] or summary["field_overflow"]:
        raise SystemExit(1)
    import zipfile
    with zipfile.ZipFile(output/"asteroids_medium.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for item in manifest["files"]:
            archive.write(output/item["relative"], item["relative"])
        archive.write(output/"manifest.json", "manifest.json")
        archive.write(output/"summary.json", "summary.json")
        archive.write(Path(__file__).with_name("README.txt"), "README.txt")


if __name__ == "__main__":
    main()
