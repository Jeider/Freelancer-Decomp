"""Read a copied arrival autosave using the production courier save loader."""
from pathlib import Path
import json
import subprocess
from check_orders import function,compiler_env
from check_order_state import PREFIX,MOCKS

ROOT=Path(__file__).resolve().parents[2]

def main():
    fixture=ROOT/'out/train_courier/jump_diagnostic/autosave_before_fix.ini'
    assert fixture.exists(), 'Copy/decode the affected autosave read-only first'
    catalog=json.loads((ROOT/'out/train_courier/catalog.json').read_text())
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text()
    methods='\n'.join(function(source,s) for s in ('bool activeOrder(', 'void refreshBrief(', 'void observeLoss(', 'bool readSave('))
    bridge=(ROOT/'src/include/train_courier_bridge.h').read_text().replace('#pragma once','').replace('#include "common_csys.h"','')
    rows=['};\nint main(){Mission m;']
    for base in catalog['bases'].values():
        for point in base['points']:
            rows.append('m.config.points.push_back({'+json.dumps(point['nickname'])+',1,{}});')
    from order_texts import rows as texts
    for name,commodity in catalog['commodities'].items():
        ids=[str(row[1]) for row in texts() if row[0].startswith('brief_'+name.removeprefix('comm_')+'_')]
        rows.append('m.config.descriptions['+json.dumps(name)+']={'+','.join(ids)+'};')
    rows.append('INI_Reader input('+json.dumps(str(fixture))+');assert(m.readSave(input));')
    rows.append(r'''
        assert(m.state.stage==Stage::Deliver && m.state.wagons==10 && m.state.unlockedWagons==10);
        assert(m.restoreCargo && !m.cargoPending && m.savedCargo.coupled && m.savedCargo.system==777);
        assert(m.state.reward==31840 && m.lostPods==0 && m.savedCargo.hitpoints==10431);
        assert(m.remaining>1945 && m.remaining<1946 && m.expectedSeconds==2100);
        unsigned pods=0,units=0;
        for(unsigned i=0;i<m.savedCargo.equipmentCount;++i){auto const& e=m.savedCargo.equipment[i];if(e.mounted){++pods;assert(e.health==1);}else units+=e.count;}
        assert(pods==20 && units==1000);
        puts("PASS: affected Omega-15 autosave loads with 10 wagons, 20 intact pods, 1000 units, original hull damage, quote and remaining time; coupled restore targets current system");
    }''')
    out=ROOT/'src/obj/train_courier/saved_jump';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'saved.cpp';cpp.write_text(PREFIX+bridge+MOCKS+methods+'\n'.join(rows))
    compiler,env=compiler_env();exe=out/'saved.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/D_CRT_SECURE_NO_WARNINGS',
                    '/I'+str(ROOT/'src/include'),str(cpp),'/Fo'+str(out/'saved.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__=='__main__':main()
