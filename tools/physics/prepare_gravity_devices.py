"""Stage dedicated hardware, repair toggle and normal DATA/EQUIPMENT content."""
from pathlib import Path
from datetime import datetime
import hashlib, json, re, shutil, sys
root=Path(__file__).resolve().parents[2]
game=Path('D:/games/FL_MOD')
stage=root/'src/obj/gravity_devices_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
stage.mkdir(parents=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
files=[]
common_only='--common-only' in sys.argv
binaries_only='--binaries-only' in sys.argv
obsolete='DATA_EXTRA/EQUIPMENT/gravity_devices.ini'
for relative in ('bin/Common.dll','bin/Common.pdb','bin/Server.dll','bin/Server.pdb',
                 'bin/freelancer.exe','bin/freelancer.pdb','DATA/EQUIPMENT/gravity_devices.ini',
                 'DATA/EQUIPMENT/repair_devices.ini','bin/freelancer.ini',obsolete):
    if common_only and relative not in ('bin/Common.dll','bin/Common.pdb'): continue
    if binaries_only and (not relative.startswith('bin/') or relative.endswith('.ini')): continue
    target=stage/relative
    if relative==obsolete:
        files.append(dict(relative=relative,original=digest(game/relative),prepared=None,delete=True));continue
    target.parent.mkdir(parents=True,exist_ok=True)
    if relative=='bin/freelancer.ini':
        data=(game/relative).read_bytes()
        data=re.sub(rb'(?mi)^[ \t]*equipment[ \t]*=[ \t]*(?:\.\.\\DATA_EXTRA\\)?EQUIPMENT\\(?:gravity_devices|repair_devices)\.ini[^\r\n]*(?:\r?\n|$)',b'',data)
        section=re.search(rb'(?mi)^\[Data\][ \t]*\r?\n',data);assert section
        newline=b'\r\n' if b'\r\n' in data else b'\n'
        lines=b''.join(b'   equipment = EQUIPMENT\\'+name+b'.ini'+newline for name in (b'gravity_devices',b'repair_devices'))
        data=data[:section.end()]+lines+data[section.end():];target.write_bytes(data)
        assert b'DATA_EXTRA\\EQUIPMENT\\gravity_devices.ini' not in data
    else:
        source=root/relative if relative.startswith('DATA/') else root/'src/obj/gravity_device_type_bin'/Path(relative).name
        shutil.copy2(source,target)
    files.append(dict(relative=relative,original=digest(game/relative),prepared=digest(target),delete=False))
dependencies=['bin/DALib.dll','bin/dacom.dll','bin/zlib.dll','bin/imeui.dll','bin/alchemy.dll']
manifest=dict(game=str(game),files=files,dependencies=[dict(relative=p,sha256=digest(game/p)) for p in dependencies])
assert all(d['sha256'] for d in manifest['dependencies'])
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
installer=(root/'tools/physics/install_gravity_devices.ps1').read_text()
if common_only or binaries_only:
    begin=installer.index('$allowed=@(');end=installer.index('\n',begin)
    allowed=','.join("'"+entry['relative']+"'" for entry in files)
    installer=installer[:begin]+"$allowed=@("+allowed+")"+installer[end:]
    installer=installer.replace('Count -ne 10','Count -ne '+str(len(files)))
(stage/'install.ps1').write_text(installer)
print(stage/'install.ps1')
