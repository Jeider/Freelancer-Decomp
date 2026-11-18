"""Review the actual revision-04 CMP against both selected art projections."""
import base64
import hashlib
import json

import numpy as np
import rh_concept_b_profile as new
from rh_redesign_paths import CONCEPT_B_FORM

OUT=new.OUT
REF=new.REFERENCE
ART=json.loads((REF.parent/'measurements.json').read_text(encoding='utf-8'))['landmarks']

def main():
    models={}
    ratios={}
    for revision,folder in ((3,CONCEPT_B_FORM),(4,OUT)):
        cmp=folder/'rh_concept_b_lod0.cmp'
        _,nodes=new.mesh.read_tree(cmp.read_bytes())
        poses={name:new.native.evaluate_pose(nodes,phase) for name,phase in [('open',0),('folded',1)]}
        points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in poses['folded']])
        low,high=points.min(0),points.max(0);length=high[2]-low[2]
        models[revision]=(poses,low,high,length)
        ratios[revision]=dict(side_height_over_length=float((high[1]-low[1])/length),
                             side_cabin_over_length=float((-4.35-low[2])/length),
                             side_neck_over_length=float((4.35+(-1.95 if revision==3 else -.10))/length),
                             folded_width_over_length=float((high[0]-low[0])/length),
                             length=float(length),bounds=[low.tolist(),high.tolist()],
                             sha256=hashlib.sha256(cmp.read_bytes()).hexdigest())
    def projection(rev,phase,view):
        poses,low,high,length=models[rev]
        result=[]
        for g in poses[phase]:
            for tri in g['corners']:
                p=tri[:,:3]
                if view=='side':
                    scale=(498-87)/length
                    q=np.column_stack((498-(p[:,2]-low[2])*scale,190-(p[:,1]-low[1])*scale))
                else:
                    scale=(440-215)/length
                    q=np.column_stack((416+p[:,0]*scale,215+(p[:,2]-low[2])*scale))
                a,c=q[1]-q[0],q[2]-q[0]
                if abs(a[0]*c[1]-a[1]*c[0])<.002:continue
                result.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in q)+'"/>')
        return ''.join(result)
    ref=base64.b64encode(REF.read_bytes()).decode('ascii')
    panels=[]
    for view,box,clip,title in [('side','72 -18 440 222',(79,8,429,192),'Профиль — нос вправо'),
                               ('top','320 202 194 250',(345,207,140,244),'Вид сверху — нос вверх')]:
        x,y,w,h=clip
        layers=[]
        for rev in (3,4):
            for phase in ('open','folded'):
                color='#0873c0' if rev==4 else '#c64b2b'
                layers.append(f'<g class="model" data-revision="{rev}" data-phase="{phase}" fill="{color}" opacity=".4">{projection(rev,phase,view)}</g>')
        panels.append(f'<section><h2>{title}</h2><svg viewBox="{box}"><defs><clipPath id="{view}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs><image width="515" height="517" href="data:image/png;base64,{ref}" clip-path="url(#{view})"/>'+''.join(layers)+'</svg></section>')
    art=dict(side_height_over_length=(190-16)/411,side_cabin_over_length=77/411,
             side_neck_over_length=84/411,folded_width_over_length=114/225)
    labels={'side_height_over_length':'Высота / длина','side_cabin_over_length':'Кабина / длина',
            'side_neck_over_length':'Шея / длина','folded_width_over_length':'Сложенная ширина / длина'}
    rows=''.join(f'<tr><td>{label}</td><td>{art[key]:.3f}</td><td>{ratios[3][key]:.3f}</td><td>{ratios[4][key]:.3f}</td></tr>' for key,label in labels.items())
    html='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RH B — revision 04 и выбранный арт</title>
<style>body{font:17px/1.5 system-ui,sans-serif;background:#eeece5;color:#20272e;max-width:1500px;margin:24px auto;padding:0 20px}h1{font-size:28px}h2{font-size:20px}.controls{display:flex;flex-wrap:wrap;gap:24px;position:sticky;top:8px;padding:16px;background:white;z-index:2;border-radius:8px}.views{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-top:20px}section{padding:12px;background:#faf8f0;border:1px solid #c6c2b8;border-radius:8px}svg{width:100%;height:540px}select{font:inherit}table{border-collapse:collapse;background:white}td,th{padding:8px 18px;border:1px solid #c9c8c1;text-align:left}.renders{display:grid;grid-template-columns:1fr 1fr;gap:20px}.renders img{width:100%}video{max-width:100%}@media(max-width:850px){.views,.renders{grid-template-columns:1fr}svg{height:420px}}</style>
<h1>RH concept B — revision 04</h1><p>Основные ориентиры: выбранные боковой профиль и вид сверху. Синий слой — геометрия нового CMP; красный — revision 03. Референс сохранён без изменения пикселей.</p>
<div class="controls"><label>Модель <select id="revision"><option value="4">Новая — revision 04</option><option value="3">Прежняя — revision 03</option><option value="both">Обе</option><option value="none">Только арт</option></select></label><label>Поза <select id="phase"><option value="folded">Крылья вдоль корпуса</option><option value="open">Крылья раскрыты</option></select></label><label>Прозрачность <input id="alpha" type="range" min="0" max="1" step=".02" value=".4"></label></div>
<div class="views">'''+''.join(panels)+'''</div><p>Масштаб равномерный, по полной длине корабля. Сбоку совмещена нижняя граница, сверху — продольная ось. Ручные измерения рисунка приблизительные; это сравнение формы, не инженерный допуск.</p>
<table><tr><th>Отношение</th><th>Арт</th><th>Revision 03</th><th>Revision 04</th></tr>'''+rows+'''</table>
<p>Сохранено исходное стекло и положение пилота/камеры. Кабина поэтому не обязана повторять каждую линию рисунка. Неоднозначную толщину и поперечные соединения пришлось интерпретировать. Все показанные формы присутствуют в CMP; дополнительных деталей только для рендера нет.</p>
<div class="renders"><section><h2>Раскрыто</h2><img src="geometry_open.png" alt="Новая геометрия: крылья раскрыты"></section><section><h2>Сложено вперёд</h2><img src="geometry_folded.png" alt="Новая геометрия: крылья сложены"></section><section><h2>Сбоку</h2><img src="geometry_side.png" alt="Профиль модели"></section><section><h2>Сверху</h2><img src="geometry_top_folded.png" alt="Вид сверху со сложенными крыльями"></section></div>
<h2>Движение механизма</h2><video controls loop muted preload="metadata" src="wing_mechanism.mp4"></video>
<p><a href="README.md">Изменения, ограничения и проверки</a></p>
<script>function update(){let rev=document.getElementById('revision').value,phase=document.getElementById('phase').value,alpha=document.getElementById('alpha').value;document.querySelectorAll('.model').forEach(e=>{e.style.display=(e.dataset.revision===rev||rev==='both')&&e.dataset.phase===phase?'inline':'none';e.setAttribute('opacity',alpha)})}['revision','phase','alpha'].forEach(id=>document.getElementById(id).addEventListener('input',update));update();</script></html>'''
    (OUT/'comparison.html').write_text(html,encoding='utf-8')
    (OUT/'projection_measurements.json').write_text(json.dumps(dict(art=art,models=ratios,method='manual reference landmarks; orthographic projection of decoded CMP triangles; equal scale along both axes'),indent=2),encoding='utf-8')
    print(json.dumps(ratios,indent=2))

if __name__=='__main__':main()
