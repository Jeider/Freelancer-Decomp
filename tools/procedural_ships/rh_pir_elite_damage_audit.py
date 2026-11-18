"""Read-only source-model, component wire and engine-cap comparison."""
import json
from pathlib import Path
import struct as S
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rh_pir_elite_build as b
from rh_concept_b_damage_reference import groups
from preview import render

f = b.f
OUT = b.OUT / 'damage_review'
DATA = Path('D:/Games/FL_MOD/DATA')


def parts(nodes, pose=None):
    transforms, _ = f.audit.transforms(nodes, pose)
    lib = {f.mesh.crc(p.split('/')[-2]): f.audit.decode(n.blob)
           for p, n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    result = {}
    for file, owner in f.component_map(nodes).items():
        part = f.mesh.child(nodes[0], file)
        gs = [g for path, node in f.mesh.walk([part])
              if path.lower().endswith('/vmeshref') and
              ('/multilevel/' not in path.lower() or '/level0/' in path.lower())
              for g in f.audit.extract(node.blob, lib)]
        if gs:result[owner] = f.base.world(gs, *transforms[file.lower()])
    return result


def main():
    OUT.mkdir(exist_ok=True)
    sources = [DATA / 'ships/rheinland/rh_elite/rh_elite.cmp',
               DATA / 'ships/rheinland/rh_elite/rh_alt_elite.cmp',
               DATA / 'ships/rheinland/rh_pir_elite/rh_pir_elite.cmp',
               DATA / 'ships/liberty/li_elite/li_elite.cmp',
               DATA / 'ships/order/or_elite/or_elite.cmp']
    report = []
    for source in sources:
        _, nodes = f.mesh.read_tree(source.read_bytes())
        lib = {f.mesh.crc(p.split('/')[-2]): f.audit.decode(n.blob)[0]
               for p, n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
        tr, _ = f.audit.transforms(nodes)
        script_start, _ = f.audit.transforms(nodes, ('Sc_extend wing', 0))
        script_end, _ = f.audit.transforms(nodes, ('Sc_extend wing', 1))
        constructs = []
        for path, node in f.mesh.walk(nodes):
            if '/cmpnd/cons/' not in path.lower():
                continue
            kind = path.rsplit('/', 1)[-1].lower()
            size = {'fix': 176, 'rev': 208, 'pris': 208}[kind]
            for at in range(0, len(node.blob), size):
                constructs.append(dict(kind=kind,
                    parent=f.mesh.string(node.blob[at:at+64]),
                    child=f.mesh.string(node.blob[at+64:at+128])))
        wire = []
        for file, owner in f.component_map(nodes).items():
            part = f.mesh.child(nodes[0], file)
            w = next((n for n in part.children if n.name.lower() == 'vmeshwire'), None)
            if w is None:
                continue
            raw = f.mesh.child(w, 'VWireData').blob
            _, crc, bias, nv, ni, count = S.unpack_from('<II4H', raw)
            ids = np.frombuffer(raw, '<u2', offset=16)
            if not len(ids):
                wire.append(dict(owner=owner, edges=0))
                continue
            ps = lib[crc][bias + ids, :3]
            r, t = tr[file.lower()]; ur, ut = script_start[file.lower()]
            er, et = script_end[file.lower()]
            wire.append(dict(owner=owner, edges=int(len(ids)//2),
                             local_bounds=[ps.min(0), ps.max(0)],
                             rest_bounds=[(ps@r.T+t).min(0), (ps@r.T+t).max(0)],
                             script_start_bounds=[(ps@ur.T+ut).min(0), (ps@ur.T+ut).max(0)],
                             script_end_bounds=[(ps@er.T+et).min(0), (ps@er.T+et).max(0)]))
        modelparts = parts(nodes)
        hp = f.hp_world(nodes)
        stats = []
        for owner, gs in modelparts.items():
            ps = np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs])
            stats.append(dict(owner=owner, triangles=sum(len(g['corners']) for g in gs),
                              rest_bounds=[ps.min(0), ps.max(0)]))
        report.append(dict(source=str(source), sha256=f.digest(source),
                           pose_samples='Sc_extend wing: first and last keys; not assumed to be unfolded',
                           constructs=constructs, wire=wire, parts=stats))
        if source.stem not in ('rh_elite', 'rh_pir_elite'):
            continue
        cap = source.with_name(source.stem + '_dmg_port_engine.3db')
        damaged = groups(cap)
        anchor = hp['dpport_engine']
        # Cap DpConnect is not assumed to be zero in original assets.
        _, cap_nodes = f.mesh.read_tree(cap.read_bytes())
        leaves = {p.lower(): n for p, n in f.mesh.walk(cap_nodes)}
        pos = next(n for p, n in leaves.items() if p.endswith('/dpconnect/position'))
        rot = next(n for p, n in leaves.items() if p.endswith('/dpconnect/orientation'))
        cr = np.frombuffer(rot.blob, '<f4').reshape(3,3)
        ct = np.frombuffer(pos.blob, '<f4')
        hr = np.array(anchor['orientation']); ht = np.array(anchor['position'])
        damaged = f.base.world(damaged, hr @ cr.T, ht - hr @ cr.T @ ct)
        engine = next(gs for name, gs in modelparts.items() if name.lower() == 'rh_port_engine_lod1')
        points = np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in engine+damaged])
        center=(points.min(0)+points.max(0))*.5
        radius=np.linalg.norm(points-center,axis=1).max()*1.25
        library = DATA / ('ships/rheinland/rh_pir_playerships.mat' if source.stem=='rh_pir_elite'
                          else 'ships/rheinland/rh_playerships.mat')
        mats=f.audit.material_table([library])
        for label, geometry in (('healthy',engine), ('damaged',damaged)):
            render(geometry,mats,center,radius,(-1,-.65,1),size=700,mode='texture').save(OUT/(source.stem+'_'+label+'.png'))
        report[-1]['engine_cap'] = dict(file=str(cap), triangles=sum(len(g['corners']) for g in damaged),
                                        world_bounds=[np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in damaged]).min(0),
                                                      np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in damaged]).max(0)],
                                        hp=anchor)
    (OUT/'models.json').write_text(json.dumps(report,default=b.v.hp.serial,indent=2),encoding='utf-8')
    sheet=Image.new('RGB',(1400,1520),'#14222b');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
    for row, model in enumerate(('rh_elite','rh_pir_elite')):
        for col, state in enumerate(('healthy','damaged')):
            sheet.paste(Image.open(OUT/(model+'_'+state+'.png')),(col*700,row*760+60))
            draw.text((col*700+20,row*760+15),model+' — '+('двигатель целый' if state=='healthy' else 'остаток после разрушения'),font=font,fill='white')
    sheet.save(OUT/'engine_comparison.png')
    print(json.dumps([{ 'model':Path(r['source']).name, 'wire':[(w['owner'],w['edges']) for w in r['wire']],
                       'engine_cap':r.get('engine_cap',{}).get('triangles')} for r in report],indent=2))


if __name__=='__main__':main()
