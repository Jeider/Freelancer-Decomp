"""Install the checked object-material trial; no cloud/config/ship deployment."""
import sys
import json
import re
import install_asteroid_fog as installer

installer.OUT=installer.ROOT/'out/graphics_settings/nebula_asteroid_mesh/surface_scatter'
installer.BUILD=installer.OUT/'build'
installer.PLAN=installer.OUT/'install.json'
installer.base.OUT,installer.base.BUILD=installer.OUT,installer.BUILD
installer.SHADERS=['far_rocks.hlsl','surface_material.hlsl']
installer.REPORTS=('checks.json',)
installer.SCOPE='Omega-15 medium/high model scatter; decorative meshes to 6 km with complete dynamic/billboard exclusions'
installer.FILES={**{'bin/'+name:installer.BUILD/'bin'/name for name in ('freelancer.exe','freelancer.pdb')},
    **{'DATA_EXTRA/SHADERS/'+name:installer.ROOT/'DATA_EXTRA/SHADERS'/name for name in installer.SHADERS}}

def apply():
    installer.base.idle()
    plan=json.loads(installer.PLAN.read_text())
    assert installer.base.digest(installer.OUT/'checks.json')==plan['checks']['checks.json']
    for name,expected in plan['sources'].items():
        assert installer.base.digest(installer.ROOT/name)==expected,name
    checks=json.loads((installer.OUT/'checks.json').read_text())
    assert installer.base.digest(installer.OUT/'surfaces/checks.json')==checks['surface_checks']
    surface=json.loads((installer.OUT/'surfaces/checks.json').read_text())
    verified={}
    for folder,files in ((installer.OUT/'probe/cache',checks['cache_files']),
                         (installer.OUT/'surfaces/probe/manifest_cache',surface['cache_files'])):
        for name,digest in files.items():
            assert re.fullmatch('[0-9a-f]{64}\\.bin',name)
            path=installer.base.safe(folder/name,installer.OUT)
            assert installer.base.digest(path)==digest,path
            verified[name]=(path.read_bytes(),digest)
    cache=installer.base.safe(installer.base.cache_path(),installer.base.cache_path())
    cache.mkdir(parents=True,exist_ok=True)
    created=[]
    try:
        for name,(data,digest) in verified.items():
            target=installer.base.safe(cache/name,cache)
            if not target.exists():
                with target.open('xb') as out:out.write(data)
                created.append((target,digest))
            assert installer.base.digest(target)==digest,target
        installer.apply()
    except BaseException:
        for target,digest in created:
            installer.base.safe(target,cache)
            assert installer.base.digest(target)==digest
            target.unlink()
        raise
    record=installer.OUT/'installed.json';installed=json.loads(record.read_text())
    installed['verified_shader_cache_entries']=len(verified)
    installed['new_shader_cache_entries']=len(created)
    record.write_text(json.dumps(installed,indent=2))
    print(f'Warmed {len(verified)} verified shader entries; existing cache preserved')

if __name__=='__main__':
    apply() if '--apply' in sys.argv else installer.prepare()
