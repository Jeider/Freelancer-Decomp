"""Create a review index and a hash-bound offline handoff; never deploy."""
import html,json
from pathlib import Path
import numpy as np
import rh_fighter_final as d
f=d.f

def main():
    build=d.read('build.json');sha=f.digest(d.ASSETS/'rh_pir_fighter.cmp')
    for name in ('build.json','validation.json','equipment_check.json','blend_check.json'):
        assert d.read(name)['cmp_sha256']==sha,name
    assert d.read('sur_check.json')['sha256']==f.digest(d.ASSETS/'rh_pir_fighter.sur')
    assert d.read('atlas.json')['sha256']==f.digest(d.ASSETS/'rh_pir_fighter_lods.mat')
    assert d.read('blend_check.json')['sha256']==f.digest(d.OUT/'rh_pir_fighter.blend')
    assert build['review_sha256']==f.digest(d.OUT/'rh_pir_fighter_review_open.cmp')
    for zone in build['damage']:
        assert zone['sha256']==f.digest(d.ASSETS/zone['file'])
        assert d.read('damage_export_check.json')['zones'][zone['zone']]['sha256']==zone['sha256']
    applied=(d.OUT/'source_applied.json').exists() and d.read('pythonlancer_check.json')['live_source_changed']
    package={p.name:dict(sha256=f.digest(p),bytes=p.stat().st_size) for p in sorted(d.ASSETS.iterdir()) if p.is_file()}
    d.dump(d.OUT/'manifest.json',dict(model='rh_pir_fighter',stage='offline game-ready candidate; in-game checks belong to user',installed=False,game_launched=False,
        assets=package,cmp_sha256=sha,export_salt=build['salt'],private_resources=build['resources'],damage=build['damage'],lod_triangles=build['lod_triangles'],
        shared_material=str(d.MAT),shared_material_sha256=f.digest(d.MAT),original_cmp_sha256=f.digest(d.SOURCE/'original.cmp'),original_sur_sha256=f.digest(d.SOURCE/'original.sur'),
        user_hardpoint_source=d.read('user_hardpoint_source.json'),equipment_seats=d.read('mounts_check.json'),origin=d.read('origin_check.json'),
        pythonlancer=dict(source_applied=applied,files='three Pythonlancer source files; patch retained',live_DATA_written=False),validation_reports=['validation.json','rig_check.json','origin_check.json','mounts_check.json','equipment_check.json','sur_check.json','neck_uv_check.json','blend_check.json','damage_lods_check.json','damage_export_check.json','pythonlancer_check.json']))
    d.dump(d.OUT/'lod_material_handoff.json',dict(offered=True,merged_by_user=False,material=d.ATLAS,texture=d.ATLAS+'.tga',file='assets/rh_pir_fighter_lods.mat',policy='One handoff for this new fighter atlas. After user merges it, use the unchanged shared identities and stop offering another MAT.'))
    ini=['; Add selected lines to the existing [Player] section after ship_archetype.','; Replace entries for these parts; do not duplicate. 0 = destroyed; 1 = intact.']
    ini+=['collision_group = '+p+', 0' for p in d.PARTS.values()]
    ini+=['','; Optional last-base snapshot:']+['; base_collision_group = '+p+', 0' for p in d.PARTS.values()]
    ini+=['','; Receiving HPs are not savegame keys:']+['; '+p+' -> DpRHF_'+z for z,p in d.PARTS.items()]
    (d.OUT/'damage_save_test.ini').write_text('\n'.join(ini)+'\n',encoding='utf8')
    hp=d.read('rig_check.json')['hardpoints'];lines=['# Hardpoints rh_pir_fighter','','Positions and orientation ownership are in extended flight. The prototype roof HPs and native pilot/cockpit positions are preserved.','','| HP | Object | X | Y | Z |','|---|---|---:|---:|---:|']
    lines+=['| '+h['name']+' | '+h['owner']+' | '+' | '.join(f'{v:.5f}' for v in h['position'])+' |' for h in sorted(hp.values(),key=lambda h:h['name'].lower())]
    (d.OUT/'hardpoints.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    # Actual wire resources in their static owning frames, with highlightable parts.
    wires=d.read('wire.json')['parts'];panels=[]
    for title,axes in [('Сбоку',(2,1)),('Сверху',(0,2)),('Сзади',(0,1))]:
        paths=[]
        for name,record in wires.items():
            for line in record['world']:
                p=np.array(line)[:,axes];p[:,1]*=-1
                paths.append('<path class="wire '+name+'" d="M '+str(p[0,0])+','+str(p[0,1])+' L '+str(p[1,0])+','+str(p[1,1])+'"/>')
        panels.append('<section><h3>'+title+'</h3><svg viewBox="-8 -8 16 16">'+''.join(paths)+'</svg></section>')
    photographs=[('mounts_uv_detail.png','Исправленная UV площадок'),('mounts_bottom.png','Площадки форсажей'),('equipment_bottom.png','Посадка оборудования — модели для проверки'),('equipment_rear.png','Мина и CM на разных двигателях'),('neck_detail.png','Шея — одна UV-карта'),('flight_front.png','LOD0, раскрыт'),('flight_rear.png','Корма'),('folded_front.png','Сложен'),('cargo_open.png','Трюм открыт'),('lod1_front.png',f"LOD1 — {build['lod_triangles'][1]} треугольников"),('lod2_front.png','LOD2 — 373 треугольника'),('damage_rear.png','Разрывы крыльев и двигателей'),('damage_bottom.png','Повреждения снизу')]
    photographs += [('damage_lod1_rear.png','Повреждения LOD1'),('damage_lod2_bottom.png','Повреждения LOD2')]
    cards=''.join('<figure><a href="review/'+p+'"><img src="review/'+p+'" loading="lazy"></a><figcaption>'+t+'</figcaption></figure>' for p,t in photographs)
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><title>rh_pir_fighter — проверка комплекта</title><style>body{background:#141b22;color:#e2e8ef;font:16px system-ui;max-width:1280px;margin:32px auto;padding:0 24px}a{color:#87cfff}h1{font-size:26px}.gallery,.wireviews{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}figure{margin:0;background:#26313c;padding:8px}img{width:100%;height:auto}figcaption{padding:8px}svg{width:100%;background:#0c1625}.wire{stroke:#8cd8e7;stroke-width:.022;fill:none}button{padding:8px;margin:8px;color:white;background:#33495c;border:0;cursor:pointer}.selected{stroke:#ffda55;stroke-width:.045}</style><h1>rh_pir_fighter — офлайн-комплект</h1><p>LOD0 16941 · LOD1 3949 · LOD2 373 · 54 HP · четыре зоны повреждения. В игру не установлен.</p><p><a href="README.md">Состав и установка пользователем</a> · <a href="rh_pir_fighter_review_open.cmp">Раскрытый CMP для HP</a> · <a href="rh_pir_fighter.blend">Blender</a> · <a href="damage_save_test.ini">Повреждения для сейва</a></p><div class="gallery">'''+cards+'''</div><h2>Вайрфрейм: принадлежность деталей</h2><p>Контуры взяты из сборки. Выбор ниже проверяет разделение, а не имитирует игровую проверку.</p><button onclick="choose('port_wing_lod1')">Левое крыло</button><button onclick="choose('starboard_wing_lod1')">Правое крыло</button><button onclick="choose('port_engine_lod1')">Левый двигатель</button><button onclick="choose('starboard_engine_lod1')">Правый двигатель</button><button onclick="choose('Root')">Корпус</button><div class="wireviews">'''+''.join(panels)+'''</div><script>function choose(n){document.querySelectorAll('.wire').forEach(e=>e.classList.toggle('selected',e.classList.contains(n)))}</script></html>'''
    page=page.replace('LOD0 16941 · LOD1 3949 · LOD2 373 · 54 HP',f"LOD0 {build['lod_triangles'][0]} · LOD1 {build['lod_triangles'][1]} · LOD2 {build['lod_triangles'][2]} · {build['hardpoints']} HP")
    (d.OUT/'index.html').write_text(page,encoding='utf8')
    readme='''# rh_pir_fighter — комплект для ручной установки

19 ноября 2026. Принятый F14/F01 UV/03, игровой риг и производные ресурсы.
**Комплект подготовлен офлайн. Игра, live DATA и действующие исходники Pythonlancer не изменены.**

## Файлы

- [assets/rh_pir_fighter.cmp](assets/rh_pir_fighter.cmp): анимированный корабль, три LOD, 54 HP, вайрфрейм.
- [assets/rh_pir_fighter.sur](assets/rh_pir_fighter.sur): статическая раскрытая коллизия, оборудование и щит.
- В `assets/` также четыре пары damage 3DB/SUR: port_wing, starboard_wing, port_engine, starboard_engine.
- [assets/rh_pir_fighter_lods.mat](assets/rh_pir_fighter_lods.mat): **один новый атлас** 2048² DXT1, 12 mip-уровней.
- [rh_pir_fighter_review_open.cmp](rh_pir_fighter_review_open.cmp): отдельная раскрытая модель для просмотра и правок HP.
- [rh_pir_fighter.blend](rh_pir_fighter.blend): игровой риг, HP и отдельные сцены LOD/повреждений. Открывается на кадре 49, в полёте.
- [Галерея и вайрфрейм](index.html), [все HP](hardpoints.md), [строки повреждений для сейва](damage_save_test.ini).
- [pythonlancer.patch](pythonlancer.patch), исходники в `pythonlancer/`, [результат shiparch для просмотра](shiparch_review.ini).
- [manifest.json](manifest.json): SHA-256, свежая соль экспорта, связи частных ресурсов и отчёты.

Каталог комплекта: `D:/work/Freelancer-Decomp/out/ship_design/rh_fighter/rh_pir_fighter/`.
Игровое назначение файлов из `assets/`: `DATA/SHIPS/rheinland/rh_pir_fighter/`.
Исходная модель и SUR закреплены в `source/`; они нужны для дальнейшего редактирования.

## Поведение

Начальная поза сложена, как на базах. В полёте крыло раскрывается. Обратный ход:
сначала выравнивание до горизонтали, затем втягивание внутренней секции.
Запуск — 5 секунд ожидания и 2 секунды раскрытия. Пушки движутся со своими крыльями.
Вайрфрейм и SUR остаются раскрытыми; две независимые зоны крыльев сохраняют
свою подсветку и исчезают при разрушении соответствующей детали.

Створки Sc_open baydoor открывают неглубокий трюм прямо под люком. Metal только
во внутренности. Кабина и её родные HP сохранены. Передняя наклонная панель шеи
имеет одну непрерывную карту panel01 вместо двух зеркальных половин.

LOD: **16941 / 3949 / 373** треугольника; интервалы 0 / 180 / 550 / 10000.
Последняя оболочка не содержит внутренних вырезов. Её внешний вид запечён с
нашего корабля, включая стекло и закрытые створки, а не взят с прежнего RH fighter.

Крылья сохраняют около 28,7% своего объёма и направляющие; двигатели — около
45,4%, с продольной рваной чашей. Это производные наших целых деталей.
Damage 3DB содержат геометрию и ссылки на общий rh_pir_playerships.mat, без
встроенных текстур. Заглушек на отлетевших частях нет.

| Деталь | Принимающий HP | Simple |
|---|---|---|
| port_wing_lod1 | DpRHF_port_wing | rh_pir_fighter_dmg_port_wing_cap |
| starboard_wing_lod1 | DpRHF_starboard_wing | rh_pir_fighter_dmg_starboard_wing_cap |
| port_engine_lod1 | DpRHF_port_engine | rh_pir_fighter_dmg_port_engine_cap |
| starboard_engine_lod1 | DpRHF_starboard_engine | rh_pir_fighter_dmg_starboard_engine_cap |

## Pythonlancer и MAT

Подготовлены **три файла исходников**: PirateBanshee в world/ship.py,
отдельный playerships/rh_pir_fighter.ini и pirate-ветка simples/pir_nmd.ini.
Шаблон включает два двигателя ENGINE_DOUBLE_SAME, четыре CollisionGroup и
дополнительные HpWeapon05/06. Прежние пять оружейных точек остаются, то есть
черновик даёт семь пушечных креплений; прежние MAX_WEAPONS не расширены.
Старый одиночный пиратский engine-cap заменён двумя Simple. Другие 152 корабля
при сравнении результатов генератора не изменились.

Исходники и diff предназначены для просмотра/применения пользователем.
`review_data/` — изолированная генерация через DataFolder, не живой DATA.
Не копировать весь world/ship.py поверх более свежих правок без сравнения patch.

Новый материал: `rh_pir_fighter_f01_projection_lod`.
Текстура: `rh_pir_fighter_f01_projection_lod.tga` (внутри MAT — проверенные DDS/MIPS).
Можно использовать отдельный MAT, как в staged шаблоне. Если переносишь материал
в общий rh_pir_playerships.mat, сохрани оба имени и удали из шаблона только строку
дополнительной библиотеки. Общий MAT этим комплектом не заменяется.
Это первая передача атласа этого fighter; после объединения новый MAT повторно
не нужен. Существующие atlas-материалы elite/freighter остаются прежними.

## Проверки и дальнейшие правки

Проверены повторно прочитанные CMP/3DB/SUR, индексы/CRC/соли, внешние материалы,
положения капов, постоянство раскрытого wire и сохранение геометрии/UV LOD0
после сборки. Максимальный VMS: 16284 вершины / 24459 индексов.
54 HP проверены после сохранения/повторного открытия Blender; 108 матриц рига
совпали с игровыми каналами с погрешностью менее 3×10⁻⁷.
61 положение створок проверено с реальными native equipment hulls: пересечений
с оружием и щитом нет. Минимальный запас крыльевых пушек от боковины при втягивании
больше 1,07 единицы. Другие модели оборудования могут отличаться по габаритам.
Щит покрывает корпус и оборудование; !fxd присутствует только у Root.

Игровой запуск, загрузка сохранения, HUD и отделение деталей **здесь не проверялись**:
их проверяет пользователь после установки. Это подготовленный кандидат для игры.
Для правок HP используй review_open.cmp; не редактируй старый UV/03.
Следующая сборка обнаруживает изменённый review_open, сохраняет его как источник
и принимает его HP. После переноса HP требуется пересчёт встроенных equipment
hulls SUR; имя hpid само по себе не переносит геометрию оборудования.

Скрипты сборки: `tools/procedural_ships/rh_fighter_final*.py`.
Порядок: prepare (`rh_fighter_final.py`), Blender damage/lods, atlas-png,
lod_dds.exe, atlas-mat, build, SUR, equipment, check, Blender review, staged
Pythonlancer prepare/baseline/staged/check, handoff. Ни один из этих шагов не
устанавливает файлы в игру. Blender запускается только через blender_workspace.py.
'''
    latest='''## Центр корпуса и последние пользовательские HP

Источник — переданный пользователем review_open, сохранённый в
`source/user_hardpoints.cmp`; SHA-256 записан в user_hardpoint_source.json.
Все 55 HP сохранены относительно корпуса: пользователь снова передвинул
форсажи вперёд, их новые положения приняты. CM и мина остаются на боках разных
двигателей. Владельцы, ориентации и дополнительные параметры HP сохранены.

Новый ноль — середина основного корпуса: Root, обе carved_flank и
Sculpted_roof_shoulders. В прежних координатах это [0, -0.0475, -1.005].
Перенос к носу 1.005; весь комплект использует p_new = p_old - C.
Геометрия, HP, шарниры/оси, LOD, повреждения, wire и SUR пересчитаны согласованно.
Габариты основной части относительно нового нуля симметричны:
X=±1.7115, Y=±1.9725, Z=±3.245. Кабина, задний диск и крылья не смещают этот ориентир.
Матрицы шести каналов проверены в 61 положении каждая; максимальная ошибка
смены координат менее 2e-8. Система координат пользовательского HP-исходника
записана отдельно, чтобы следующие ручные правки не получили двойной сдвиг.

Принятые длинные площадки закреплены в source/ventral_shelves.json. Их форма
не зависит от последующих переносов HP. Исправлены UV 12 светлых треугольников:
масштаб по обеим осям одинаковый (0.60 UV на единицу), прежнее растяжение около
2.22 раза устранено. Плоская монтажная часть имеет одну непрерывную карту;
отдельная карта переднего ската начинается только на его настоящем перегибе.
Все остальные UV, материалы, нормали и форма сохранены. 56 треугольников площадок
остаются в существующем числе LOD0, новой геометрии в этой правке нет.
Фотографии/атлас LOD обновлены; SUR заново включает реальные объёмы оборудования.
Площадки остаются на корпусе при повреждении двигателей.

Для четырёх изменённых креплений SUR построен по настоящим моделям оборудования
в их системе HpConnect: rh_thruster02, ge_mine_dropper, li_cm_dropper01.
Их исходники закреплены в source/equipment. Старый корабельный SUR не совпадал
с текущими native HP: вычитание старой позиции форсажа давало смещение около
пяти единиц. Эта ошибка переноса устранена для изменённых креплений.
Синие модели оборудования в отдельной сцене Blender — только пример для проверки
посадки; в геометрию корабля они не включены.

'''
    readme=readme.replace('## Поведение',latest+'## Поведение')
    final_damage='''## Релиз повреждений

Четыре независимые зоны: оба крыла и оба двигателя. Задний диск, корпус и
площадки форсажей сохраняются. Детали построены из текущего целого меша;
у двигателей продольная вскрытая оболочка, у крыльев рваный обугленный край.
Все damage 3DB имеют три LOD с Switch2/LODranges = 0, 180, 550, 10000.
Тонкие треугольники Boolean исправляются в связной сетке до экспорта:
простое отбрасывание маленькой площади оставляло щели. Повторно прочитанные
3DB во всех LOD теперь замкнуты. Текстуры берутся из общего MAT, отдельных
материалов разрушений и заглушек отлетающих обломков нет.

| Деталь | LOD0 / LOD1 / LOD2 |
|---|---|
'''
    final_damage+=''.join('| '+z['zone']+' | '+' / '.join(map(str,z['lod_triangles']))+' |\n' for z in build['damage'])
    final_damage+='\nПолный блок корабля и четыре Simple: [rh_pir_fighter_integration.ini](rh_pir_fighter_integration.ini).\n\n'
    final_damage+=('Три проверенных исходника уже внесены в Pythonlancer. Генерация рабочей DATA\nи установка моделей остаются за пользователем; source_applied.json фиксирует хеши.\n\n' if applied else 'Исходники подготовлены для Pythonlancer; рабочая DATA не записывалась.\n\n')
    readme=readme.replace('## Файлы',final_damage+'## Файлы')
    if applied:
        readme=readme.replace('Игра, live DATA и действующие исходники Pythonlancer не изменены.', 'В Pythonlancer внесены три исходника; игра и live DATA не изменены.')
        readme=readme.replace('Исходники и diff предназначены для просмотра/применения пользователем.', 'Исходники уже применены; diff сохранён для просмотра сделанных изменений.')
    readme=readme.replace('54 HP',str(build['hardpoints'])+' HP')
    readme=readme.replace('16941 / 3949 / 373',' / '.join(map(str,build['lod_triangles'])))
    maximum=d.read('validation.json')['maximum']
    readme=readme.replace('16284 вершины / 24459 индексов',f"{maximum['vertices']} вершин / {maximum['indices']} индексов")
    gap=min(d.read('equipment_check.json')['wing_equipment_clearance'].values())
    readme=readme.replace('больше 1,07 единицы',f"{gap:.3f} единицы")
    readme=readme.replace('Это первая передача атласа этого fighter; после объединения новый MAT повторно\nне нужен.', 'Атлас этого fighter уже передан; эта сборка обновляет его изображение под\nновые площадки, сохраняя имена материала и текстуры. После объединения повторная\nбиблиотека не нужна.')
    readme=readme.replace('Blender damage/lods, atlas-png,', 'Blender damage + damage-lods/lods, atlas-png,')
    (d.OUT/'README.md').write_text(readme,encoding='utf8')
    print('HANDOFF',len(package),'assets;',sum(v['bytes'] for v in package.values()),'bytes;',sha,flush=True)

if __name__=='__main__':main()
