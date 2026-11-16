"""Strong per-atlas hair normals. Preserve all currently installed head sculpting."""
import argparse,copy,hashlib,json,struct
from collections import Counter
from datetime import datetime
from io import BytesIO
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from build import ROOT,GAME,DataFolder,read_tree,write_tree,child,blob,arr,faces,triangles,Node
from repair_panel_normals import leaves
from short_hair import BOUNDARIES

OUT=ROOT/'out/all_hair';MAPS=ROOT/'DATA_EXTRA/ROOM_MATERIALS/HAIR'
# Previously deferred large/long styles, reviewed against the source atlases.
EXTRA={
4:[.63,.60,.49,.35,.30,.30,.30,.35,.49,.60,.63],
5:[.78,.76,.66,.51,.30,.24,.30,.51,.66,.76,.78],
6:[.76,.72,.62,.48,.34,.24,.34,.48,.62,.72,.76],
19:[.84,.80,.57,.37,.17,.12,.17,.37,.57,.80,.84],
26:[.71,.66,.53,.40,.28,.22,.28,.40,.53,.66,.71],
40:[.70,.65,.54,.37,.29,.31,.29,.37,.54,.65,.70],
54:[.59,.57,.44,.32,.23,.19,.23,.32,.44,.57,.59],
56:[.76,.72,.56,.41,.24,.19,.24,.41,.56,.72,.76],
62:[.78,.75,.56,.35,.12,.08,.12,.35,.56,.75,.78],
64:[.20,.18,.15,.10,.08,.08,.08,.10,.15,.18,.20],
65:[.20,.18,.15,.10,.08,.08,.08,.10,.15,.18,.20],
}
def sha(b):return hashlib.sha256(b).hexdigest()
def is_hair(name):return name.startswith(('short_hair_','hero_hair_')) or name in ('hatcher_hair_v1','hatcher_hat_hair')

