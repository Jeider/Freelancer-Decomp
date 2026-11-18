"""Apply the separately GPU-verified dgVoodoo VRAM budget; retain all other game settings."""
import hashlib
import json
from pathlib import Path
import install_animation as base

OUT=base.OUT/'shadows'


def main():
    base.idle()
    report=json.loads((OUT/'verified.json').read_text())
    for path,expected in report['sources'].items():
        assert base.digest(Path(path))==expected,'Test source changed: '+path
    assert base.digest(base.GAME/'D3D9.dll')==report['provider'],'D3D9 provider changed'
    target=base.safe(base.GAME/'dgVoodoo.conf',base.GAME)
    previous=target.read_bytes()
    assert hashlib.sha256(previous).hexdigest()==report['before'],'Game settings changed after test'
    proposed=(OUT/'dgVoodoo.proposed.conf').read_bytes()
    assert hashlib.sha256(proposed).hexdigest()==report['after'],'Candidate changed after test'
    try:
        target.write_bytes(proposed)
        assert base.digest(target)==report['after'],'Installed settings failed verification'
    except BaseException:
        target.write_bytes(previous)
        raise
    for name in ('D3D9.dll','probe.exe','check_shadow_budget.obj','dgVoodoo.conf','dgVoodoo.proposed.conf'):
        path=base.safe(OUT/name,OUT)
        if path.exists():path.unlink()
    report['installed_path']=str(target)
    (OUT/'installed.json').write_text(json.dumps(report,indent=2))
    print('Installed and hash-verified: DirectX VRAM 256 -> 4096 MiB; other settings unchanged; probe binaries cleaned')


if __name__=='__main__':main()
