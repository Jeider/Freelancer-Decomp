"""Verify the staged world plan and execute native boarding selection/placement."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from check_orders import function, compiler_env

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT=ROOT/'out/train_courier/owners'
sys.path.insert(0,str(PROJECT))
from tools.data_folder import DataFolder
from managers.courier_owners import plan
from managers.parking_commandants import parse,one


def main():
    registry=json.loads((OUT/'payload/Assets/Pythonlancer/story/rpg/courier_owners.json').read_text(encoding='utf-8'))
    assert len(registry['bases'])==19
    class ReadOverlay(DataFolder):
        def data_path(self,name):
            target=super().data_path(name)
            return target if target.exists() else DataFolder(root=PROJECT.parent.parent).data_path(name)
    folder=ReadOverlay(root=OUT/'payload')
    catalog=folder.data_path('MISSIONS/TrainCourier/catalog.ini').read_bytes()
    files,report=plan(PROJECT,folder,registry,catalog)
    assert sum(r['posture']=='sit' for r in report)==7
    for name,content in files.items():assert folder.data_path(name).read_bytes()==content,name
    assert not any(name.startswith('AUDIO/') for name in files)
    entries=parse(files['RPG/courier_contacts.ini'])
    assert len(entries)==18 # existing Bismarck catalog entry is retained
    rows=parse(catalog)
    parking={one(r,'base'):r for k,r in rows if k=='courierparking'}
    points={one(r,'base'):r for k,r in rows if k=='courierpoint'}
    routes={(one(r,'source'),one(r,'destination')) for k,r in rows if k=='courierroute'}
    for owner in report:
        base=owner['base'];group=owner['group']
        assert base in points and base in parking
        assert one(points[base],'system')==one(parking[base],'system')==owner['system']
        assert any(a==base for a,b in routes) and any(b==base for a,b in routes)
        header=parse(files[f'RPG/courier/{base}_dialog.ini'])[0][1]
        assert one(header,'courier_base')==base and one(header,'scene_group')=='rm0001'
        assert one(header,'session_group')==group
        scene=files[f'SCRIPTS/RPG/{group}/conversation.thn']
        assert scene.count(b'START_IK')==4 and b'WFC' not in scene and b'WLKG' not in scene
        for step in range(1,9):
            vendor=files[f'SCRIPTS/RPG/{group}/gestures/vendor_{step:02}.thn']
            player=files[f'SCRIPTS/RPG/{group}/gestures/player_{step:02}.thn']
            if owner['posture']=='sit':assert b'_CHRB_' in vendor and b'_STND_' not in vendor
            assert b'_CHRB_' not in player
    with tempfile.TemporaryDirectory(dir=OUT) as temp:
        root=Path(temp)
        class Failing(DataFolder):
            calls=0
            def sync_data_file(self,name,value):
                result=super().sync_data_file(name,value);self.calls+=1
                if self.calls==2:raise OSError('injected transaction failure')
                return result
        original=DataFolder(root=root/'game')
        name='RPG/courier_contacts.ini';original.sync_data_file(name,b'original')
        try:Failing(root=root/'game').sync_courier_owners({name:b'changed','RPG/courier/test_base.ini':b'new'},root/'backup')
        except OSError:pass
        else:raise AssertionError('expected write failure')
        assert original.data_path(name).read_bytes()==b'original'
        assert not original.data_path('RPG/courier/test_base.ini').exists()
        for invalid in ('../bad','AUDIO/MOD_ENG/RPG/rm0001/x.wav','RPG/parking_contacts.ini'):
            try:original.sync_courier_owners({invalid:b'x'},root/'backup')
            except ValueError:pass
            else:raise AssertionError(invalid)
    source=(ROOT/'src/Content/TrainCourier.cpp').read_text()
    native=function(source,'Point const* boardingPoint(')
    spawn=function(source,'void startBoarding(')
    cpp=r'''
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#include <cstdio>
struct Vector {float x=0,y=0,z=0;};
struct Matrix {float e[9]={1,0,0,0,1,0,0,0,1};};
struct Point {unsigned baseId=0,systemId=0;std::string base,transfer;Vector position;Matrix orientation;unsigned faction=42;};
struct Route {std::string source;};
struct Config {std::vector<Point> parkingPoints,points;std::vector<Route> routes;unsigned board=7;};
namespace pub {void GetBaseID(unsigned& result,char const* s){result=!strcmp(s,"transfer_a")?11:!strcmp(s,"transfer_b")?12:0;}
namespace SpaceObj {int GetLocation(unsigned id,Vector& pos,Matrix& rot){pos={float(id),2,3};return 0;}}}
'''+native+r'''
struct Mission {
 struct Solar {unsigned SystemId=0,BaseId=0,SpaceObjId=0,Faction=0;Vector Position;Matrix Orientation;} record;
 Config config;Point source;unsigned boarding=0,transferBase=0;Vector transferPosition;Matrix transferOrientation;
 bool failed=false;unsigned spawns=0,objectives=0;
 Solar* solar(){return &record;}
 void OnMissionFail(){failed=true;}
 bool SpawnMissionSolarRecord(Solar* s){++spawns;s->SpaceObjId=99;return true;}
 void objectObjective(unsigned,Point const& marker,unsigned,char const*){++objectives;assert(marker.position.x==99);}
'''+spawn+r'''
};
int main(){
 Config c;c.points={{1,10,"a"},{2,20,"b"}};c.routes={{"a"},{"b"}};
 c.parkingPoints={{1,10,"a","transfer_a",{1,2,3}},{2,20,"b","transfer_b",{8,9,10}}};
 assert(boardingPoint(c,1)==&c.parkingPoints[0]);assert(boardingPoint(c,2)==&c.parkingPoints[1]);
 assert(!boardingPoint(c,0) && !boardingPoint(c,3));
 Mission m;m.config=c;m.source=c.points[1];m.startBoarding();
 assert(!m.failed && m.spawns==1 && m.objectives==1);
 assert(m.record.SystemId==20 && m.record.BaseId==12 && m.transferBase==12);
 assert(m.record.Faction==42);
 assert(m.record.Position.x==8 && m.record.Position.y==9 && m.transferPosition.x==99);
 c.parkingPoints[1].systemId=10;assert(!boardingPoint(c,2));
 c.parkingPoints[1].systemId=20;c.parkingPoints[1].transfer="missing";assert(!boardingPoint(c,2));
 c.parkingPoints[1].transfer="transfer_b";c.routes.pop_back();assert(!boardingPoint(c,2));
 m.config=c;m.startBoarding();assert(m.failed && m.spawns==1);
 puts("PASS: native local berth selection/spawn; no Bismarck fallback; missing base/transfer/route and system mismatch rejected");
}
'''
    out=OUT/'native_check';out.mkdir(exist_ok=True);path=out/'check.cpp';path.write_text(cpp)
    compiler,env=compiler_env();exe=out/'check.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc',str(path),'/Fo'+str(out/'check.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)],check=True)
    # Exercise the actual order allocator against the staged expanded catalog.
    data={'bases':{},'routes':[],'commodities':{}}
    for kind,row in rows:
        if kind=='courierpoint':
            base=one(row,'base');market={}
            for value in row.get('supply_price',[]):
                name,price=value.split(',');market[name.strip()]={'supply':True,'demand':False,'price':int(price)}
            for name in row.get('demand',[]):market.setdefault(name,{'supply':False,'price':1})['demand']=True
            entry=data['bases'].setdefault(base,dict(system=one(row,'system'),points=[],market=market,
                freight_hub=one(row,'freight_hub')=='true',large_planet=one(row,'large_planet')=='true',refinery=one(row,'refinery')=='true'))
            entry['points'].append(dict(nickname=one(row,'nickname'),base=base,commodities=row.get('commodity',[]),position=[float(x) for x in one(row,'position').split(',')]))
        elif kind=='courierroute':data['routes'].append(dict(source=one(row,'source'),destination=one(row,'destination'),distance=int(one(row,'distance')),minimum_jumps=int(one(row,'jumps','0'))))
        elif kind=='couriercommodity':data['commodities'][one(row,'nickname')]={}
    from check_orders import main as check_orders
    check_orders(data,[r['base'] for r in report])
    print('PASS: 19 owners, 7 seated, shared speech, independent gestures/IK, local berths/routes, repeat generation, scoped DATA writes and rollback')


if __name__=='__main__':main()
