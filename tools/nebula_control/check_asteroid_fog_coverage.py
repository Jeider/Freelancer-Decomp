"""Pixel fog on actual asteroid meshes and the RP9 native/enhanced routes."""
import json
import check_surface_scatter as scatter
import check_asteroid_spawn as spawn

ROOT=scatter.mesh.ROOT
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Reuse authored exclusion fixtures and cloud/content immutability checks.
    original_mesh=scatter.mesh.main
    original_surface=scatter.surface.main
    sources=['src/RP9/RP9SurfaceFade.h','src/RP9/RP9ShaderManifest.h',
        'src/freelancer/Client/server_asteroid_fade.h',
        *['tools/nebula_control/'+name for name in ('check_asteroid_fog_coverage.py',
        'asteroid_fog_coverage_cases.inl','asteroid_spawn_cases.inl','check_asteroid_spawn.py',
        'install_asteroid_fog_coverage.py')]]
    before={name:scatter.mesh.digest(ROOT/name) for name in sources}
    def mesh_check():
        scatter.mesh.EXTRA_DEFINES+=['/DASTEROID_FOG_COVERAGE_CHECK']
        scatter.mesh.EXTRA_SOURCES+=sources
        original_mesh()
    def surface_check():
        scatter.surface.EXTRA_DEFINES+=['/DASTEROID_SPAWN_CHECK','/DASTEROID_FOG_COVERAGE_CHECK']
        original_surface()
    scatter.mesh.main=mesh_check;scatter.surface.main=surface_check
    scatter.OUT=OUT;spawn.OUT=OUT;spawn.submit_check()
    scatter.main()
    assert before=={name:scatter.mesh.digest(ROOT/name) for name in sources}
    path=OUT/'checks.json';report=json.loads(path.read_text())
    report['scope']='Omega-15 medium/high asteroid pixel fog, combined with birth/range fades; unchanged nebula and low settings'
    path.write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
