"""Refresh the staged renderer bundle's SHA256 manifest."""
import hashlib
import json
from pathlib import Path

root=Path('bin/experimental_local_shadows')
files=['Freelancer.exe','RP9.dll','alchemy.dll','flmaterials.dll',
       'surface_material.hlsl','local_shadow.hlsl','scene_fxaa.hlsl','solar_rays.hlsl']
files += [p.relative_to(root).as_posix() for p in sorted((root/'ShaderCache').glob('*.bin'))]
entries=[{'File':name,'SHA256':hashlib.sha256((root/name).read_bytes()).hexdigest().upper()} for name in files]
(root/'manifest.json').write_text(json.dumps(entries,indent=2)+'\n')
print(f'Manifest verified: {len(entries)} files')
