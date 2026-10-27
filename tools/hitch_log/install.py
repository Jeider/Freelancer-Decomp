"""Install hitch logging, navmap correction and greenhouse shader with verified backups."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'room_materials'))
import install
install.FIXED+=tuple('bin/'+name+ext for name in ('Common','SoundManager','SoundStreamer') for ext in ('.dll','.pdb'))
install.main()
