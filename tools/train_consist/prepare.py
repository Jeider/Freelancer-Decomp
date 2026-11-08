"""Assemble the supplied models into an articulated CMP/SUR, staged outside the game."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct as S
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_sur'))
import build as sur
u=sur.utf
GAME=Path('D:/games/FL_MOD')
OUT=ROOT/'out/train_consist'
MODEL=Path('DATA/SHIPS/UTILITY/FREIGHT_TRAIN')
WAGONS=20
# Centers of the modeled vertical coupling pins. Front pin top and rear pin
# bottom meet at Y=1.696; their cylindrical axes must share the same X/Z.
HEAD_REAR=(-.1,1.696,25.1456)
WAGON_FRONT=(-.1,1.696,-.22488)
WAGON_REAR=(-.1,1.696,43.21455)


def group(name,*children):
    n=u.Node(name);n.children=list(children);return n


def leaf(name,value):
    return u.Node(name,value)


def hp(node,name,p):
    hardpoints=sur.child(node,'Hardpoints')
    if hardpoints is None:
        hardpoints=group('Hardpoints');node.children.append(hardpoints)
    fixed=sur.child(hardpoints,'Fixed')
    if fixed is None:
        fixed=group('Fixed');hardpoints.children.append(fixed)
    assert sur.child(fixed,name) is None
    fixed.children.append(group(name,leaf('Orientation',S.pack('<9f',1,0,0,0,1,0,0,0,1)),
                                leaf('Position',S.pack('<3f',*p))))


def partnode(root,entry):
    return sur.child(root,sur.string(sur.child(entry,'File name')))


def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wagons',type=int,default=WAGONS)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    assert 1<=args.wagons<=20,'Validated model capacity is 1..20 wagons'
    OUT=args.output
    OUT.mkdir(parents=True,exist_ok=True)
    paths=[GAME/MODEL/(n+'.cmp') for n in ['train_car','train_cargo']]
    hdr,roots=u.read_tree(paths[0].read_bytes());root=roots[0]
    cargo=u.read_tree(paths[1].read_bytes())[1][0]
    for n in sur.child(cargo,'VMeshLibrary').children:
        assert sur.child(sur.child(root,'VMeshLibrary'),n.name) is None
        sur.child(root,'VMeshLibrary').children.append(copy.deepcopy(n))
    compound=sur.child(root,'Cmpnd')
    head=partnode(root,sur.child(compound,'Root'))
    hp(head,'HpCoupleRear',HEAD_REAR)
    template=partnode(cargo,sur.child(sur.child(cargo,'Cmpnd'),'Root'))
    constraints=sur.child(sur.child(compound,'Cons'),'Fix')
    for number in range(1,args.wagons+1):
        z=(HEAD_REAR if number==1 else WAGON_REAR)[2]-WAGON_FRONT[2]
        name=f'TrainWagon{number:02}'
        node=copy.deepcopy(template);node.name=name+'.3db'
        for kind in sur.child(node,'Hardpoints').children:
            for h in kind.children:
                if h.name.lower().startswith('hpcargo'):h.name=f'HpCargo{int(h.name[-2:])+2*(number-1):02}'
                if h.name.lower().startswith('hprunninglight'):h.name=f'HpRunningLight{int(h.name[-2:])+4*(number-1):02}'
        hp(node,'HpCoupleFront',WAGON_FRONT)
        hp(node,'HpCoupleRear',WAGON_REAR)
        if number==args.wagons:
            # Retain the sixth turret expected by stock ge_train loadouts.
            turret=copy.deepcopy(sur.child(sur.child(sur.child(head,'Hardpoints'),'Revolute'),'HpTurret01'))
            turret.name='HpTurret06'
            sur.child(turret,'Position').blob=S.pack('<3f',-.1,12.7,41)
            rev=sur.child(sur.child(node,'Hardpoints'),'Revolute')
            if rev is None:
                rev=group('Revolute');sur.child(node,'Hardpoints').children.append(rev)
            rev.children.append(turret)
        root.children.append(node)
        compound.children.append(group('Part_'+name,leaf('Object name',name.encode()+b'\0'),
                                       leaf('Index',S.pack('<I',number+2)),leaf('File name',node.name.encode()+b'\0')))
        parent='Root' if number==1 else f'TrainWagon{number-1:02}'
        # Fix gives the initial rest pose. !fxd in SUR creates the separate physical
        # instance; IInstanceTransform subsequently supplies its simulated pose.
        constraints.blob+=S.pack('<64s64s3f9f',parent.encode(),name.encode(),0,0,z,1,0,0,0,1,0,0,0,1)
    for i,name in enumerate(['Root','Part_Engine01_lod1','Part_Engine02_lod1']):
        sur.child(sur.child(compound,name),'Index').blob=S.pack('<I',i)
    target=OUT/'train_consist.cmp'
    target.write_bytes(u.write_tree(hdr,roots))
    parts=sur.read_cmp(target)
    recipe=json.loads((ROOT/'tools/train_sur/regions.json').read_text())['train_cargo.cmp']
    assert hashlib.sha256(paths[1].read_bytes()).hexdigest()==recipe['source_sha256'],'Cargo geometry changed'
    own={n:sur.hulls_for(p,12,recipe['regions']['Root'] if n.startswith('TrainWagon') else None) for n,p in parts.items()}
    # Root contains only the fixed engines. Wagons have their own SUR entries.
    fixed={n:p for n,p in parts.items() if not n.startswith('TrainWagon')}
    data=bytearray(b'vers'+S.pack('<f',2))
    for name,p in parts.items():
        hulls=own[name] if name.startswith('TrainWagon') else sur.transformed_hulls(name,fixed,own)
        surface,lo,hi=sur.encode_surface(hulls)
        dynamic=name=='Root' or name.startswith('TrainWagon')
        data.extend(S.pack('<II',u.crc(name),3 if dynamic else 2))
        if dynamic:data.extend(b'!fxd')
        data.extend(b'exts'+S.pack('<6f',*lo,*hi)+b'surf'+S.pack('<I',len(surface))+surface)
    (OUT/'train_consist.sur').write_bytes(data)
    sur.preview('train_consist',parts,own,'Root',OUT)
    manifest={'wagons':args.wagons,'anchors':{'head_rear':HEAD_REAR,'wagon_front':WAGON_FRONT,'wagon_rear':WAGON_REAR},
        'source_models':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'parts':{n:{'parent':p.parent,'translation':p.translation.tolist(),'hardpoints':p.hardpoints} for n,p in parts.items()},
        'files':{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['train_consist.cmp','train_consist.sur']}}
    (OUT/'data.json').write_text(json.dumps(manifest,indent=2))
    print('Prepared train_consist: head +',args.wagons,'dynamic wagons,',len(data),'SUR bytes')


if __name__=='__main__':main()
