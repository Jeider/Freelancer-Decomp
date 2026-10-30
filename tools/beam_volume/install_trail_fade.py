"""Install near-camera trail fading for lightweight ALE ribbons; preserve game settings."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'tools/nomad_surfaces'))
import install as deployment

deployment.STAGE = root / 'src/obj/beam_volume/trail_fade_install'
deployment.PAYLOAD = ('bin/alchemy.dll', 'bin/alchemy.pdb')
deployment.SCOPE = 'Camera-facing ALE trail vertex fade using existing beam_volume_trail_nodes/fade controls; no configuration changes'

if __name__ == '__main__':
    deployment.main()
