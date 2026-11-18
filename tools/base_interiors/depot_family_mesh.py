"""Blender entry point for the shared depot mesher, with regional source roots."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from depot_family_audit import paths,REGIONS
from depot_relief_mesh import build

regions=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(REGIONS)
for region in regions:
    assert region in REGIONS,region
    print('REGION',region,flush=True)
    build(paths(region)[0])
