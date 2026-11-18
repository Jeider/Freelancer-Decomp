"""Document and hash the validated model without retaining duplicate packages."""
import html
import json
from pathlib import Path
import rh_concept_b_final as f

OUT=f.OUT


def build():
    checks=json.loads((OUT/'checks.json').read_text());blend=json.loads((OUT/'blend_checks.json').read_text())
    assert checks['cmp_sha256']==blend['cmp_sha256']==f.digest(f.DEST)
    assert blend['blend_sha256']==f.digest(OUT/'rh_concept_b_rigged.blend')
    assembly=json.loads((OUT/'assembly.json').read_text());review=json.loads((OUT/'review_data.json').read_text())
    uv=json.loads((OUT/'uv_integration.json').read_text())
    assert uv['cmp_sha256']==checks['cmp_sha256'] and uv['lod_mat_sha256']==f.digest(f.LOD_MAT)
    installed=False
    if (OUT/'installation.json').exists():
        installation=json.loads((OUT/'installation.json').read_text())
        installed=installation.get('installed_verified',False) and installation['cmp_sha256']==checks['cmp_sha256']
    status=('Установлено для существующего архетипа `rh_elite_pir`; файлы сверены после записи.'
            if installed else 'Подготовлено к установке для существующего архетипа `rh_elite_pir`.')
    lods=checks['lods']
    readme=f'''# RH concept B — final_v1

Чистовая сборка по утверждённой revision 08 с принятыми выступом хвоста и UV,
17 ноября 2026. {status}
Игра не запускалась. Движок не изменялся.

[Просмотр модели, LOD и разрушения](comparison.html) ·
[CMP](rh_concept_b.cmp) · [SUR](rh_concept_b.sur) ·
[Blender](rh_concept_b_rigged.blend) · [Отдельный LOD MAT](rh_concept_b_lods.mat) ·
[INI-фрагмент](shiparch_fragment.ini).

## Последние принятые правки

- На средней задней стойке tail — угловатый люк и четыре пилона на основе
  подлинной исходной rh_pir_elite (`rh_pir_elite1.cmp`). Добавлено 84 треугольника
  в каждом LOD. Верхняя/нижняя рама и барабан остаются на Root при разрушении.
- CM, мины и два форсажа стоят на хвостовых пилонах и принадлежат tail.
- Начало координат перенесено по центру габаритов раскрытого исходника;
  геометрия, корневые hardpoints и дочерние начала координат смещены согласованно.
  Это геометрическое центрирование, не изменение физического центра массы.
- Одобрены [UV борта и днища](../uv_refinement_01/README.md): панели заполняют
  вырезы, длинные рамки и скосы имеют непрерывную развертку. Перенесены 128
  треугольников / 384 UV-угла; геометрия и анимация не менялись. Оба дальних
  атласа обновлены по этим UV с сохранением остальных участков.
- Wireframe построен по второму LOD (LOD1), без диагоналей плоских поверхностей
  и линий на UV-разрывах; границы и выраженные рёбра сохранены.
- CMP и damage 3DB не содержат Material/Texture library. Общий пользовательский
  MAT сохранён. Два новых атласа находятся только в отдельном LOD MAT:
  DDS/DXT1 с 12 mip-уровнями, проверенные отдельным D3D9-тестом загрузки.

## Состав

| Уровень | Треугольники | Начальная дистанция |
|---|---:|---:|
| LOD0 | {lods[0]} | 0 |
| LOD1 | {lods[1]} | 180 |
| LOD2 | {lods[2]} | 550 |

Дальний предел 10000. Три уровня находятся внутри одного CMP, у всех частей
согласованные Switch2. INI использует те же границы. Переходы подобраны как
исходные значения для новой модели; окончательное восприятие дистанций проверяет
пользователь в игре. LOD1/2 используют отдельные атласы 2048², перенесённые с LOD0,
а кабина и остекление сохраняют геометрию ближнего уровня.
Дальние уровни сохраняют части и механизм.

Ближняя форма, пиратские текстуры и острые контуры revision 08 сохранены.
При чистовой подготовке изменены разделение частей, скрытые зазоры дверей,
закрытие плоскости отрыва и технические вырожденные треугольники; затем внесены
одобренные хвост и UV, описанные выше. Новых фасок, заклёпок и балки
между крышей корпуса и верхом tail нет.

## Части и разрушение

- **Root:** корпус, кабина, барабан со всеми опорами, верхняя и нижняя части рамы.
  Барабан — 436 исходных треугольников, перенесённых без изменения поверхности.
- **Rh_tail_lod1:** задняя стойка с люком и пилонами между Y=0.70 и Y=3.90
  в координатах формы до центрирования.
  Это последнее уточнение пользователя: верх, низ и барабан при повреждении сохраняются.
  Два разреза закрыты; заглушка повреждений имеет отдельные физические оболочки
  у верхнего и нижнего срезов, не заполняя исчезнувшую стойку невидимой коллизией.
- **Rh_*_upperarm:** неподвижные П-образные пазы. Вращательная механика скрыта.
- **Rh_*_wing_lod1:** отдельные крылья; вооружение и огни принадлежат крылу.
- **Rh_*_engine_lod1:** отдельные двигатели, эффекты и точки массы на своих частях.
- Стекло и две двери трюма — отдельные исходные логические компоненты.

Пять отделяемых зон: два крыла, два двигателя, tail. Для каждой сделаны две
3DB-заглушки: на оставшемся корабле и на отлетевшем обломке. Итого **10 заглушек**
с DpConnect, самостоятельными SUR и пиратскими материалами повреждений.
Они моделируют неровный срез обшивки и утопленную внутреннюю структуру.
В shiparch_fragment.ini связаны dmg_hp/dmg_obj и group_dmg_hp/group_dmg_obj;
DpBreak находится на самой отделяемой части, поэтому учитывает её текущую позу.
Физическая оболочка пересобрана по новым частям; большой просвет над барабаном
не заполнен единым выпуклым корпусом. Идентификаторы оружейных креплений SUR
перенесены из схемы исходного корабля на новые координаты и владельцев.

## Анимация и hardpoints

Крыло вращается вперёд и внутрь на **62°** вокруг локальной ±Y, ось в раскрытой
позе до центрирования: ±3.05, −0.50, 7.80. Паз не вращается. Основной цикл — 2 секунды;
Sc_launch extend сохраняет исходную длительность 7 секунд (5 секунд ожидания,
2 секунды раскрытия), затем без скачка переходит в начало Sc_extend wing.
Сохранены используемые скрипты остановки/удержания и отдельный Sc_open baydoor.
Длительность и углы исходных дверей сохранены, посадка получила реальный зазор.

Все **{checks['original_hardpoints']} исходных именованных hardpoint** сохранены.
Исправлены нижние орудия/торпедный узел у придвинутой кабины, огни, оборудование,
байдор-точки и разрушение. Добавлен объявленный в исходном INI HpHardware01,
которого не было в исходном CMP, и по DpBreak на пяти отделяемых частях.
В Blender всего {len(review['hardpoints'])} маркеров с исходными локальными ориентациями.
Мины/контрмеры и два форсажа принадлежат отделяемой хвостовой стойке;
верхний/нижний хвостовой свет и верхняя/нижняя турели остаются на Root. Логические слоты оборудования не
подгоняются к внешней поверхности. Начало выхлопа намеренно находится за соплом.

## Blender

Коллекции LOD0/1/2, Hardpoints, Damage caps и Debris caps раздельные.
По умолчанию виден LOD0; остальные коллекции скрыты и во вьюпорте, и в рендере.
Все используемые изображения упакованы. На таймлайне есть отметки раскрытия,
складывания и открытия трюма. Дополнительные пустышки показывают hardpoints;
пушки остаются отдельными игровыми моделями.

## Проверки

- Полное повторное чтение CMP, десяти 3DB, всех SUR и INI-ссылок.
- LOD0/1/2: индексы, материалы, числа, нормали, невырожденные треугольники и границы.
  Максимум {checks['directx']['max_vertices']} вершин и {checks['directx']['max_indices']}
  индексов на VMesh, лимит 65535.
- {checks['channels']} каналов: родители, размеры ключей, оси и непрерывность launch → wing.
- 121 фаза складывания, включая контакты с пазом: пересечений нет.
- 61 фаза дверей с корпусом/стеклом/рамой: пересечений нет.
- Проверено {sum(v['samples'] for v in checks['collision_coverage'])} положений
  выборки физической оболочки, без непокрытых точек.
- Сохранённый Blender открыт заново: {blend['native_sample_frames']} фаз совпали
  с независимым чтением CMP, максимальная ошибка {blend['max_native_position_error']:.8g}.
- Подлинный исходный CMP и утверждённая revision 08 не изменились.

Это офлайн-проверки. Стрельба, отделение частей, физика и переходы LOD в живой
игре ещё не проверены; игра запускается только пользователем.

Протоколы: [checks.json](checks.json), [motion_intersections.json](motion_intersections.json),
[blend_checks.json](blend_checks.json), [collision_manifest.json](collision_manifest.json),
[uv_integration.json](uv_integration.json), [lod_materials.json](lod_materials.json),
[hardpoint distances](mount_distances.json). Расстояние эффекта от поверхности
не является само по себе дефектом: выхлоп начинается за срезом сопла.

## Основа из оригинала

Модель: `{assembly['original']}`.
SHA-256: `{assembly['original_sha256']}`.
Принятая форма: `../revision_08/rh_concept_b_lod0.cmp`.
SHA-256: `{assembly['accepted_sha256']}`.

У исходной rh_pir_elite 3 LOD: 1514 / 710 / 296 треугольников, 5 отделяемых
CollisionGroup и отдельные damage cap через DpConnect. Установленный исходный
архетип ссылается на общие rh_elite damage caps; новый фрагмент использует свои
имена, чтобы не заменить заглушки других кораблей. Материалы повреждений взяты
из пиратской библиотеки (pir_r_dmg3, Equip_genD), не из семейства metal.
Двери независимы от крыльев. Непривязанный исторический dish2 не добавлен
обратно: реальной части с таким именем в модели нет.

## Подключение

{status} Игровые пути используют `ships/rheinland/rh_concept_b/` и `damage/`.
Установщик меняет визуальные ссылки существующего `rh_elite_pir`, добавляет
отдельный LOD MAT и связывает пять CollisionGroup с десятью новыми Simple.
Имя архетипа, баланс, cockpit и лётные характеристики сохраняются. Все записи
в DATA, включая подготовку и откат, выполняются через `tools.data_folder`.
`shiparch_fragment.ini` служит справочным примером; его отдельный Ship нельзя
слепо подставлять вместо существующего архетипа сохранения.
После успешной сверки установщик удаляет временные копии установки/отката.
Модели-исходники и Blender остаются для дальнейшего редактирования; ZIP не создаётся.

## Воспроизведение

Перенос принятой UV-правки из сохранённой базы `uv_refinement_01/approved_base.cmp`:

```powershell
python -B tools/procedural_ships/rh_concept_b_uv_integrate.py
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/rh_concept_b_uv_lods.py
python -B tools/procedural_ships/rh_concept_b_lod_materials.py
python -B tools/procedural_ships/rh_concept_b_uv_integrate.py --finish
python -B tools/procedural_ships/check_rh_concept_b_final.py
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/rh_concept_b_final_blender.py -- --motion
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/rh_concept_b_render.py -- --revision 9 --save-only
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/rh_concept_b_final_review.py
python tools/blender_workspace.py --topic ship_design --script tools/procedural_ships/check_rh_concept_b_final_blend.py
python -B tools/procedural_ships/rh_concept_b_final_report.py
python -B tools/procedural_ships/rh_concept_b_install.py
```

Последняя команда только подготавливает установку. `--apply` требует закрытой
игры и отсутствия пользовательской паузы. Не запускать старые генераторы
final/damage поверх этой сборки без повторения всех последующих правок: они
описывают более ранние стадии. Источники и хеши актуальных изменений находятся
в `tail_integration.json` и `uv_integration.json`.
'''
    (OUT/'README.md').write_text(readme,encoding='utf8')
    sections=[('Чистовая форма',[('finished_open','Раскрыт'),('finished_folded','Сложен вперёд'),('finished_side','Профиль'),('finished_tail','Задний люк и четыре пилона')]),
              ('Уровни детализации',[(f'lod{i}',f'LOD{i}: {n} треугольников') for i,n in enumerate(lods)]),
              ('Повреждения',[('damage_tail','Отделена только задняя стойка; верх, низ и барабан сохранены'),('damage_port_wing','Левое крыло'),('damage_starboard_wing','Правое крыло'),
                              ('damage_port_engine','Левый двигатель'),('damage_starboard_engine','Правый двигатель'),('damage_all','Все пять частей отделены')]),
              ('Трюм',[('cargo_open','Двери открыты, освещение для осмотра внутренности')])]
    body=['<!doctype html><meta charset="utf-8"><title>RH B — finished model</title><style>body{font:16px system-ui;background:#171c22;color:#e5e8ed;margin:30px}a{color:#8ad7ee}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px}figure{margin:0}img{width:100%}figcaption{padding:8px}</style>',
          '<h1>RH concept B — чистовая сборка</h1><p>Офлайн-рендеры из готового CMP. <a href="README.md">Описание</a> · <a href="rh_concept_b.cmp">CMP</a> · <a href="rh_concept_b_rigged.blend">Blender</a></p>']
    for title,images in sections:
        body.append('<h2>'+title+'</h2><div class="grid">')
        for name,label in images:
            assert (OUT/(name+'.png')).is_file()
            assert (OUT/(name+'.png')).stat().st_mtime>=f.DEST.stat().st_mtime,('stale render',name)
            body.append(f'<figure><a href="{name}.png"><img src="{name}.png"></a><figcaption>{label}</figcaption></figure>')
        body.append('</div>')
    (OUT/'comparison.html').write_text('\n'.join(body),encoding='utf8')
    files=[f.DEST,OUT/'rh_concept_b.sur',f.LOD_MAT,OUT/'rh_concept_b_rigged.blend',OUT/'shiparch_fragment.ini',OUT/'README.md']
    files += [OUT/'comparison.html']+[OUT/(name+'.png') for _,images in sections for name,_ in images]
    files += [OUT/name for name in ('checks.json','blend_checks.json','motion_intersections.json','mount_distances.json','collision_manifest.json','uv_integration.json','lod_materials.json')]
    if installed:files.append(OUT/'installation.json')
    files += sorted((OUT/'damage').glob('*.3db'))+sorted((OUT/'damage').glob('*.sur'))
    manifest={p.relative_to(OUT).as_posix():dict(bytes=p.stat().st_size,sha256=f.digest(p)) for p in files}
    (OUT/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('DOCUMENTED',OUT/'README.md',flush=True)


if __name__=='__main__':build()
