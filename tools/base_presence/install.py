"""Install checked Server/client only, preserving Content, Common and game DATA."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_courier'))
import install_local_triggers as installer

installer.__doc__=__doc__
installer.OUT=ROOT/'out/base_presence'
installer.NAMES=('Server.dll','Server.pdb','freelancer.exe','freelancer.pdb')

if __name__=='__main__':installer.main()