def normal_map(image,hero):
    # Keep authored fine locks on NPC heads too; halving their atlas resolution
    # discarded precisely the detail that distinguishes hair from a smooth cap.
    size=min(1024,max(image.size))
    image=image.convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
    rgb=np.asarray(image,dtype=float)/255.;lum=rgb@np.array([.299,.587,.114])
    height=gaussian_filter(lum,.7)-gaussian_filter(lum,4)
    dy,dx=np.gradient(height)
    # Real texture structure supplies direction, avoiding synthetic crosswise waves.
    n=np.stack([-dx*14,dy*14,np.ones_like(dx)],axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
    packed=np.empty((size,size,4),dtype=np.uint8)
    packed[:,:,:2]=np.clip((n[:,:,:2]*.5+.5)*255,0,255).astype(np.uint8)
    packed[:,:,2]=135;packed[:,:,3]=255
    assert np.isfinite(n).all() and np.allclose(np.linalg.norm(n,axis=-1),1)
    return Image.fromarray(packed)

def build():
    OUT.mkdir(parents=True,exist_ok=True);MAPS.mkdir(parents=True,exist_ok=True)
    inventory=json.loads((ROOT/'tools/hatcher_hair/assets/short_hair_atlases.json').read_text())
    profiles={(inventory[i]['material'],inventory[i]['texture'].lower()):(inventory[i],line) for i,line in (BOUNDARIES|EXTRA).items()}
    profiles[('pi_pirate3_head_HURT','pi_pirate3_head_hurt.tga')]=(dict(head='pi_pirate3_head_hurt.dfm',texture='pi_pirate3_head_HURT.TGA'),BOUNDARIES[33])
    stage=DataFolder(root=OUT/'stage');records=[];registered={};coverage=[];map_files=set()
    for file in sorted((GAME/'DATA/CHARACTERS/HEADS').glob('*.dfm')):
        if '_holo' in file.stem or 'benchmark' in file.stem:continue
        rel='CHARACTERS/HEADS/'+file.name;source=file.read_bytes();header,roots=read_tree(source);root=roots[0]
        mats=child(root,'Material library');additions={};hair_count=0
        # Existing dedicated materials are authoritative; never rebuild those
        # heads from the old baseline (Hatcher/Darcy sculpt and Juni UV fix).
        already=any(is_hair(m.name) for m in mats.children)
        if not already:
            for mesh in child(root,'MultiLevel').children:
                if not mesh.name.startswith('Mesh'):continue
                groups=child(mesh,'Face_groups');geo=child(mesh,'Geometry')
                uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
                before=Counter(tuple(t) for g in groups.children if g.children for t in triangles(g))
                for group in list(groups.children):
                    if not group.children:continue
                    name=blob(group,'Material_name').rstrip(b'\0').decode()
                    mat=child(mats,name)
                    tex_node=next((n for n in mat.children if n.name=='Dt_name'),None)
                    if tex_node is None:continue
                    texture=tex_node.blob.rstrip(b'\0').decode()
                    profile=profiles.get((name,texture.lower()))
                    if profile is None:continue
                    row,line=profile
                    def inside(t):
                        coords=uv[ui[t]]
                        for a in range(5):
                            for b in range(5-a):
                                u,v=(coords[0]*a+coords[1]*b+coords[2]*(4-a-b))/4
                                if name=='ku_kym_head01':u,v=u%1,v%1
                                elif not (0<=u<=1 and 0<=v<=1):return False
                                # Hair islands must not include exposed ears. A
                                # conservative guard also keeps edge triangles native.
                                if min(((u-.21)/.045)**2,((u-.79)/.045)**2)+((1-v-.43)/.13)**2<1:return False
                                side={'ge_male7_head.dfm':(.16,.23,.52),'pi_pirate1_head.dfm':(.15,.30,.65),'sh_male4_head.dfm':(.16,.20,.50)}.get(row['head'])
                                if side:
                                    w,top,bottom=side
                                    if not ((u<w or u>1-w) and top<1-v<bottom):return False
                                elif 1-v>np.interp(u,[0,.16,.22,.29,.4,.5,.6,.71,.78,.84,1],line)-.008:return False
                        return True
                    selected=[];other=[]
                    for t in triangles(group):(selected if inside(t) else other).append(t)
                    if not selected:continue
                    newname='short_hair_'+name
                    if name in ('ape_head01','mandril_head01'):newname+='_'+file.stem
                    if newname not in additions:
                        material=copy.deepcopy(mat);material.name=newname;additions[newname]=material
                    if other:
                        faces(group,other);newgroup=Node('Group'+str(len([g for g in groups.children if g.children])))
                        newgroup.children=[Node('Material_name',(newname+'\0').encode())];faces(newgroup,selected);groups.children.append(newgroup)
                    else:child(group,'Material_name').blob=(newname+'\0').encode()
                child(groups,'Count').blob=struct.pack('<I',len([g for g in groups.children if g.children]))
                assert before==Counter(tuple(t) for g in groups.children if g.children for t in triangles(g))
            mats.children.extend(additions.values());child(mats,'Material count').blob=struct.pack('<I',len([m for m in mats.children if m.children]))
        for material in mats.children:
            if not is_hair(material.name):continue
            name=material.name;texture=blob(material,'Dt_name').rstrip(b'\0').decode()
            texture_data=blob(child(child(root,'Texture library'),texture),'MIP0')
            hero=name.startswith('hero_hair_') or name=='hatcher_hair_v1' or 'pl_female4' in name or 'br_darcy' in name
            if name=='short_hair_pl_female4_head03':relative='juni_hair_normal.png'
            else:
                relative='HAIR/'+sha(texture_data)[:20]+('_hq' if hero else '')+'.png'
                if relative not in map_files:normal_map(Image.open(BytesIO(texture_data)),hero).save(MAPS.parent/relative)
            map_files.add(relative)
            key=(name,texture);value=(relative,hero)
            assert key not in registered or registered[key]==value,'Conflicting material texture '+name
            registered[key]=value;hair_count+=1
        coverage.append(dict(file=file.name,hair_materials=hair_count,modified=bool(additions)))
        if additions:
            data=write_tree(header,roots)
            old={p:b for p,_,b in leaves(source)[1]};new={p:b for p,_,b in leaves(data)[1]}
            for path,value in old.items():
                if '/Face_groups/' in path or path.endswith('/Material count'):continue
                assert new[path]==value,path
            stage.sync_data_file(rel,data);records.append(dict(file=rel,before=sha(source),after=sha(data)))
    lines=['// Generated by tools/hatcher_hair/all_hair.py; exact hair-only material pairs.',
           'struct FullHairMaterial { const char* Name; const char* Texture; const char* Map; bool Hero; };',
           'static const FullHairMaterial kFullHairMaterials[] = {']
    for (name,texture),(relative,hero) in sorted(registered.items()):
        lines.append('    {"'+name+'", "'+texture+'", "'+relative+'", '+str(hero).lower()+'},')
    lines.append('};\n');(ROOT/'src/RP9/RP9FullHairMaterials.h').write_text('\n'.join(lines))
    (OUT/'manifest.json').write_text(json.dumps(records,indent=2));(OUT/'coverage.json').write_text(json.dumps(coverage,indent=2))
    (ROOT/'tools/hatcher_hair/assets/all_hair_maps.json').write_text(json.dumps(sorted(map_files),indent=2))
    print('Heads with hair:',sum(c['hair_materials']>0 for c in coverage),'newly split:',len(records),'maps:',len(map_files))
    print('Without scalp-hair profile:',', '.join(c['file'] for c in coverage if not c['hair_materials']))

def install():
    records=json.loads((OUT/'manifest.json').read_text());live=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage')
    for r in records:
        assert sha(live.data_path(r['file']).read_bytes()) in (r['before'],r['after'])
        assert sha(stage.data_path(r['file']).read_bytes())==r['after']
    backup=DataFolder(root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for r in records:backup.sync_data_file(r['file'],live.data_path(r['file']).read_bytes())
    try:
        for r in records:
            live.sync_data_file(r['file'],stage.data_path(r['file']).read_bytes())
            assert sha(live.data_path(r['file']).read_bytes())==r['after']
    except Exception:
        for r in records:live.sync_data_file(r['file'],backup.data_path(r['file']).read_bytes())
        raise
    print('Installed',len(records),'heads; existing customized heads preserved.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    install() if args.apply else build()
