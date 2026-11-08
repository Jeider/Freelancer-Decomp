"""Stage/install the checked HUD marker client using the shared EXE/PDB installer."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/rpg_contacts'))
import install_client

# The train client build retains the coupling HUD and FreelancerRpgWorld=1.
# The shared installer verifies that flag, live DLL dependencies, staged hashes,
# process shutdown, backups and rollback. No model or game INI is changed.
install_client.BUILD = ROOT/'src/obj/train_yard/freelancer'
install_client.OUT = ROOT/'src/obj/hud_geometry/install'

if __name__ == '__main__':
    install_client.main()
