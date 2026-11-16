"""Split verified hair UV regions into opt-in materials, without changing faces/rigs."""
import argparse, copy, hashlib, json, struct
from collections import Counter
from datetime import datetime
import numpy as np
from build import ROOT, GAME, DataFolder, read_tree, write_tree, child, blob, arr, faces, triangles, Node
from repair_panel_normals import leaves

OUT=ROOT/'out/hair_rollout'
# Reviewed atlas boundaries: x=0,.16,.22,.29,.40,.50,.60,.71,.78,.84,1.
# Values are image-space y, conservatively INSIDE hair, not skin or eyebrows.
# Bald heads and long/large female styles deliberately have no entry.
BOUNDARIES={
0:[.54,.54,.33,.14,.13,.16,.13,.14,.33,.54,.54],
1:[.45,.42,.32,.09,.06,.08,.06,.09,.32,.42,.45],
2:[.53,.50,.35,.16,.13,.16,.13,.16,.35,.50,.53],
3:[.66,.61,.48,.36,.32,.32,.32,.36,.48,.61,.66],
7:[.47,.44,.32,.12,.09,.12,.09,.12,.32,.44,.47],
8:[.12,.12,.12,.11,.09,.11,.09,.11,.12,.12,.12],
9:[.61,.60,.56,.46,.27,.15,.27,.46,.56,.60,.61],
10:[.52,.48,.39,.15,.17,.21,.17,.15,.39,.48,.52],
11:[.50,.46,.35,.15,.15,.22,.15,.15,.35,.46,.50],
12:[.50,.46,.34,.13,.12,.14,.12,.13,.34,.46,.50],
13:[.43,.41,.34,.11,.10,.13,.10,.11,.34,.41,.43],
15:[.19,.19,.16,.02,.00,.00,.00,.02,.16,.19,.19],
16:[.51,.47,.34,.12,.08,.10,.08,.12,.34,.47,.51],
17:[.51,.46,.33,.13,.15,.20,.15,.13,.33,.46,.51],
18:[.54,.48,.33,.15,.16,.21,.16,.15,.33,.48,.54],
20:[.51,.47,.33,.17,.12,.25,.13,.17,.33,.47,.51],
21:[.49,.46,.33,.13,.12,.12,.12,.13,.33,.46,.49],
22:[.64,.61,.57,.46,.34,.34,.34,.46,.57,.61,.64],
23:[.56,.52,.36,.17,.17,.18,.17,.17,.36,.52,.56],
24:[.54,.49,.33,.12,.10,.10,.10,.12,.33,.49,.54],
25:[.62,.54,.40,.13,.11,.27,.11,.13,.40,.54,.62],
27:[.48,.44,.32,.17,.14,.16,.14,.17,.32,.44,.48],
28:[.48,.46,.40,.30,.12,.09,.12,.30,.40,.46,.48],
30:[.72,.68,.51,.30,.13,.07,.13,.30,.51,.68,.72],
31:[.20,.20,.17,.00,.00,.00,.00,.00,.17,.20,.20],
32:[.54,.48,.36,.12,.12,.19,.12,.12,.36,.48,.54],
33:[.59,.55,.41,.25,.12,.10,.12,.25,.41,.55,.59],
34:[.70,.62,.47,.32,.25,.23,.25,.32,.47,.62,.70],
35:[.71,.66,.46,.31,.15,.09,.15,.31,.46,.66,.71],
36:[.50,.47,.39,.28,.16,.13,.16,.28,.39,.47,.50],
38:[.59,.54,.40,.24,.19,.19,.19,.24,.40,.54,.59],
39:[.58,.56,.45,.25,.16,.12,.16,.25,.45,.56,.58],
41:[.53,.49,.40,.25,.16,.17,.16,.25,.40,.49,.53],
44:[.11,.10,.08,.08,.12,.17,.12,.08,.08,.10,.11],
46:[.45,.42,.31,.15,.12,.13,.12,.15,.31,.42,.45],
47:[.47,.43,.32,.13,.09,.09,.09,.13,.32,.43,.47],
48:[.50,.47,.33,.12,.10,.10,.10,.12,.33,.47,.50],
49:[.48,.44,.36,.29,.22,.19,.22,.29,.36,.44,.48],
50:[.53,.49,.40,.31,.12,.10,.12,.31,.40,.49,.53],
51:[.51,.47,.36,.13,.13,.19,.13,.13,.36,.47,.51],
52:[.45,.42,.32,.10,.09,.10,.09,.10,.32,.42,.45],
55:[.15,.13,.10,.08,.06,.08,.06,.08,.10,.13,.15],
58:[.42,.38,.31,.22,.21,.24,.21,.22,.31,.38,.42],
59:[.15,.13,.11,.10,.11,.13,.11,.10,.11,.13,.15],
60:[.62,.56,.42,.12,.08,.08,.08,.12,.42,.56,.62],
61:[.49,.46,.40,.31,.12,.08,.12,.31,.40,.46,.49],
63:[.57,.54,.44,.32,.24,.17,.24,.32,.44,.54,.57],
66:[.45,.42,.32,.13,.12,.15,.12,.13,.32,.42,.45],
67:[.45,.42,.30,.08,.06,.07,.06,.08,.30,.42,.45],
68:[.57,.53,.39,.17,.14,.17,.14,.17,.39,.53,.57],
69:[.15,.14,.11,.00,.00,.00,.00,.00,.11,.14,.15],
73:[.52,.48,.36,.26,.26,.23,.26,.26,.36,.48,.52],
74:[.48,.45,.34,.15,.13,.16,.13,.15,.34,.45,.48],
}

