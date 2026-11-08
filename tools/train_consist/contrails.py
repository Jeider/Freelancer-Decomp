"""Authored train trail anchors. Preview only; never writes models into the game."""
from pathlib import Path
import argparse
import re
import struct
import prepare as model

# Local coordinates of actual LOD0 contour vertices, with 0.15 m outward
# clearance. Engine02's local +Z points to the locomotive's left side.
LOCOMOTIVE = [
    ('Engine01_lod1', 'HpContrail01', (8.534865, -2.103273, .257425)),
    ('Engine02_lod1', 'HpContrail02', (.257414, -2.103288, 8.534848)),
    ('Root', 'HpContrail03', (-8.927109, 10.367233, 19.329031)),
    ('Root', 'HpContrail04', (8.724770, 10.367236, 19.329031)),
]
# Rear outer frame corners. Put these on the LAST surviving wagon, rather
# than the root: articulated movement must carry the anchors with the tail.
TAIL = [
    ('HpContrail01', (-6.018318, 8.799130, 40.311546)),
    ('HpContrail02', (5.815633, 8.798680, 40.311546)),
    ('HpContrail03', (-6.018318, -4.030840, 40.311554)),
    ('HpContrail04', (5.815633, -4.018907, 40.311562)),
]

def annotate(root, wagons=False):
    compound=model.sur.child(root,'Cmpnd')
    nodes={model.sur.string(model.sur.child(entry,'Object name')):model.partnode(root,entry)
           for entry in compound.children if model.sur.child(entry,'Object name')}
    if wagons:
        tail=max(nodes,key=lambda n: int(n[10:]) if re.fullmatch(r'TrainWagon\d+',n) else 0)
        anchors=[(tail,name,position) for name,position in TAIL]
    else:
        anchors=LOCOMOTIVE
    # Never silently overwrite points authored later by the user. Re-running
    # the model generator keeps pre-existing trails intact.
    if any(re.fullmatch(r'hpcon(?:t|tr)ail\d+',hp.name,re.I)
           for node in nodes.values() if (hardpoints:=model.sur.child(node,'Hardpoints'))
           for kind in hardpoints.children for hp in kind.children):
        return
    for part,name,position in anchors:
        model.hp(nodes[part],name,position)

def annotated(raw,wagons=False):
    header,trees=model.u.read_tree(raw)
    annotate(trees[0],wagons)
    return model.u.write_tree(header,trees)

def preview(game,output):
    # This is a geometry inspection, not a model or binary build.
    import numpy as np
    from PIL import Image, ImageDraw
    canvas=Image.new('RGB',(1200,1000),'#f5f7fa');draw=ImageDraw.Draw(canvas)
    folder=game/'DATA/SHIPS/UTILITY/FREIGHT_TRAIN'
    for col,(filename,wagons) in enumerate([('train_locomotive.cmp',False),('train_wagons.cmp',True)]):
        parts=model.sur.read_cmp(folder/filename)
        if wagons:
            triangles=parts['Root'].triangles
            anchors=[(name,np.array(pos)) for name,pos in TAIL]
        else:
            triangles=np.concatenate([p.triangles@p.rotation+p.translation for p in parts.values()])
            anchors=[(name,np.array(pos)@parts[part].rotation+parts[part].translation)
                     for part,name,pos in LOCOMOTIVE]
        draw.text((col*600+20,15),'Last wagon frame' if wagons else 'Locomotive',fill='#172b44')
        for row,((a,b),label) in enumerate(zip([(2,0),(2,1),(0,1)],['Top Z/X','Side Z/Y','Rear X/Y'])):
            xy=triangles[:,:,[a,b]].reshape(-1,2);lo=xy.min(axis=0);hi=xy.max(axis=0)
            center=(lo+hi)/2;scale=min(520/(hi[0]-lo[0]),250/(hi[1]-lo[1]))
            def screen(p):
                q=(p-center)*scale
                return float(q[0]+col*600+300),float(190+row*310-q[1])
            draw.text((col*600+20,50+row*310),label,fill='#172b44')
            for tri in triangles:draw.polygon([screen(p) for p in tri[:,[a,b]]],fill='#9da9b5')
            for name,pos in anchors:
                x,y=screen(pos[[a,b]])
                draw.ellipse((x-4,y-4,x+4,y+4),fill='#da3829')
                draw.text((x+7,y-12),name[-2:],fill='#a51f13')
    output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output)
    print('Geometry preview only:',output)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,default=Path('D:/Games/FL_MOD'))
    parser.add_argument('--preview',type=Path,required=True)
    args=parser.parse_args();preview(args.game,args.preview)
