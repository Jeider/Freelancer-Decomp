"""Document the checked offline delivery. No live game/model writes."""
import json
import rh_freighter_final as d
f=d.f

def main():
    build=d.read('build.json');validation=d.read('validation.json');motion=json.loads((d.OUT/'review/motion_check.json').read_text());blender=d.read('blend_check.json')
    assert validation['cmp_sha256']==build['cmp_sha256']==f.digest(d.ASSETS/'rh_pir_freighter.cmp')
    assert motion['cmp_sha256']==build['cmp_sha256'] and not motion['collisions']
    assert f.digest(d.OUT/'rh_pir_freighter.blend')==blender['sha256']
    expected={'rh_pir_freighter.cmp','rh_pir_freighter.sur','rh_pir_freighter_lods.mat'}
    expected|={'rh_pir_freighter_dmg_'+zone+ext for zone in d.PARTS for ext in ('.3db','.sur')}
    assert {p.name for p in d.ASSETS.iterdir() if p.is_file() and p.name!='manifest.json'}==expected
    files={p.name:dict(bytes=p.stat().st_size,sha256=f.digest(p)) for p in d.ASSETS.iterdir() if p.is_file() and p.name!='manifest.json'}
    receipt=d.read('integration/installation.json') if (d.OUT/'integration/installation.json').exists() else None
    installed=bool(receipt) and all(receipt['game_assets'].get('ships/rheinland/rh_pir_freighter/'+n)==e['sha256'] for n,e in files.items() if not n.endswith('.mat'))
    handoff=(d.OUT/'lod_material_handoff.json').exists()
    d.dump(d.ASSETS/'manifest.json',dict(files=files,cmp_sha256=build['cmp_sha256'],lod_material='rh_pir_freighter_projection_lod',installed=installed,lod_mat_installed=False))
    # manifest is metadata; permit it on repeated documentation runs.
    source_applied=(d.OUT/'source_applied.json').exists()
    table='\n'.join('| '+z['zone']+' | `'+z['part']+'` | `'+z['hardpoint']+'` | `'+z['archetype']+'` |' for z in build['damage'])
    text=f'''# RH pirate freighter Q13 — финальная модель

{'**Модель и разрушения установлены по разовому прямому разрешению пользователя.** [Отчёт](integration/installation.json). Исходные модели подключены к обычной сборке Pythonlancer через DataFolder.' if installed else '**Офлайн-поставка, установка не выполнена.**'}

Визуальная основа — принятая uv_15. Ближняя геометрия и UV сохранены.
Пользовательские HP взяты из изменённого `uv_15/rh_pir_freighter_review_open.cmp`:
`9b169791451dfb8632975665936c157e0934ef96d086ddced739d7cf3bacd8c2`.
Все 64 точки, включая 17 отредактированных, перенесены в анимированную модель.
Четыре новые точки повреждений добавлены на Root, всего 68 HP.

## Файлы

- [Авторские файлы корабля](assets/): CMP, SUR, 4 повреждённых 3DB/SUR; локальный MAT хранится как источник LOD-атласа.
- [Blender](rh_pir_freighter.blend): кадр 211, раскрытая поза; полная анимация, пользовательские HP, скрытые коллекции LOD и повреждённой сборки.
- [Статичный раскрытый CMP](rh_pir_freighter_review_open.cmp): только для просмотра/редактирования. Игровая анимация находится в `assets/rh_pir_freighter.cmp`.
- [Разрушенная сборка](previews/damage_ship_above.png), [детали разрушения](previews/damage_parts.png), [сравнение LOD](previews/lod_comparison.png), [вайрфрейм](previews/wire_review.png).
- [Оригинальные разрушения для сравнения](previews/native_damage_reference.png).
- [Патч Pythonlancer](pythonlancer.patch), [сгенерированный блок корабля](shiparch_review.ini), [результат проверки](pythonlancer_check.json).
{'- [Актуальная интеграция моделей и damage в Pythonlancer](integration/pythonlancer.patch), [новый блок корабля](integration/shiparch_review.ini), [проверки обычной генерации](integration/check.json).' if installed else ''}

## Разрушения

| Зона | CollisionGroup.obj | Получающий HP на Root | Simple |
|---|---|---|---|
{table}

Двигатель получен из нашего целого корпуса: сохранены опора, плечо и продольная
половина оболочки, открыта внутренняя полость, оставлен повреждённый внутренний узел.
Панель сохраняет переднюю часть с вентиляцией и рваную диагональную кромку.
Последняя правка добавляет вывернутые края, семь отогнутых полос обшивки на каждом
борту и объёмные изломы механической подложки. Основания полос проверены на
соединение с панелью. [Сравнение до/после и разбор оригинала](panel_damage/README.md).
Этот вариант разрушений принят пользователем 18 ноября 2026.
Это не масштабированные оригинальные обломки. Отдельные накладки на улетающие
обломки отсутствуют; `group_dmg_hp/group_dmg_obj` не используются.
Кнопки/цилиндры являются дочерними частями панели и уходят вместе с ней.

## Геометрия, физика, материалы

LOD0/1/2: **{' / '.join(map(str,build['lod_triangles']))}** треугольников.
Переходы: 0 / 250 / 750 / 10000. Кабина и её UV сохранены во всех LOD.
Дальние поверхности получают атлас из 54 проекций этой модели в Blender.
Локальный `rh_pir_freighter_lods.mat` содержит только этот атлас;
пользовательский общий `rh_pir_playerships.mat` не изменён.
CMP и повреждённые 3DB не содержат Material/Texture libraries.
{'Материал rh_pir_freighter_projection_lod и текстура rh_pir_freighter_projection_lod.tga переданы один раз для включения пользователем в общий MAT. Отдельный LOD MAT не устанавливается и больше не предлагается. Шаблон Pythonlancer уже использует только общий MAT; факт пользовательского слияния ещё не подтверждён. [Правило передачи](lod_material_handoff.json).' if handoff else 'После слияния LOD MAT пользователем пути библиотек можно скорректировать отдельно.'}

SUR статична и соответствует раскрытому кораблю. В неё встроены 20 настоящих
объёмов оборудования, преобразованных по новым HP; HpMount охватывает корабль
и оборудование с запасом 6%. HpShield01 остаётся креплением генератора.
Только Root имеет `!fxd`; локальные поверхности сохраняются для отделяемых частей.
Вайрфрейм принадлежит деталям: 4 группы повреждения имеют собственные контуры.
Контуры раскрытых цилиндров находятся у своей панели, а не у Root; дочерний
анимированный wire явно пуст, поэтому не включается запасной показ треугольников.

Нулевая поза сложена. Исходные Cons/Animation сохранены побайтно, включая задержку
launch и механизм трюма. В каждом экспорте свежая соль; [сопоставление ресурсов](build.json).

## Проверки и установка

- [Бинарная проверка](validation.json): лимиты VMesh {validation['maximum']['vertices']} вершин / {validation['maximum']['indices']} индексов; ссылки, CRC, внешние материалы, HP, точная геометрия/UV damage после записи.
- [Движение](review/motion_check.json): 65 фаз двери, 49 фаз боковых механизмов, 0 пересечений; лучи пола/стен трюма, проверка вентиляции и опор двигателей.
- [SUR](sur_check.json): покрытие корпуса и оборудования, щит, разбор всех файлов.
- [DDS](atlas.json): DXT1, 12 mip-уровней; отдельный D3D9-конвертер и upload-check прошли.
- [Blender](blend_check.json): сохранён и повторно открыт, LOD/damage выключены одновременно в render и viewport.
- Pythonlancer: меняется только `rh_freighter_pir`, 152 остальных корабля не меняются; баланс сохранён. Статус исходников: **{'изменения применены' if source_applied else 'проверенный патч подготовлен, применение ещё не выполнено'}**.

{'На этот раз пользователь явно разрешил установку и продолжение при запущенной игре. В рабочую DATA записаны только 10 файлов модели/разрушений. Активный shiparch.ini и общий MAT не менялись; пользователь выполняет обычную генерацию Pythonlancer и объединение LOD-материала. Временные бинарные копии установки удалены после проверки.' if installed else 'Установка принадлежит пользователю. Рабочие DATA, shiparch.ini и общий MAT не менялись.'}
Игра и сервер агентом не запускались. Проверка реального боя/отделения деталей
остаётся за игровым тестом пользователя после перезапуска.
Архетип остаётся `rh_freighter_pir`, путь модели — `ships/rheinland/rh_pir_freighter/rh_pir_freighter.cmp`.
Не запускайте исторические установщики соседних прототипов.
'''
    (d.OUT/'README.md').write_text(text,encoding='utf8')
    d.dump(d.OUT/'delivery.json',dict(files=files,cmp_sha256=build['cmp_sha256'],blend_sha256=blender['sha256'],
        user_source_sha256=d.read('hardpoint_transfer.json')['source_sha256'],pythonlancer_source_applied=source_applied,
        installed=installed,lod_mat_installed=False,lod_handoff_once=handoff,game_launched=False,checks=['validation.json','sur_check.json','review/motion_check.json','atlas.json','pythonlancer_check.json','blend_check.json']+(['integration/check.json','integration/installation.json','integration/cleanup.json'] if installed else [])))
    print('DOCUMENTED DELIVERY',len(files),'authoring assets; installed',installed)

if __name__=='__main__':main()
