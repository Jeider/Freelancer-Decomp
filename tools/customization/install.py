"""Install checked customization binaries into FL_MOD/bin with hashes and rollback."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_courier'))
import install_local_triggers as installer
installer.__doc__=__doc__
installer.OUT=ROOT/'out/customization'
installer.NAMES=('Common.dll','Common.pdb','Server.dll','Server.pdb','freelancer.exe','freelancer.pdb')
if __name__=='__main__': installer.main()
