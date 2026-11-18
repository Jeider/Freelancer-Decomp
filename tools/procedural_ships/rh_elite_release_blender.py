"""Distance geometry for accepted RH pirate elite; never launch from repo root."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_concept_b_final_blender as h

OUT=HERE.parents[1]/'out/ship_design/rh_elite/rh_pir_elite/tail_rim/release'


def simplify(groups,label,ratio):
    obj,slots=h.mesh_object(dict(groups=groups),label)
    obj.data.validate(verbose=False,clean_customdata=False)
    before=sum(len(g['corners']) for g in groups)
    if ratio < 1:
        mod=obj.modifiers.new('Distance silhouette','DECIMATE')
        mod.ratio=ratio
        mod.use_collapse_triangulate=True
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    gs=h.groups_from_mesh(mesh,slots)
    evaluated.to_mesh_clear()
    bpy.data.objects.remove(obj,do_unlink=True)
    after=sum(len(g['corners']) for g in gs)
    assert after and after <= before
    return gs,dict(part=label,before=before,after=after,ratio=ratio)


def main():
    data=json.loads((OUT/'lod_input.json').read_text())
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    levels=[];statistics=[]
    for lv,kept in enumerate(data['preserved'],1):
        report=[]
        for name,groups in data['replacements'].items():
            ratio=(.42 if lv==1 else .23) if name in ('Root','Rh_tail_lod1') else (.7 if lv==1 else .5)
            if 'upperarm' in name:ratio=1
            gs,stats=simplify(groups,name+' LOD'+str(lv),ratio)
            kept[name].extend(gs)
            report.append(stats)
        levels.append(kept)
        statistics.append(dict(level=lv,triangles=sum(len(g['corners']) for gs in kept.values() for g in gs),parts=report))
    damaged={};damage_stats={}
    for zone,gs in data['damage'].items():
        damaged[zone]=[];damage_stats[zone]=[]
        for lv,ratio in ((1,.50),(2,.24)):
            groups,stats=simplify(gs,zone+' damage LOD'+str(lv),ratio)
            damaged[zone].append(groups);damage_stats[zone].append(stats)
    (OUT/'lod_geometry.json').write_text(json.dumps(dict(levels=levels,damage=damaged),separators=(',',':')))
    (OUT/'lod_generation.json').write_text(json.dumps(dict(levels=statistics,damage=damage_stats),indent=2))
    print('LODS READY',[(x['level'],x['triangles']) for x in statistics],flush=True)


if __name__=='__main__':main()