def sha(data):return hashlib.sha256(data).hexdigest()

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    inventory=json.loads((ROOT/'tools/hatcher_hair/assets/short_hair_atlases.json').read_text())
    profiles={inventory[i]['material']:(inventory[i],line) for i,line in BOUNDARIES.items()}
    stage=DataFolder(root=OUT/'stage'); baseline=DataFolder(root=OUT/'original')
    rows=[]; registered={}
    for file in sorted((GAME/'DATA/CHARACTERS/HEADS').glob('*.dfm')):
        if any(s in file.stem for s in ('_hat','_helmet','_holo','benchmark','li_hatcher')):continue
        rel='CHARACTERS/HEADS/'+file.name
        if not baseline.data_path(rel).exists():baseline.sync_data_file(rel,file.read_bytes())
        source=baseline.data_path(rel).read_bytes();header,roots=read_tree(source);root=roots[0]
        mats=child(root,'Material library'); additions={};stats=[]
        for mesh in child(root,'MultiLevel').children:
            if not mesh.name.startswith('Mesh'):continue
            geo=child(mesh,'Geometry'); groups=child(mesh,'Face_groups')
            uv=arr(geo,'UV0','<f4',2); ui=arr(geo,'UV0_indices','<u4').ravel()
            moved=0; total=sum(len(triangles(g)) for g in groups.children if g.children)
            original_triangles=Counter(tuple(t) for g in groups.children if g.children for t in triangles(g))
            for group in list(groups.children):
                if not group.children:continue
                name=blob(group,'Material_name').rstrip(b'\0').decode()
                if name not in profiles:continue
                row,line=profiles[name]; mat=child(mats,name)
                texture=blob(mat,'Dt_name').rstrip(b'\0').decode()
                if texture.lower()!=row['texture'].lower():continue
                def inside(t):
                    coords=uv[ui[t]]
                    # Sample triangle interiors and edges too, not merely its centroid.
                    for a in range(5):
                        for b in range(5-a):
                            u,v=(coords[0]*a+coords[1]*b+coords[2]*(4-a-b))/4
                            if not (0<=u<=1 and 0<=v<=1):return False
                            side_only={
                                'ge_male7_head.dfm':(.16,.23,.52),
                                'pi_pirate1_head.dfm':(.15,.30,.65),
                                'sh_male4_head.dfm':(.16,.20,.50),
                            }.get(row['head'])
                            if side_only:
                                width,top,bottom=side_only
                                if not ((u<width or u>1-width) and top<1-v<bottom):return False
                                continue
                            limit=np.interp(u,[0,.16,.22,.29,.40,.50,.60,.71,.78,.84,1],line)
                            if 1-v>limit-.008:return False
                    return True
                hair=[];skin=[]
                for tri in triangles(group):(hair if inside(tri) else skin).append(tri)
                if not hair:continue
                hero=file.stem in ('pi_pirate5_head','old_trent_head')
                newname=('hero_hair_' if hero else 'short_hair_')+name
                if newname not in additions:
                    newmat=copy.deepcopy(mat);newmat.name=newname;additions[newname]=newmat
                if skin:
                    faces(group,skin)
                    newgroup=Node('Group'+str(len([g for g in groups.children if g.children])))
                    newgroup.children=[Node('Material_name',(newname+'\0').encode())];faces(newgroup,hair);groups.children.append(newgroup)
                else:child(group,'Material_name').blob=(newname+'\0').encode()
                registered[(newname,texture)]=hero
                moved+=len(hair)
            put_count=child(groups,'Count');put_count.blob=struct.pack('<I',len([g for g in groups.children if g.children]))
            assert total==sum(len(triangles(g)) for g in groups.children if g.children)
            assert original_triangles==Counter(tuple(t) for g in groups.children if g.children for t in triangles(g))
            stats.append(dict(lod=mesh.name,hair_triangles=moved,triangles=total))
        if not additions:continue
        mats.children.extend(additions.values());child(mats,'Material count').blob=struct.pack('<I',len([m for m in mats.children if m.children]))
        data=write_tree(header,roots)
        # Geometry, normals, UVs, skeleton and textures MUST remain byte-identical.
        old={p:b for p,_,b in leaves(source)[1]};new={p:b for p,_,b in leaves(data)[1]}
        for path,value in old.items():
            if '/Face_groups/' in path or path.endswith('/Material count'):continue
            assert new[path]==value,path
        stage.sync_data_file(rel,data)
        rows.append(dict(file=rel,before=sha(source),after=sha(data),lods=stats))
    header=['// Generated by tools/hatcher_hair/short_hair.py; verified hair-only material/texture pairs.',
            'struct ShortHairMaterial { const char* Name; const char* Texture; bool Hero; };',
            'static const ShortHairMaterial kShortHairMaterials[] = {']
    for (name,texture),hero in sorted(registered.items()):header.append('    {"'+name+'", "'+texture+'", '+str(hero).lower()+'},')
    header.append('};\n')
    (ROOT/'src/RP9/RP9ShortHairMaterials.h').write_text('\n'.join(header))
    (OUT/'manifest.json').write_text(json.dumps(rows,indent=2))
    print('Prepared',len(rows),'heads;',len(registered),'hair materials; no added polygons.')
    for r in rows:print(r['file'],r['lods'][0]['hair_triangles'])

def install():
    rows=json.loads((OUT/'manifest.json').read_text());stage=DataFolder(root=OUT/'stage');live=DataFolder(root=GAME)
    for r in rows:
        assert sha(live.data_path(r['file']).read_bytes()) in (r['before'],r['after']),r['file']+' changed'
        assert sha(stage.data_path(r['file']).read_bytes())==r['after']
    backup=DataFolder(root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for r in rows:backup.sync_data_file(r['file'],live.data_path(r['file']).read_bytes())
    try:
        for r in rows:
            live.sync_data_file(r['file'],stage.data_path(r['file']).read_bytes())
            assert sha(live.data_path(r['file']).read_bytes())==r['after']
    except Exception:
        for r in rows:live.sync_data_file(r['file'],backup.data_path(r['file']).read_bytes())
        raise
    print('Installed and hash verified',len(rows),'heads.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    install() if args.apply else build()
