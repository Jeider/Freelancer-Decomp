"""Create helmet-only heads, preserving skin, topology, UVs and animation data."""
import argparse, hashlib, json
from datetime import datetime
from io import BytesIO
import numpy as np
from PIL import Image
from scipy.ndimage import label
from build import GAME, ROOT, DataFolder, read_tree, write_tree, child, blob, arr, put, triangles, export
from repair_panel_normals import leaves

OUT = ROOT/'out/comm_hat'
NAMES = ('li_hatcher_head', 'br_darcy_head')

def digest(data): return hashlib.sha256(data).hexdigest()

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    stage = DataFolder(root=OUT/'stage')
    report = {}
    for name in NAMES:
        source = (GAME/'DATA/CHARACTERS/HEADS'/ (name+'.dfm')).read_bytes()
        header, roots = read_tree(source)
        root = roots[0]
        atlas = None
        if name == 'br_darcy_head':
            atlas = np.asarray(Image.open(BytesIO(blob(child(child(root,'Texture library'), 'br_darcy_head01.tga'), 'MIP0'))).convert('RGB'))/255.
            grey = (np.ptp(atlas,axis=2)<.13) & (atlas.max(axis=2)<.62)
            regions, _ = label(grey)
            counts = np.bincount(regions[:100].ravel()); counts[0] = 0
            hair_mask = regions == counts.argmax()
        def hair_sample(uv):
            u,v = uv
            # Only the grey region connected to the top hair, not eyebrows/eyelashes.
            return hair_mask[int((1-v)%1*(len(atlas)-1)), int(u%1*(atlas.shape[1]-1))]
        lods = []
        for mesh in child(root,'MultiLevel').children:
            if not mesh.name.startswith('Mesh'): continue
            geo = child(mesh,'Geometry')
            p = arr(geo,'Points','<f4',3); before = p.copy()
            pi = arr(geo,'Point_indices','<u4').ravel()
            ui = arr(geo,'UV0_indices','<u4').ravel(); uv = arr(geo,'UV0','<f4',2)
            hair, protected = set(), set()
            for group in child(mesh,'Face_groups').children:
                if not group.children: continue
                mat = blob(group,'Material_name').rstrip(b'\0').decode()
                for tri in triangles(group):
                    ids = pi[tri]
                    samples = [uv[ui[i]] for i in tri]
                    is_hair = mat == 'hatcher_hair_v1' or (atlas is not None and mat == 'br_darcy_head01' and
                        all(hair_sample(s) for s in samples+[np.mean(samples,axis=0)]))
                    (hair if is_hair else protected).update(map(int,ids))
            # Keep welded hairline/skin seams fixed on both sides.
            weld = {}
            for i,pos in enumerate(p): weld.setdefault(tuple(np.round(pos,5)),[]).append(i)
            for ids in weld.values():
                if any(i in protected for i in ids): protected.update(ids)
            movable = sorted(hair-protected)
            # Radial scalp envelope, no texture painting or face deformation.
            center = np.array([0., .052, .005])
            radii = np.array([.065, .093, .088])
            skin = before[sorted(protected)]
            for i in movable:
                delta = p[i]-center
                radius = np.linalg.norm(delta/radii)
                if radius > 1:
                    distance = np.linalg.norm(skin-before[i],axis=1).min()
                    blend = float(np.clip(distance/.032,0,1))
                    blend = blend*blend*(3-2*blend)
                    # Darcy has a separate fringe lying over the forehead. Tucking
                    # it radially would bury it under the skin and leave slivers.
                    if name == 'br_darcy_head' and before[i,2] > .035:
                        blend *= float(np.clip((before[i,1]-.12)/.035,0,1))
                    p[i] += (center+delta/radius-p[i])*blend
            assert np.array_equal(p[list(protected)], before[list(protected)])
            assert np.isfinite(p).all()
            put(geo,'Points',p.astype('<f4').tobytes())
            # Recompute changed hair normals, retaining original face normals exactly.
            normals = arr(geo,'Vertex_normals','<f4',3)
            accum = np.zeros_like(p)
            for group in child(mesh,'Face_groups').children:
                if not group.children: continue
                for tri in triangles(group):
                    ids = pi[tri]; a,b,c = p[ids]
                    n = np.cross(b-a,c-a)
                    for i in ids: accum[i] += n
            for i in movable:
                length = np.linalg.norm(accum[i])
                if length > 1e-12: normals[i] = accum[i]/length
            put(geo,'Vertex_normals',normals.astype('<f4').tobytes())
            geo.children = [n for n in geo.children if not n.name.startswith('Hair_motion_')]
            lods.append(dict(lod=mesh.name, changed=int(np.any(p!=before,axis=1).sum()), protected=len(protected), max_y=float(p[:,1].max())))
        # Unique material prevents opt-in hair relief on the helmet copy.
        for mat in child(root,'Material library').children:
            if mat.name == 'hatcher_hair_v1': mat.name = 'hatcher_hat_hair'
        for mesh in child(root,'MultiLevel').children:
            if not mesh.name.startswith('Mesh'): continue
            for group in child(mesh,'Face_groups').children:
                if group.children and blob(group,'Material_name').rstrip(b'\0') == b'hatcher_hair_v1':
                    put(group,'Material_name',b'hatcher_hat_hair\0')
        data = write_tree(header,roots)
        old_leaves = {path: value for path,_,value in leaves(source)[1]}
        new_leaves = {path.replace('/hatcher_hat_hair/','/hatcher_hair_v1/'): value for path,_,value in leaves(data)[1]}
        for path,value in old_leaves.items():
            if path.endswith(('/Points','/Vertex_normals','/Hair_motion_weights','/Hair_motion_bone')): continue
            expected = b'hatcher_hat_hair\0' if path.endswith('/Material_name') and value == b'hatcher_hair_v1\0' else value
            assert new_leaves[path] == expected, path
        rel = 'CHARACTERS/HEADS/'+name+'_hat.dfm'
        stage.sync_data_file(rel,data)
        export(read_tree(data)[1][0], OUT/(name+'_hat.json'))
        report[name] = dict(source_sha256=digest(source), output_sha256=digest(data), lods=lods)
    rel = 'CHARACTERS/bodyparts.ini'
    data = (GAME/'DATA'/rel).read_bytes()
    report['bodyparts_before'] = digest(data)
    for name in NAMES:
        if ('nickname = '+name+'_hat').encode() in data: continue
        line = ('mesh = characters\\heads\\'+name+'.dfm').encode()
        assert data.count(line) == 1
        eol = b'\r\n' if b'\r\n' in data else b'\n'
        addition = eol.join([b'',b'',b'[Head]',('nickname = '+name+'_hat').encode(),('mesh = characters\\heads\\'+name+'_hat.dfm').encode()])
        data = data.replace(line,line+addition)
    stage.sync_data_file(rel,data)
    report['bodyparts_after'] = digest(data)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

def install():
    stage = DataFolder(root=OUT/'stage'); live = DataFolder(root=GAME)
    report = json.loads((OUT/'validation.json').read_text())
    assert digest((GAME/'DATA/CHARACTERS/bodyparts.ini').read_bytes()) in (report['bodyparts_before'],report['bodyparts_after'])
    for name in NAMES:
        assert digest((GAME/'DATA/CHARACTERS/HEADS'/(name+'.dfm')).read_bytes()) == report[name]['source_sha256']
        assert digest(stage.data_path('CHARACTERS/HEADS/'+name+'_hat.dfm').read_bytes()) == report[name]['output_sha256']
    backup = DataFolder(root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for rel in ['CHARACTERS/HEADS/'+name+'_hat.dfm' for name in NAMES]+['CHARACTERS/bodyparts.ini']:
        if live.data_path(rel).exists(): backup.sync_data_file(rel,live.data_path(rel).read_bytes())
        data = stage.data_path(rel).read_bytes()
        live.sync_data_file(rel,data)
        assert live.data_path(rel).read_bytes() == data
    print('Installed both helmet heads and bodyparts entries; normal heads unchanged.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    if args.apply: install()
    else: build()
