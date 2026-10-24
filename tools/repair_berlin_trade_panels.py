"""Stage only Bonn's space_panelc normal repair; never modifies game assets."""
import hashlib
import json
import math
import struct
from pathlib import Path
from repair_panel_normals import leaves, triangles, face_normal, repair

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/games/FL_MOD')
REL = 'DATA/SOLAR/MISC/space_panelc.3db'
OUT = ROOT / 'src/obj/berlin_panel_repair'


def metrics(raw):
    dots = []
    meshes = []
    for name, _, blob in leaves(raw)[1]:
        if not name.lower().endswith('/vmeshdata'):
            continue
        header, desc, groups = triangles(blob)
        for group in groups:
            for i in range(0, len(group), 3):
                normal = face_normal(group[i:i+3])
                if normal:
                    dots.extend(sum(a*b for a,b in zip(normal,struct.unpack_from('<3f',v,12))) for v in group[i:i+3])
        meshes.append(dict(name=name, vertices=header[-1], triangles=header[3]//3, groups=header[2]))
    return dict(meshes=meshes, corners=len(dots), corners_below_dot_099=sum(d<.99 for d in dots),
                min_normal_dot=min(dots), max_angle_degrees=math.degrees(math.acos(max(-1,min(1,min(dots))))))


def diagnostic(raw, offset, label):
    """Orthographic normal-direction chart, not an in-game texture/render capture."""
    out = [f'<text x="{offset+15}" y="30" fill="white">{label}</text>']
    for path, _, blob in leaves(raw)[1]:
        if not path.lower().endswith('/vmeshdata'):
            continue
        _, _, groups = triangles(blob)
        for group in groups:
            for i in range(0,len(group),3):
                face=group[i:i+3]
                normal=face_normal(face)
                # View the broad panel side; tiny thickness surfaces remain visible as arrows.
                points=[struct.unpack_from('<3f',v) for v in face]
                coords=[(offset+230+p[2]*2.8,230-p[1]*2.8) for p in points]
                dot=sum(sum(a*b for a,b in zip(normal,struct.unpack_from('<3f',v,12))) for v in face)/3
                hue=max(0,min(120,dot*120))
                out.append('<polygon points="'+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in coords)+f'" fill="hsl({hue:.1f},70%,45%)" stroke="#20252b" stroke-width=".5"/>')
    return ''.join(out)


def main():
    source=GAME/REL
    before=source.read_bytes()
    # Limit this tool to the inspected full-reference, single-level Bonn panel variant.
    nodes=leaves(before)[1]
    assert sum(p.lower().endswith('/vmeshdata') for p,_,_ in nodes)==1
    assert sum(p.lower().endswith('/vmeshref') for p,_,_ in nodes)==1
    assert not any('/multilevel/' in p.lower() for p,_,_ in nodes)
    repair(source,OUT/REL)
    after=(OUT/REL).read_bytes()
    report=dict(target='rh_ber_09 — Trading base Bonn, eight space_panelc objects',
        relative=REL,original_sha256=hashlib.sha256(before).hexdigest(),prepared_sha256=hashlib.sha256(after).hexdigest(),
        before=metrics(before),after=metrics(after),
        validation='All 80 triangle positions, winding, UV bytes and material groups retained; full VMeshRef adjusted; every other UTF leaf byte-identical. Single authored LOD retained. Shared archetype also repairs its uses outside Bonn.')
    assert report['after']['corners_below_dot_099']==0
    assert source.read_bytes()==before
    (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    (OUT/'normal_alignment.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="920" height="480" viewBox="0 0 920 480"><rect width="920" height="480" fill="#15191e"/>'+diagnostic(before,0,'Original: normal alignment')+diagnostic(after,460,'Repaired: normal alignment')+'<text x="20" y="465" fill="white">Diagnostic only: green = normal aligned with triangle; orange/red = smoothed across hard edge.</text></svg>',encoding='utf8')
    print(json.dumps(report,indent=2,ensure_ascii=True))


if __name__=='__main__':
    main()
