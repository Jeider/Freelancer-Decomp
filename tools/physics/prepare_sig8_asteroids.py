"""Prepare the Sig8 test preset + binaries in the workspace. Never write to the game."""
import hashlib
import json
from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
FIELDS = [f'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/sig8_ast{i}_asteroids.ini' for i in range(1, 6)]
ARCH = 'DATA/SOLAR/solararch.ini'
BINS = ['bin/'+name+ext for name, exts in [('Common', ['.dll', '.pdb']),
        ('Server', ['.dll', '.pdb']), ('freelancer', ['.exe', '.pdb'])] for ext in exts]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def convert_field(original_field):
    """Replace only dynamic settings; preserve all decorative settings and assets."""
    sections = re.split(rb'(?=^\[)', original_field, flags=re.M)
    changed = 0
    far_radii = {}
    for i, section in enumerate(sections):
        if section.startswith(b'[ServerDynamicAsteroids]'):
            assert re.search(rb'(?m)^asteroid\s*=\s*srv_ast_tau29_normal_[abc]\s*$', section)
            variant = re.search(rb'srv_ast_tau29_normal_([abc])', section).group(1).decode()
            key = b'placement_radius' if re.search(rb'(?m)^spawn_mode\s*=\s*forward\s*$', section) else b'despawn_radius'
            match = re.search(rb'(?m)^'+key+rb'\s*=\s*([0-9.]+)', section)
            far_radii[variant] = float(match.group(1)) if match else 3000
            sections[i] = b''
            continue
        if section.startswith(b'[DynamicAsteroids]'):
            assert re.search(rb'(?m)^asteroid\s*=\s*ast_tau29_normal_[abc]\s*$', section)
            section, n = re.subn(rb'(?m)^(count\s*=\s*)(?:30|0)(?=\s*$)', rb'\g<1>0', section)
            assert n == 1, 'Unexpected existing count; review preset before changing it'
            sections[i] = section
            changed += 1
    assert changed == 3
    field = b''.join(sections).replace(b'; Server-owned test population; count is total, not per camera.', b'')
    field = field.replace(b'; Server-owned population around player ships; overlapping players share rocks.', b'').rstrip()
    field += b'\r\n\r\n; Server-owned population around player ships; overlapping players share rocks.\r\n'
    for index, variant in enumerate('abc', 801):
        far_radius = far_radii.get(variant, 3000)
        assert 500 <= far_radius <= 100000
        section = f'''[ServerDynamicAsteroids]
asteroid = srv_ast_tau29_normal_{variant}
spawn_mode = forward
count = 60
placement_radius = {far_radius:g}
placement_offset = {far_radius*0.85:g}
despawn_radius = {far_radius*1.5:g}
max_velocity = 20
max_angular_velocity = 0.3
seed = {index}

'''
        field += section.replace('\n', '\r\n').encode('ascii')
    return field


def prepare():
    stage = ROOT/'src/obj/server_asteroids_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
    original_arch = (GAME/ARCH).read_bytes()
    upgrade = b'srv_ast_tau29_normal_' in original_arch
    if upgrade:
        for variant in 'abc':
            assert original_arch.count(f'nickname = srv_ast_tau29_normal_{variant}'.encode()) == 1
    configs = [(rel, convert_field((GAME/rel).read_bytes())) for rel in FIELDS]
    arch = original_arch.rstrip()+b'\r\n\r\n; Server-owned dynamic asteroids (Sig8 test preset).\r\n'
    for variant in 'abc':
        mesh = f'solar/asteroids_mod/tau29/ast_tau29_nrml_{variant}.3db'
        assert (GAME/'DATA'/mesh).is_file()
        assert (GAME/'DATA'/mesh).with_suffix('.sur').is_file()
        section = f'''[Solar]
nickname = srv_ast_tau29_normal_{variant}
ids_name = 60200
ids_info = 60200
type = SERVER_ASTEROID
DA_archetype = {mesh.replace('/', chr(92))}
material_library = solar\\asteroids_mod\\tau29\\ast_tau29.mat
explosion_arch = explosion_ast_tau29
mass = 400
hit_pts = 4000
destructible = true
LODranges = 0, 20000
distance_render = 6000

'''
        arch += section.replace('\n', '\r\n').encode('ascii')
    assert (GAME/'DATA/solar/asteroids_mod/tau29/ast_tau29.mat').is_file()
    binaries = ['bin/Server.dll', 'bin/Server.pdb', 'bin/freelancer.exe', 'bin/freelancer.pdb'] if upgrade else BINS
    for rel in binaries:
        (stage/rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, stage/rel)
    if not upgrade:
        configs.append((ARCH, arch))
    for rel, payload in configs:
        (stage/rel).parent.mkdir(parents=True, exist_ok=True)
        (stage/rel).write_bytes(payload)
    paths = binaries+[rel for rel, _ in configs]
    dependencies = ['bin/DALib.dll', 'bin/dacom.dll', 'bin/zlib.dll', 'bin/imeui.dll',
                    'bin/alchemy.dll', 'bin/RP9.dll',
                    'DATA/UNIVERSE/SYSTEMS_MOD/SIGMA8/sig8.ini']
    if upgrade:
        dependencies += ['bin/Common.dll', ARCH]
    manifest = {'game': str(GAME), 'files': [
        {'relative': rel, 'original': sha(GAME/rel), 'prepared': sha(stage/rel)} for rel in paths],
        'dependencies': [{'relative': rel, 'sha256': sha(GAME/rel)} for rel in dependencies]}
    (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    template = (ROOT/'tools/physics/install_server_asteroids.ps1').read_text(encoding='utf-8-sig')
    (stage/'install.ps1').write_text(template, encoding='utf-8-sig')
    print(stage)
    print(f'Prepared {len(paths)} files; distant forward formation in all five Sig8 fields. FarRocks/billboards unchanged. Game unchanged.')


if __name__ == '__main__':
    prepare()
