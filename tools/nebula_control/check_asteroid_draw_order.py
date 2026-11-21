"""Regression: keep local asteroid material after native fog cover, with real assets."""
import json
from pathlib import Path
import check_asteroid_mesh as probe

probe.OUT = probe.ROOT / 'out/graphics_settings/nebula_asteroid_mesh/fog_surface/draw_order'
probe.PROBE = probe.OUT / 'probe'
probe.EXTRA_DEFINES = ['/DASTEROID_OVERLAY_ORDER_CHECK']
probe.EXTRA_SOURCES = ['src/freelancer/Client/far_rocks.h',
                       'src/freelancer/Client/space_scene_obj_draw.cpp',
                       'tools/nebula_control/check_asteroid_mesh.py',
                       'tools/nebula_control/check_asteroid_mesh.cpp',
                       'tools/nebula_control/asteroid_draw_order_cases.inl',
                       'tools/nebula_control/check_asteroid_draw_order.py',
                       'tools/nebula_control/install_asteroid_draw_order.py']

def main():
    game=Path('D:/Games/FL_MOD')
    guarded=[game/'DATA_EXTRA/VOLUMETRIC/volumetric.ini',
             game/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini',
             game/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini',
             game/'Assets/Pythonlancer/universe/content/asteroid_definition.py']
    guarded += sorted((game/'DATA/SOLAR/NEBULA_MOD/GENERATED').glob('gen_om15_*_nebula.ini'))
    for name in ('nebula_volume.hlsl','nebula_volume.hlsli','nebula_composite.hlsl','far_rocks.hlsl'):
        for root in (probe.ROOT,game):guarded.append(root/'DATA_EXTRA/SHADERS'/name)
    guards={str(p):probe.digest(p) for p in guarded}
    draw=(probe.ROOT/'src/freelancer/Client/space_scene_obj_draw.cpp').read_text()
    body=draw[draw.index('    void DrainMeshAndAsteroids('):draw.index('    // DAT_00675240')]
    late=body.index('FarRocksPass::LocalObjects')
    assert body.count('FarRocksPass::LocalObjects')==1
    assert late>body.index('DrawFogOverlay(Cam)')
    assert late>body.rindex('CliAsteroidTickFields(Cam)')
    assert late<body.index('DrainBucket(Cam, 4, false)')
    assert body.count('FarRocksDrawAll(Camera, G_DrawCtxZFar, G_FieldEnclosure);')==2
    rocks=(probe.ROOT/'src/freelancer/Client/far_rocks.cpp').read_text()
    assert 'Far->P.bNebulaLocal && Visit->Enclosure != 0' in rocks
    assert 'LocalPass != (Visit->Pass == FarRocksPass::LocalObjects)' in rocks
    probe.main()
    assert guards=={str(p):probe.digest(p) for p in guarded}
    report_path=probe.OUT/'checks.json'
    report=json.loads(report_path.read_text())
    report.update(guards={**guards,**report['assets']},shader_changes=False,profile_changes=False,
                  scope='local meshes after native fog overlay; shaders/clouds unchanged',
                  limitations='Real native assets and mesh shader, controlled overlay; no complete game-scene capture')
    report_path.write_text(json.dumps(report,indent=2))
    print('PASS production schedule audit, native mesh materials and unchanged cloud/shader hashes')

if __name__=='__main__':main()
