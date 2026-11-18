"""Reopen every saved scene and check editable meshes, linked images and source visibility."""
import bpy
import json
import gzip
import sys
import traceback
import argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure as configure_blender_workspace
configure_blender_workspace('character_rounding')
OUT=Path(__file__).resolve().parents[2]/'out/character_rounding/contours_2k'
ap=argparse.ArgumentParser();ap.add_argument('--package',choices=['contours_2k','bracer_starts','hero_bodies'],default='contours_2k');ap.add_argument('--repair-metadata',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=OUT.parent/args.package
repair='--repair-metadata' in sys.argv
bpy.context.preferences.filepaths.save_version=0
if hasattr(bpy.context.preferences.filepaths,'save_preview_images'):bpy.context.preferences.filepaths.save_preview_images=False
valid=[];errors=[]
for folder in sorted(OUT.iterdir()):
    if not (folder/'report.json').exists():continue
    try:
        report=json.loads((folder/'report.json').read_text())
        cache=json.loads((folder/'render_source.json').read_text())
        assert report['output_sha256']==cache['sha256']
        blend_name='hero_body.blend' if args.package=='hero_bodies' else 'contours_2k.blend'
        bpy.ops.wm.open_mainfile(filepath=str(folder/blend_name),load_ui=False)
        source=bpy.data.collections['SOURCE - native geometry'];edited=bpy.data.collections['EDIT - hero body' if args.package=='hero_bodies' else 'EDIT - contours 2k']
        assert source.hide_viewport and source.hide_render
        assert not edited.hide_viewport and not edited.hide_render
        meshes=[o for o in edited.objects if o.type=='MESH']
        count=sum(len(o.data.polygons) for o in meshes)
        assert count==report['triangles_after']<=report.get('triangle_limit',2000)
        assert all(len(f.vertices)==3 for o in meshes for f in o.data.polygons)
        assert all(o.data.uv_layers and o.vertex_groups for o in meshes)
        data=json.loads(gzip.decompress((folder/'after.json.gz').read_bytes()))
        groups=[g for g in data['groups'] if g['faces']]
        assert len(groups)==len(meshes)
        for ob,group in zip(meshes,groups):
            assert len(ob.data.polygons)==len(group['faces'])
            checked_vertices=set()
            for polygon,face in zip(ob.data.polygons,group['faces']):
                for loop_id,index in zip(polygon.loop_indices,face):
                    vi=ob.data.loops[loop_id].vertex_index;vertex=ob.data.vertices[vi]
                    x,y,z=data['points'][data['point_indices'][index]]
                    assert max(abs(a-b) for a,b in zip(vertex.co,(x,-z,y)))<1e-6,'Saved position differs'
                    uv=ob.data.uv_layers.active.data[loop_id].uv;expected=data['uv'][data['uv_indices'][index]]
                    assert max(abs(a-b) for a,b in zip(uv,expected))<1e-6,'Saved UV differs'
                    if vi in checked_vertices:continue
                    checked_vertices.add(vi)
                    weights={ob.vertex_groups[g.group].name:g.weight for g in vertex.groups}
                    expected_weights={data['bones'][bone]:weight for bone,weight in data['skin'][index].items() if weight>0}
                    assert set(weights)==set(expected_weights),'Saved bone groups differ'
                    assert all(abs(weights[k]-w)<1e-6 for k,w in expected_weights.items()),'Saved weights differ'
            if repair:ob['dfm_material']=group['name']
        for image in bpy.data.images:
            if image.source=='FILE':assert Path(bpy.path.abspath(image.filepath)).exists(),image.filepath
        if repair:
            for text in list(bpy.data.texts):
                if text.name.startswith('README - native DFM metadata'):bpy.data.texts.remove(text)
            text=bpy.data.texts.new('README - native DFM metadata')
            text.write(json.dumps(dict(report=report,native_bones=data['bones'],
                note='Editable rest-pose meshes with UVs, normals and native weight groups. No animation rig. Source collection is hidden. Textures are linked to existing shared exports.'),indent=2))
            bpy.ops.wm.save_as_mainfile(filepath=str(folder/blend_name),compress=True)
        metadata=json.loads(bpy.data.texts['README - native DFM metadata'].as_string())
        assert metadata['report']['output_sha256']==report['output_sha256']
        valid.append(folder.name)
    except Exception as error:errors.append(dict(name=folder.name,error=repr(error),line=traceback.extract_tb(error.__traceback__)[-1].lineno))
(OUT/'blend_validation.json').write_text(json.dumps(dict(valid=valid,errors=errors),indent=2))
print('BLEND_CHECK',len(valid),'errors',errors,flush=True)
if errors:raise SystemExit(1)
