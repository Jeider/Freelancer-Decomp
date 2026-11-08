"""Read docking hardpoints from installed miner/train CMPs; never modify the game."""
import json
import struct
from pathlib import Path
from stage import u, sections, one

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
result={}
for nickname,model in [('Roid_Miner','SHIPS/UTILITY/MINING/mining.cmp'),
                       ('Roid_Miner2','SHIPS/UTILITY/MINING/mining_with_panels.cmp'),
                       ('tc_boarding_solar','SHIPS/UTILITY/FREIGHT_TRAIN/train_boarding.cmp')]:
    source=GAME/'DATA'/model
    _,trees=u.read_tree(source.read_bytes())
    record={'model':str(source),'hardpoints':{}}
    def visit(node,path=''):
        path+='/'+node.name
        if node.name.lower().startswith('hpdock'):
            record['hardpoints'][node.name]={'path':path}
            for child in node.children:
                if child.name.lower() in ('position','orientation'):
                    record['hardpoints'][node.name][child.name.lower()]=struct.unpack('<'+str(len(child.blob)//4)+'f',child.blob)
        for child in node.children:visit(child,path)
    for tree in trees:visit(tree)
    ini='SOLAR/train_courier.ini' if nickname=='tc_boarding_solar' else 'SOLAR/solararch.ini'
    definition=next(s for k,s in sections(GAME/'DATA'/ini) if k=='solar' and one(s,'nickname').lower()==nickname.lower())
    record['docking_sphere']=definition.get('docking_sphere',[])
    result[nickname]=record
    print(nickname,record['docking_sphere'])
    for name,hp in record['hardpoints'].items():
        if name.lower().startswith(('hpdockmounta','hpdockpointa')):print(name,hp)
out=ROOT/'out/train_courier/docking_comparison.json'
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
