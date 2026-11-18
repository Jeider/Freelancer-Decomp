"""Read-only native character audit for the Meshy Hassler clothing prototype."""
import gzip, hashlib, io, json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
import contours as c
from hands import skeleton

OUT=c.ROOT/'out/character_rounding/hassler'
INPUT=Path('D:/Work/Meshy/Hassler1')
ASSETS={'body':'BODIES/rh_male_elite_body.dfm', 'epaulettes':'BODIES/rh_reichman_body.dfm',
        'head':'HEADS/rh_hassler_head.dfm', 'left_hand':'HANDS/rh_male_glove_left.dfm',
        'right_hand':'HANDS/rh_male_glove_right.dfm'}

def digest(data): return hashlib.sha256(data).hexdigest()
def dump(path,data): path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

def main():
    assert shutil.disk_usage(c.ROOT).free>3*1024**3
    (OUT/'source').mkdir(parents=True,exist_ok=True);(OUT/'textures').mkdir(exist_ok=True)
    report={'user_inputs':{p.name:{'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
                           for p in INPUT.iterdir() if p.is_file()},'native':{},'installed':False}
    for label,rel in ASSETS.items():
        path=c.GAME/'DATA/CHARACTERS'/rel;raw=path.read_bytes();h,roots=c.read_tree(raw);root=roots[0]
        snapshot=OUT/'source'/path.name
        if snapshot.exists(): assert digest(snapshot.read_bytes())==digest(raw),'Native source changed'
        else: snapshot.write_bytes(raw)
        records,groups,faces=c.as_records(root);bones=skeleton(root)
        cmp={c.blob(n,'Object name').rstrip(b'\0').decode():int(c.arr(n,'Index','<u4').ravel()[0])
             for n in c.child(root,'Cmpnd').children if any(f.name=='Index' for f in n.children)}
        # Runtime skin arrays index ordered 3DB resources. Body Cmpnd agrees.
        for i,b in enumerate(bones):
            if b['name'] in cmp: assert cmp[b['name']]==i,(label,b['name'],i,cmp[b['name']])
        hardpoints={}
        resources=[n for n in root.children if n.name.lower().endswith('.3db')]
        for bi,(b,node) in enumerate(zip(bones,resources)):
            a=np.array(b['native_bind']);inverse=np.eye(4);inverse[:3,:3]=a[:9].reshape(3,3);inverse[:3,3]=a[9:]
            bind=np.linalg.inv(inverse)
            hp=next((n for n in node.children if n.name=='Hardpoints'),None)
            if hp:
                for kind in hp.children:
                    for point in kind.children:
                        mat=np.eye(4);mat[:3,:3]=c.arr(point,'Orientation','<f4',3);mat[:3,3]=c.arr(point,'Position','<f4').ravel()
                        hardpoints[point.name]={'bone':b['name'],'matrix':(bind@mat).tolist(),'local':mat.tolist()}
        data={'points':[r['p'].tolist() for r in records],'normals':[r['n'].tolist() for r in records],
              'uv':[r['uv'].tolist() for r in records],'skin':[r['skin'] for r in records],
              'bones':bones,'hardpoints':hardpoints,'groups':[],'source':str(path),'sha256':digest(raw)}
        for g,fs in zip(groups,faces):
            name=c.blob(g,'Material_name').rstrip(b'\0').decode()
            mat=next(n for n in c.child(root,'Material library').children if n.name.lower()==name.lower())
            tn=next((n.blob.rstrip(b'\0').decode() for n in mat.children if n.name=='Dt_name'),None)
            texpath=None
            if tn:
                tex=next(n for n in c.child(root,'Texture library').children if n.name.lower()==tn.lower())
                payload=next(n.blob for n in tex.children if n.name in ('MIP0','MIPS'))
                texpath=OUT/'textures'/(digest(payload)[:16]+'.png')
                if not texpath.exists(): Image.open(io.BytesIO(payload)).save(texpath)
            data['groups'].append({'name':name,'texture':str(texpath) if texpath else None,'faces':fs})
        c.save_json(OUT/'source'/(label+'.json.gz'),data)
        ml=c.child(root,'MultiLevel')
        report['native'][label]={'path':str(path),'sha256':digest(raw),'bones':len(bones),
            'bounds':[np.array(data['points']).min(0).tolist(),np.array(data['points']).max(0).tolist()],
            'groups':[g['name'] for g in data['groups']],
            'lods':{n.name:sum(len(c.triangles(g)) for g in c.child(n,'Face_groups').children if g.children)
                    for n in ml.children if n.name.startswith('Mesh')}}
    dump(OUT/'source_audit.json',report)
    print(json.dumps(report['native'],indent=2))

if __name__=='__main__':main()
