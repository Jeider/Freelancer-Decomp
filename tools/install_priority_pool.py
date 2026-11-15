"""Install the checked Common build; retain one DLL rollback, no DATA generation."""
import hashlib,json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/priority_pool'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    raise RuntimeError('Withdrawn: this experimental limit check did not resolve the Tau4 crash. Do not reinstall.')
    result=subprocess.run(['tasklist','/FI','IMAGENAME eq freelancer.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=True)
    assert 'freelancer.exe' not in result.stdout.lower(),'Close Freelancer before replacing Common.dll'
    source=ROOT/'src/obj/train_courier/rpg1/bin'
    target=GAME/'bin'
    assert (OUT/'check.exe').exists()
    subprocess.run([str(OUT/'check.exe')],check=True,timeout=45)
    backup=OUT/'Common.before.dll'
    assert not backup.exists(),'One rollback already exists; inspect prior installation'
    before=sha(target/'Common.dll')
    shutil.copy2(target/'Common.dll',backup)
    for name in ('Common.dll','Common.pdb'):
        shutil.copy2(source/name,target/name)
        assert sha(source/name)==sha(target/name)
    (OUT/'installed.json').write_text(json.dumps(dict(before=before,after=sha(target/'Common.dll'),rollback=str(backup)),indent=2))
    print('Installed Common.dll and matching PDB in game bin; one DLL rollback retained. Pythonlancer not run.')
if __name__=='__main__':main()
