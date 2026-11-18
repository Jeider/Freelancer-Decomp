"""Read existing shield hulls and check the accepted Q13; never writes game assets."""
import re
import numpy as np
from scipy.spatial import ConvexHull
import rh_freighter_hold_repair as h
from ship_collision_audit import sur_parts,surface
from rh_concept_b_v2_sur import read_hulls
d=h.d;f=d.f

def root_surface(path):
    chunks=next(v for pid,v in sur_parts(path.read_bytes()) if pid==f.mesh.crc('Root'))
    blob=next(v for tag,v in chunks if tag==b'surf')
    ids=next(v for tag,v in chunks if tag==b'hpid')
    return read_hulls(blob),surface(blob),[int(n) for n in np.frombuffer(ids,'<u4')]

def main():
    cmp=h.OUT/'rh_pir_freighter.cmp';sur=h.LIVE.with_suffix('.sur')
    _,nodes=d.tree(cmp);hp=d.hardpoints(nodes,('Sc_extend wing',0))
    hulls,stats,ids=root_surface(sur);shieldid=f.mesh.crc('HpMount')
    shield=next(p for cid,p in hulls if cid==shieldid)
    cv=ConvexHull(shield);assert shieldid in ids and f.mesh.crc('HpShield01') in ids
    assert sum(cid==shieldid for cid,p in hulls)==1
    records=[]
    for pose,label in [(('Sc_extend wing',0),'extended flight'),(None,'folded'),(('Sc_rh_freighter',1),'cargo open')]:
        for name,gs in d.world(nodes,pose).items():
            p=d.points(gs);outside=np.max(p@cv.equations[:,:3].T+cv.equations[:,3],axis=1)
            records.append(dict(pose=label,part=name,vertices_tested=len(p),outside=int((outside>1e-4).sum()),
                                minimum_plane_margin=float(-outside.max())))
    equipment=[];names={f.mesh.crc(v['name']):k for k,v in hp.items()}
    for cid,p in hulls:
        if cid==shieldid or cid not in names:continue
        outside=np.max(p@cv.equations[:,:3].T+cv.equations[:,3],axis=1)
        equipment.append(dict(name=hp[names[cid]]['name'],vertices=len(p),outside=int((outside>1e-4).sum())))
    assert all(r['outside']==0 for r in records+equipment)
    shiparch=d.GAME/'DATA/SHIPS/shiparch.ini';text=shiparch.read_text(encoding='cp1251')
    section=next(s for s in re.split(r'(?m)^\[Ship\]\s*$',text) if re.search(r'(?mi)^nickname\s*=\s*rh_freighter_pir\s*$',s))
    link=re.search(r'(?mi)^shield_link\s*=\s*(.*)$',section).group(1).strip()
    assert link.lower()=='r_freighter_shield01, hpmount, hpshield01'
    shield3db=d.GAME/'DATA/Ships/rheinland/rh_freighter/rh_freighter_shield.3db'
    _,sh=d.tree(shield3db);leaves=[p for p,n in f.mesh.walk(sh)]
    assert any('/SpConnect/' in p for p in leaves)
    has_mesh=any('/vmesh' in p.lower() for p in leaves)
    _,original,_=root_surface(d.SOURCE/'original.sur')
    report=dict(cmp_path=str(cmp),cmp_sha256=f.digest(cmp),sur_path=str(sur),sur_sha256=f.digest(sur),
        shield=next(r for r in stats['hulls'] if r['client']==shieldid),shield_hpid_present=True,
        generator_hull_present=any(cid==f.mesh.crc('HpShield01') for cid,p in hulls),
        coverage=records,equipment=equipment,
        original_shield=next(r for r in original['hulls'] if r['client']==shieldid),
        shiparch_shield_link=link,shield_attachment_3db=dict(path=str(shield3db),sha256=f.digest(shield3db),
            has_render_mesh=has_mesh,leaves=leaves),
        result='Existing embedded shield covers the accepted model and equipment; no extra shield SUR needed',
        game_writes=False)
    d.dump(h.OUT/'shield_check.json',report)
    print('PASS: shield',report['shield']['triangles'],'triangles;',len(equipment),'equipment hulls;',len(records),'part/pose checks; no uncovered vertices')

if __name__=='__main__':main()
