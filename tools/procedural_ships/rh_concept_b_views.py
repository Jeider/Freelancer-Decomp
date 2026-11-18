"""Read-only orthographic silhouette comparison against the user's chosen art views.

The original PNG is preserved byte-for-byte. SVG projections/landmarks are an
analysis layer in a local HTML document, not alterations to the reference art.
Landmarks are manually identified and approximate, not automatic edge detection.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import rh_concept_b_form as model
from rh_redesign_paths import WORK

OUT=WORK/'analysis/concept_b_master_views'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference',type=Path)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    reference=OUT/'reference_selected.png'
    if args.reference:
        if reference.exists():
            assert reference.read_bytes()==args.reference.read_bytes(), 'Preserve the existing selected art; use a new named reference for changes'
        else:shutil.copy2(args.reference,reference)
    assert reference.is_file()
    _,nodes=model.mesh.read_tree(model.DEST.read_bytes())
    poses={name:model.evaluate_pose(nodes,phase) for name,phase in [('open',0),('folded',1)]}
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in poses['folded']])
    low,high=points.min(0),points.max(0)
    length=high[2]-low[2]
    # Manual reference landmarks in the supplied 515x517 image.
    art=dict(side=dict(aft_x=87,nose_x=498,top_y=16,bottom_y=190,cabin_rear_x=421,
                       neck_body_x=337,brace_upper=[238,67],brace_lower=[213,156],hub=[175,86]),
             top=dict(nose_y=215,aft_y=440,axis_x=416,left_x=359,right_x=473,
                      port_panel_tip=[382,303],port_panel_root=[376,380],cabin_aft_y_range=[268,278]))
    side=art['side'];top=art['top']
    side_length=side['nose_x']-side['aft_x'];top_length=top['aft_y']-top['nose_y']
    side_scale=side_length/length;top_scale=top_length/length
    def project(p,view):
        if view=='side':return np.column_stack((side['nose_x']-(p[:,2]-low[2])*side_scale,
                                                side['bottom_y']-(p[:,1]-low[1])*side_scale))
        return np.column_stack((top['axis_x']+p[:,0]*top_scale,
                               top['nose_y']+(p[:,2]-low[2])*top_scale))
    def silhouette(scene,view):
        result=[]
        for group in scene:
            for tri in group['corners']:
                q=project(tri[:,:3],view)
                a,c=q[1]-q[0],q[2]-q[0]
                if abs(a[0]*c[1]-a[1]*c[0])<.002:continue
                result.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in q)+'"/>')
        # Group opacity is applied once to the union, not once per overlapping triangle.
        return ''.join(result)
    ref64=base64.b64encode(reference.read_bytes()).decode('ascii')
    brace=np.array([[1.75,(-1.20-1.19)/2,(1.25+2.16)/2],
                          [1.75,(2.66+2.91)/2,(3.17+2.65)/2]])
    # Endpoints measured from the authored shoulder contour in revision 03.
    brace_projection=project(brace,'side')
    panels=[]
    for view,box,clip,title in [('side','70 -32 450 242',(79,8,429,192),'Профиль — нос вправо'),
                               ('top','322 202 188 250',(345,207,140,244),'Вид сверху — нос вверх')]:
        x,y,w,h=clip
        silhouettes=''.join(f'<g class="mesh {pose}" fill="#0676db" opacity=".42" style="display:{"inline" if pose=="folded" else "none"}">{silhouette(scene,view)}</g>' for pose,scene in poses.items())
        marks=''
        if view=='side':
            a,c=side['brace_lower'],side['brace_upper'];b,d=brace_projection
            marks=f'<path d="M{a[0]},{a[1]} L{c[0]},{c[1]}" stroke="#e03c28" stroke-width="2.5"/><path d="M{b[0]},{b[1]} L{d[0]},{d[1]}" stroke="#0676db" stroke-width="2.5" stroke-dasharray="5 3"/>'
            for label,(mx,my) in [('верх опоры',c),('низ опоры',a)]:
                marks+=f'<circle cx="{mx}" cy="{my}" r="3" fill="#e03c28"/><text x="{mx+5}" y="{my-6}" font-size="8" fill="#9a1e15">{label}</text>'
        else:
            a,c=top['port_panel_tip'],top['port_panel_root']
            marks=f'<path d="M{a[0]},{a[1]} L{c[0]},{c[1]}" stroke="#e03c28" stroke-width="2"/><circle cx="{a[0]}" cy="{a[1]}" r="2" fill="#e03c28"/>'
        panels.append(f'''<section><h2>{title}</h2><svg viewBox="{box}" role="img" aria-label="{title}: арт и силуэт revision 03">
<defs><clipPath id="clip-{view}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs>
<image width="515" height="517" href="data:image/png;base64,{ref64}" clip-path="url(#clip-{view})"/>
{silhouettes}<g class="marks" fill="none">{marks}</g></svg></section>''')
    ratios=dict(side_height_over_length=dict(art=(190-16)/side_length,model=float((high[1]-low[1])/length)),
                side_cabin_length_over_ship_length=dict(art=(498-421)/side_length,model=float((-4.35-low[2])/length)),
                side_neck_length_over_ship_length=dict(art=(421-337)/side_length,model=float((-1.95+4.35)/length)),
                top_folded_width_over_length=dict(art=(473-359)/top_length,model=float((high[0]-low[0])/length)))
    rows=''.join(f'<tr><td>{name}</td><td>{values["art"]:.3f}</td><td>{values["model"]:.3f}</td></tr>' for name,values in [
        ('Высота / длина, сбоку',ratios['side_height_over_length']),('Кабина / длина, сбоку',ratios['side_cabin_length_over_ship_length']),
        ('Открытая шея / длина, сбоку',ratios['side_neck_length_over_ship_length']),('Ширина сложенного силуэта / длина, сверху',ratios['top_folded_width_over_length'])])
    html='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>RH B — основные проекции и расхождения revision 03</title><style>
body{font:17px/1.5 system-ui,sans-serif;margin:24px auto;max-width:1500px;padding:0 20px;color:#20272e;background:#eeece5}h1{font-size:28px}h2{font-size:20px;margin:10px 0}.controls{display:flex;gap:24px;flex-wrap:wrap;background:white;padding:16px;border-radius:8px;position:sticky;top:8px;z-index:2}.views{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-top:20px}section{background:#faf8f0;border:1px solid #c6c2b8;padding:14px;border-radius:8px}svg{width:100%;height:540px}table{border-collapse:collapse;background:white}th,td{text-align:left;padding:8px 18px;border:1px solid #c9c8c1}.note{max-width:1050px}button,select{font:inherit}input{vertical-align:middle}@media(max-width:850px){.views{grid-template-columns:1fr}svg{height:420px}}</style>
<h1>RH concept B: профиль и вид сверху — основные</h1>
<p class="note">Исходный арт сохранён без изменения пикселей. Синий слой — точная ортографическая проекция геометрии revision 03. Красным вручную отмечены опора и направление длинной панели. Это разбор прежней модели, новая геометрия здесь не предлагается.</p>
<div class="controls"><label><input id="show" type="checkbox" checked> Силуэт модели</label><label>Прозрачность <input id="alpha" type="range" min="0" max="1" step=".02" value=".42"></label><label>Поза <select id="pose"><option value="folded">Сложено вперёд</option><option value="open">Раскрыто</option></select></label><label><input id="marks" type="checkbox" checked> Опорные точки</label></div>
<div class="views">'''+''.join(panels)+'''</div>
<p class="note">Совмещены полная длина и нижняя граница профиля; сверху — длина и продольная ось. Масштаб равномерный, без растягивания силуэта по одной оси. Рисунок не считается точным ортографическим чертежом. Выбор позы меняет только модель: состояние механизма на рисунке ещё нужно согласовать с рабочими шарнирами.</p>
<h2>Приблизительные пропорции</h2><table><tr><th>Отношение</th><th>Арт</th><th>Revision 03</th></tr>'''+rows+'''</table>
<p class="note">Границы деталей на арте определены вручную; округлённые отношения служат диагностикой, а не допуском для автоматической приёмки. Размер исходной кабины защищён: совпадение пропорций потребует пересобрать окружающую композицию, а не произвольно масштабировать стекло.</p>
<p><a href="../../../../../docs/ru/ship_design/rh_concept_b_master_views.md">Подробный разбор и правила следующей итерации</a></p>
<script>const byId=id=>document.getElementById(id);function update(){document.querySelectorAll('.mesh').forEach(e=>{e.style.display=byId('show').checked&&e.classList.contains(byId('pose').value)?'inline':'none';e.setAttribute('opacity',byId('alpha').value)});document.querySelectorAll('.marks').forEach(e=>e.style.display=byId('marks').checked?'inline':'none')}['show','alpha','pose','marks'].forEach(id=>byId(id).addEventListener('input',update));update();</script></html>'''
    # HTML is five levels below the repository root.
    (OUT/'comparison.html').write_text(html,encoding='utf-8')
    report=dict(reference=str(reference),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                model=str(model.DEST),model_sha256=hashlib.sha256(model.DEST.read_bytes()).hexdigest(),
                authoring='manual landmark selection; no automatic image understanding or edge tracing claimed',
                landmarks=art,ratios=ratios,model_bounds_folded=[low.tolist(),high.tolist()],
                brace_model_native=brace.tolist(),brace_model_projected=brace_projection.tolist())
    (OUT/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(ratios,indent=2),flush=True)
    print('Saved',OUT/'comparison.html',flush=True)


if __name__=='__main__':main()
