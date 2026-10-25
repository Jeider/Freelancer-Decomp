"""Stage the Health toolbar client and three new native glyphs; preserve existing art."""
import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
game = Path('D:/games/FL_MOD')
stage = repo / 'src/obj/health_controls/install'
glyphs = ['HUD_health_wing.3db', 'HUD_health_pause.3db', 'HUD_health_wing_lock.3db']
new_paths = ['DATA/INTERFACE/HUD/' + name for name in glyphs]
payloads = {name: repo / name for name in ('bin/freelancer.exe', 'bin/freelancer.pdb')}
for name, relative in zip(glyphs, new_paths):
    if (game / relative).exists():
        raise SystemExit('Existing artwork must be preserved: ' + relative)
    payloads[relative] = repo / 'src/obj/health_controls/icons' / name
digest = lambda blob: hashlib.sha256(blob).hexdigest().upper()
files = []
for relative, source in payloads.items():
    data = source.read_bytes()
    dest = stage / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    original = game / relative
    files.append(dict(relative=relative, original=digest(original.read_bytes()) if original.exists() else None,
                      prepared=digest(data)))
deps = ['DATA/INTERFACE/hud.ini', 'DATA/INTERFACE/HUD/HUD_health.3db',
        'DATA/INTERFACE/HUD/hud_target2.cmp', 'DATA/INTERFACE/interface.generic.vms',
        'DATA/INTERFACE/HUD/HUD_target_view3.3db', 'DATA/INTERFACE/HUD/HUD_target_view4.3db']
(stage / 'manifest.json').write_text(json.dumps(dict(game=str(game), files=files,
    dependencies=[dict(relative=name, sha256=digest((game / name).read_bytes())) for name in deps]), indent=2))
# Reuse the reviewed backup/hash/rollback installer with an explicit five-file allowlist.
script = (repo / 'tools/targeting_hud/install_health.ps1').read_text()
lines = script.splitlines()
lines[1] = "$repo = 'D:\\work\\Freelancer-Decomp'"
script = '\n'.join(lines).replace('src/obj/health_hud/install', 'src/obj/health_controls/install')
old_allowed = "@('bin/freelancer.exe', 'bin/freelancer.pdb', 'DATA/INTERFACE/HUD/HUD_health.3db', 'DATA/INTERFACE/hud.ini')"
allowed = '@(' + ', '.join("'" + name + "'" for name in payloads) + ')'
script = script.replace(old_allowed, allowed)
new_allowed = '@(' + ', '.join("'" + name + "'" for name in new_paths) + ')'
script = script.replace("$entry.relative -ne 'DATA/INTERFACE/HUD/HUD_health.3db'", '$entry.relative -notin ' + new_allowed)
script = script.replace('codex_health_hud_', 'codex_health_controls_').replace('Health HUD (four files)', 'Health controls (five files)')
(stage / 'install.ps1').write_text(script, encoding='utf-8-sig')
print('Staged client and three Health control glyphs:', stage)
