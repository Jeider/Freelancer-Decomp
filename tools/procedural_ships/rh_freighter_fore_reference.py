"""Read the original front cornice, its real UVs and the user's marked profile."""
import json
import shutil
import numpy as np
import rh_freighter_uv11 as e

q,f=e.q,e.f
OUT=e.OUT.parents[1]/'references/fore_cornice_12'


def main():
    assert shutil.disk_usage(q.ROOT).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for label,source,mat in [('rh_freighter',q.SOURCE.parent.parent/'rh_freighter/rh_freighter.cmp',q.MAT.with_name('rh_playerships.mat')),
                             ('rh_pir_freighter',q.SOURCE,q.MAT)]:
        _,nodes=f.mesh.read_tree(source.read_bytes());names=f.component_map(nodes)
        tr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
        mats=f.audit.material_table([mat,source.parents[3]/'fx/envmapbasic.mat'])
        groups=[];triangles=[]
        for file,gs in f.local_geometry(nodes).items():
            if names[file]!='Root':continue
            for g in f.base.world(gs,*tr[file.lower()]):
                t=np.array(g['corners']);mask=(t[:,:,2].max(1)<-3.5)&(t[:,:,1].min(1)>-.85)
                if not mask.any():continue
                selected=t[mask];groups.append(dict(material=g['material'],corners=selected))
                for i,tri in zip(np.where(mask)[0],selected):
                    triangles.append(dict(material=mats[g['material']]['name'],source_triangle=int(i),corners=tri.tolist()))
        assert groups
        for name,direction in [('front',(0,.001,-1)),('corner',(1,.4,-1)),('side',(1,.001,0))]:
            q.cull_render(groups,mats,np.array([0,2,-5.8]),4.8,direction,size=1000).save(OUT/f'{label}_{name}.png')
        records.append(dict(model=str(source),model_sha256=f.digest(source),material=str(mat),material_sha256=f.digest(mat),triangles=triangles))
    (OUT/'native_fore.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    refs=[]
    for i,key in enumerate(('5Sb1pN','C3PhFQ','TQnRJF','C1jFpK','ZAw84B'),1):
        source=e.prev.Path(f'C:/Users/Freel/AppData/Local/Temp/codex-clipboard-{key}.png');target=OUT/f'user_{i:02}_{key}.png'
        if source.exists():shutil.copyfile(source,target)
        refs.append(dict(order=i,original=str(source),file=target.name,sha256=f.digest(target)))
    (OUT/'user_references.json').write_text(json.dumps(refs,indent=2),encoding='utf8')
    print('FORE_REFERENCE',OUT,'free GB',round(shutil.disk_usage(q.ROOT).free/1024**3,2))
    for entry in records[1]['triangles']:
        t=np.array(entry['corners']);n=e.old.normal(t)
        if abs(n[2])>.5 or n[1]>.8:
            print(entry['material'],entry['source_triangle'],'XYZ',np.round(t[:,:3],3).tolist(),'UV',np.round(t[:,6:8],4).tolist(),'n',np.round(n,2).tolist())


if __name__=='__main__':main()
