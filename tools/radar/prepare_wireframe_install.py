"""Stage Common, client and the nine opt-in Solar records for reversible installation."""
from datetime import datetime
import json
import shutil
from stage_wireframe import ROOT, GAME, OUT
from stage_solars import sha


def digest(path):
    return sha(path.read_bytes()) if path.exists() else None


def main():
    report=json.loads((OUT/'stage.json').read_text())
    assert digest(GAME/'DATA/SOLAR/solararch.ini')==report['original'], 'Solar definitions changed; restage'
    assert digest(OUT/'solararch.ini')==report['prepared']
    for relative, expected in report['dependencies'].items():
        assert digest(GAME/relative)==expected, 'Input changed: '+relative
    stage=ROOT/'src/obj/radar_wireframe_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
    stage.mkdir(parents=True)
    sources={f'bin/{name}':ROOT/'bin'/name for name in ('Common.dll','Common.pdb','freelancer.exe','freelancer.pdb')}
    sources['DATA/SOLAR/solararch.ini']=OUT/'solararch.ini'
    files=[]
    for relative,source in sources.items():
        target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        files.append(dict(relative=relative,original=digest(GAME/relative),prepared=digest(target)))
    (stage/'manifest.json').write_text(json.dumps(dict(game=str(GAME),files=files,dependencies=report['dependencies']),indent=2)+'\n')
    script=(ROOT/'tools/inventory_categories/install.ps1').read_text()
    script=script.replace('Count -ne 8','Count -ne 5').replace('all 8 SHA256','all 5 SHA256')
    script=script.replace('codex_inventory_categories_','codex_radar_wireframe_').replace('Inventory categories installed','Radar wireframe installed')
    lines=script.splitlines()
    lines=["$allowed=@("+','.join("'"+p+"'" for p in sources)+')' if line.startswith('$allowed=') else line for line in lines]
    script='\n'.join(lines)+'\n'
    guard='''foreach ($dependency in $manifest.dependencies.PSObject.Properties) {
    $target=[IO.Path]::GetFullPath((Join-Path $game $dependency.Name))
    if (-not $target.StartsWith($game+'\\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Invalid dependency path'}
    if ((Hash $target) -ne $dependency.Value) {throw 'Lair model/system changed since staging'}
}
'''
    script=script.replace('$backup=Join-Path',guard+'$backup=Join-Path')
    (stage/'install.ps1').write_text(script)
    print(stage/'install.ps1')


if __name__=='__main__':main()
