"""Author the sill UV correction on the approved native shape, without installation."""
import collections
import json
from pathlib import Path
import numpy as np
import rh_concept_b_final as f

OUT=f.OUT.parent/'uv_refinement_01'
PANEL=f.mesh.crc('pir_r_panel01_256')
PANEL2=f.mesh.crc('pir_r_panel02_256')


def refine(groups,shift):
    edits=[];counts=collections.Counter()
    density=.98/6.6
    for gi,g in enumerate(groups):
        for ti,t in enumerate(g['corners']):
            p=t[:,:3]-shift
            x,y,z=p.T
            if z.min()<-.1001 or z.max()>6.5001:continue
            uv=None;kind=None
            # Each red backing fills the complete modeled recess, retaining the
            # authored panel's narrow painted perimeter, not its beige atlas field.
            if g['material']==PANEL2 and np.allclose(abs(x),1.97,atol=1e-4) and y.min()>=-.6001 and y.max()<=-.0599:
                a,b=next((a,b) for a,b in ((.3,2.),(2.18,3.9),(4.1,5.5)) if z.min()>=a-1e-4 and z.max()<=b+1e-4)
                # Pixel bounds manually inspected on the original 2048px atlas.
                # First vertical red strapped panel, including its thin rim.
                u0,u1=40/2048,300/2048;v0,v1=88/2048,936/2048
                uv=np.column_stack((u0+(y+.60)/.54*(u1-u0),v0+(z-a)/(b-a)*(v1-v0)))
                kind='red_panel_to_recess'
            elif g['material']==PANEL:
                # One chart over the complete existing frame. No resets at its
                # arbitrary triangulation/section boundaries; rails and uprights
                # share exactly the same physical-to-texture scale.
                if np.allclose(abs(x),2.05,atol=1e-4) and y.min()>=-.8001 and y.max()<=.1601:
                    uv=np.column_stack((.01+(z+.10)*density,.856+(.16-y)*density))
                    kind='continuous_side_frame'
                # Existing sloped lower edge, unrolled by actual surface distance.
                # This changes neither topology nor the approved hard-edged shape.
                elif (y.min()>=-1.1501 and y.max()<=-.7999 and np.min(abs(x))>=1.5499
                      and np.allclose(y,-1.15+(abs(x)-1.55)*.7,atol=1e-4)):
                    across=(2.05-abs(x))*np.sqrt(1+.7**2)
                    uv=np.column_stack((.01+(z+.10)*density,.87+across*density))
                    kind='continuous_bottom_slope'
                elif np.allclose(y,-1.15,atol=1e-4) and np.min(abs(x))>=.7999 and np.max(abs(x))<=1.5501 and np.ptp(z)>.001:
                    uv=np.column_stack((.01+(z+.10)*density,.87+(1.55-abs(x))*density))
                    kind='continuous_bottom_side_strip'
                elif np.allclose(y,.16,atol=1e-4) and np.min(abs(x))>=1.6499 and np.max(abs(x))<=2.0501 and np.ptp(z)>.001:
                    uv=np.column_stack((.01+(z+.10)*density,.87+(2.05-abs(x))*density))
                    kind='continuous_sill_top'
            if uv is not None:
                assert np.isfinite(uv).all() and uv.min()>0 and uv.max()<1
                edits.append(dict(group=gi,triangle=ti,material=g['material'],kind=kind,before=t[:,6:8].tolist(),after=uv.tolist(),positions=t[:,:3].tolist()))
                t[:,6:8]=uv;counts[kind]+=1
    assert counts['red_panel_to_recess']==12
    assert counts['continuous_side_frame']==72
    assert counts['continuous_bottom_slope']==20
    assert counts['continuous_bottom_side_strip']==4
    assert counts['continuous_sill_top']==20
    # Independent UV Jacobians: frame/slope/top/floor charts must have an
    # isotropic scale. Panels may fit the small differences between opening sizes.
    stretch={}
    for e in edits:
        t=groups[e['group']]['corners'][e['triangle']]
        stretch.setdefault(e['kind'],[]).append(f.b.prev.distortion(t))
    for kind,values in stretch.items():
        assert max(values)<(1.3 if kind=='red_panel_to_recess' else 1.0001),(kind,max(values))
    return edits,dict(counts),{k:max(v) for k,v in stretch.items()}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    _,nodes=f.mesh.read_tree(f.DEST.read_bytes())
    root=next(k for k,v in f.component_map(nodes).items() if v=='Root')
    groups=f.local_geometry(nodes)[root]
    before=[g['corners'][...,:6].copy() for g in groups]
    assembly=json.loads((f.OUT/'assembly.json').read_text());shift=np.array(assembly['center_shift_native'])
    edits,counts,stretch=refine(groups,shift)
    assert all(np.array_equal(a,g['corners'][...,:6]) for a,g in zip(before,groups))
    report=dict(base_cmp=str(f.DEST),base_cmp_sha256=f.digest(f.DEST),base_blend=str(f.OUT/'rh_concept_b_rigged.blend'),
                base_blend_sha256=f.digest(f.OUT/'rh_concept_b_rigged.blend'),shared_mat_sha256=f.digest(f.SHARED_MAT),
                center_shift_native=shift.tolist(),root_file=root,edits=edits,counts=counts,max_stretch=stretch,
                geometry_normals_materials_unchanged=True,stage='LOD0 mapping review; installation explicitly suspended by user')
    (OUT/'uv_changes.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (f.OUT/'installation_hold.json').write_text(json.dumps(dict(reason='User stopped installation for sill/bottom UV corrections',review=str(OUT)),indent=2))
    native=json.loads((f.OUT/'checks.json').read_text())
    (f.OUT/'README.md').write_text(f'''# RH concept B — подготовленная сборка, установка остановлена

Хвост из `../tail_prototype_01/` утверждён пользователем и перенесён в этот CMP.
Задний люк и четыре пилона находятся на отделяемой средней стойке. Верхняя и
нижняя рама, барабан и его опоры остаются на Root. Геометрия центрирована вместе
с анимационной иерархией и хардпоинтами.

**Текущая правка: [маппинг борта и днища](../uv_refinement_01/README.md).**
Пользователь остановил установку до её просмотра. В этом CMP ещё предыдущие UV;
новая развертка находится в Blender-файле соседней папки. Установщик блокируется
файлом `installation_hold.json`. Подготовленный `install/` также относится к
предыдущим UV и не должен устанавливаться.

## Подготовленные игровые ресурсы

- CMP: `rh_concept_b.cmp`, без Material library и Texture library.
- SUR: `rh_concept_b.sur`, проверены проём над барабаном и отделение средней стойки.
- LOD0/1/2: {native['lods']}, новый выступ присутствует во всех уровнях.
- Wireframe ссылается на LOD1; диагонали плоских поверхностей и UV-разрывы исключены.
- 10 damage 3DB и 10 SUR в `damage/`, без встроенных текстур.
- `rh_concept_b_lods.mat`: только два DXT1-атласа LOD, по 12 mip-уровней.
  Общий пользовательский `rh_pir_playerships.mat` не изменён.
- `shiparch_fragment.ini` и подготовленный `install/shiparch.diff` содержат связи
  новых разрушений и MAT. Характеристики и cockpit исходного корабля сохранены.

Протоколы: `checks.json`, `motion_intersections.json`, `blend_checks.json`,
`tail_integration.json`, `collision_manifest.json`, `lod_materials.json`.
Анимация проверена на 121 фазе крыльев и 61 фазе дверей; пересечений нет.
18 фаз повторно открытого Blender совпали с чтением CMP. Это офлайн-проверки;
игра не запускалась и новая сборка в DATA не установлена.

После принятия UV требуется перенести исправление в CMP и дальние атласы,
обновить отдельный MAT, предпросмотр и подготовку установщика. Старый ZIP этой
папки не является актуальным комплектом.
''',encoding='utf8')
    sections=[]
    for name,title in (('side_strip','Панели и обрамление'),('bottom_corner','Угол днища'),('underside','Вид снизу')):
        sections.append(f'<h2>{title}</h2><div class="pair"><figure><img src="before_{name}.png"><figcaption>До</figcaption></figure><figure><img src="after_{name}.png"><figcaption>После</figcaption></figure></div>')
    (OUT/'comparison.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><title>RH B — UV до/после</title>'
        '<style>body{font:16px system-ui;background:#1c2027;color:#eef0f5;margin:24px}a{color:#8cd5ff}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0}img{width:100%;display:block}figcaption{padding:8px}h2{margin-top:32px}@media(max-width:850px){.pair{grid-template-columns:1fr}}</style>'
        '<h1>RH concept B — исправленная развертка</h1><p>Одинаковые камера и свет. Геометрия, материалы и текстуры сохранены; изменены UV 128 треугольников.</p>'
        '<p><a href="rh_concept_b_uv_review.blend">Blender</a> · <a href="README.md">Описание</a>. Установка в игру остановлена.</p>'+''.join(sections)+'</html>',encoding='utf8')
    print('UV CORRECTIONS',counts,'MAX STRETCH',stretch,flush=True)


if __name__=='__main__':main()
