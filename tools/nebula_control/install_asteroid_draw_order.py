"""Install the verified client-only asteroid draw-order correction."""
import json
import os
from pathlib import Path
import sys
import install_object_volume as installer

installer.OUT = installer.ROOT / 'out/graphics_settings/nebula_asteroid_mesh/fog_surface/draw_order'
installer.BUILD = installer.OUT / 'build'
installer.PLAN = installer.OUT / 'install.json'
installer.base.OUT, installer.base.BUILD = installer.OUT, installer.BUILD

if __name__ == '__main__':
    if '--apply' not in sys.argv:
        installer.prepare()
    else:
        installer.apply()
        # The original native MAT/3DBs stay in DATA; these are only extracted
        # texture copies owned by this regression probe.
        probe = installer.base.safe(installer.OUT / 'probe', installer.OUT)
        removed = 0
        for directory, children, files in os.walk(probe, followlinks=False):
            for child in children: installer.base.safe(Path(directory) / child, probe)
            for name in files:
                path = installer.base.safe(Path(directory) / name, probe)
                before = path.stat()
                assert path.stat().st_mtime_ns == before.st_mtime_ns
                path.unlink(); removed += before.st_size
        record = installer.OUT / 'installed.json'
        plan = json.loads(record.read_text())
        plan['removed_build_bytes'] += removed
        record.write_text(json.dumps(plan, indent=2))
        print(f'Removed remaining {removed} bytes of extracted probe assets; originals unchanged')
