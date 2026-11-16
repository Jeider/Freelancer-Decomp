"""Stage/apply checked Content.dll only for server-wide NPC scaling."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/train_courier'))
import install_local_triggers as installer

installer.__doc__ = __doc__
installer.OUT = ROOT/'out/npc_scaling'

if __name__ == '__main__': installer.main()
