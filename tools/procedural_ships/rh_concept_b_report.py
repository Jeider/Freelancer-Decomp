"""Assemble review sheets from actual model renders, and document revision 03."""
import hashlib
import json
from PIL import Image,ImageDraw,ImageFont,ImageOps
from rh_redesign_paths import CONCEPT_B_FORM as OUT, CONCEPT_B_DETAIL as OLD, CONCEPTS


def sheet(name,cells,columns=2,size=(1000,786)):
    w,h=size;rows=(len(cells)+columns-1)//columns
    pic=Image.new('RGB',(columns*w,rows*(h+50)),(25,30,37));draw=ImageDraw.Draw(pic)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25)
    for i,(title,path) in enumerate(cells):
        x,y=(i%columns)*w,(i//columns)*(h+50)
        draw.text((x+20,y+10),title,font=font,fill=(234,239,244))
        image=Image.open(path).convert('RGB');image=ImageOps.contain(image,(w,h))
        pic.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
    pic.save(OUT/name,quality=95)


def main():
    stats=json.loads((OUT/'checks.json').read_text());rig=json.loads((OUT/'rig_checks.json').read_text())
    channels=json.loads((OUT/'channel_checks.json').read_text())
    digest=hashlib.sha256((OUT/'rh_concept_b_lod0.cmp').read_bytes()).hexdigest()
    assert digest==stats['output_sha256']==rig['cmp_sha256']==channels['cmp_sha256']
    assert not rig['panel_intersections'] and channels['all_parents_and_frame_sizes_valid']
    sheet('comparison_revision02_03.jpg',[
        ('Revision 02 — прежняя геометрия',OLD/'geometry_open.png'),('Revision 03 — новая геометрия',OUT/'geometry_open.png'),
        ('Revision 02 — складывание вверх',OLD/'geometry_folded.png'),('Revision 03 — вперёд и к корпусу',OUT/'geometry_folded.png')])
    sheet('art_comparison.jpg',[('Ориентир — concept B',CONCEPTS/'rh_concept_B.png'),
                                ('Revision 03 — реальная модель с текстурами',OUT/'textured_open.png')],size=(1152,900))
    sheet('review_sheet.jpg',[
        ('Кабина: задник и рамки остекления',OUT/'cabin_rear_culling.png'),('Трюм: двери скрыты, пол и стены на месте',OUT/'cargo_hidden_doors_culling.png'),
        ('Вид сверху — раскрыто',OUT/'geometry_top_open.png'),('Вид сверху — сложено вперёд',OUT/'geometry_top_folded.png')])
    text=f'''# RH concept B — revision 03

Переработка первого LOD по замечаниям к revision 02 и исследованию исходных
моделей/артов. Предыдущая версия сохранена в `../revision_02`.
Это офлайн-прототип: в рабочую игру не установлен, игра не запускалась.

## Смотреть

- [Сравнение revision 02 / 03](comparison_revision02_03.jpg).
- [Арт и новая модель](art_comparison.jpg). Ракурсы различаются; это сопоставление образа, не точное наложение.
- [Крупные планы и движение сверху](review_sheet.jpg).
- [Анимация крыльев и дверей, MP4](wing_mechanism.mp4).
- [CMP — LOD0](rh_concept_b_lod0.cmp).
- [Blender со встроенными текстурами и ключами](rh_concept_b_rigged.blend).
- [OBJ раскрытый](rh_concept_b_open.obj), [OBJ сложенный](rh_concept_b_folded.obj).
- [Архив всего прототипа](rh_concept_b_revision_03.zip).

## Что изменено

| Узел | Результат |
|---|---|
| Кабина | Удалён красный выступ. Новая замкнутая задняя оболочка соединена с продлёнными рейками шеи. Сохранены исходное стекло и точки пилота/камеры; наружные стойки построены между фактическими границами стёкол. |
| Трюм | Собственные пол, борта и торцы, обрамление проёма и две опоры на полу. Видимы при открытых или скрытых дверях. |
| Рама | Непрерывная восьмигранная оболочка с согласованными фасками, без щелей между отдельными секторами. |
| Барабан | Пять настоящих закруглённых прорезей с глубиной и задней стенкой. Общая UV-проекция лицевой поверхности. |
| Корпус | Связанные щёки, утопленные жалюзи и несущие плечи; сохранена вертикальная композиция Rheinland. |
| Крылья | Два шарнира на сторону: 68° у основания и 27° в локте. Оси ±Y; горизонтальное движение вперёд и внутрь. |
| Мелкие детали | Моделированные заклёпки удалены. Геометрия расходуется на оболочки, прорези и механизм. |
| Материалы | `metal`/`metal03` только внутри грузового отсека и снизу дверей. Наружные поверхности используют Rheinland armor. Пушки остаются отдельными моделями. |

Силуэт и пропорции опираются на concept B: вынесенная кабина, открытая шея,
тяжёлый угловатый корпус, вертикальная рама со ступицей и короткие крылья.
Изученные LI/RH-механизмы использованы для выбора осей и родительской иерархии;
численные углы авторские и проверены на новой геометрии.

## Анимация и проверка

Основной `Sc_extend wing`: t=0 — раскрыто, t=2 — сложено. Раскрытие проигрывается
назад. `Sc_launch extend` удерживает сложенные крылья до 5 с и раскрывает к 7 с;
его конец точно совпадает с началом основного скрипта. Имена действующих
скриптов и их длительности сохранены, родители обновлены для нового локтя.
Неиспользуемый исходный канал `dish2` исключён из этого прототипа.

В Blender: кадры 1–24 раскрыто, 25–73 складывание, 73–97 сложено,
97–145 раскрытие; 169–201 открытие дверей, 225–257 закрытие. Всего 288 кадров,
24 fps. У материалов параметр `Texture blend`: 0 — геометрия, 1 — текстура.
Геометрия рендера, Blender и CMP одна и та же; render-only subdivision нет.
Крупные планы используют отсечение обратных граней, трюм дополнительно освещён
диагностической лампой. Прежние рендеры revision 02 такой проверки не делали.

- **{stats['triangles']} треугольников**, 11 частей, только Level0.
- Максимум {stats['directx_format_checks']['max_vertices_per_vmesh']} вершин и {stats['directx_format_checks']['max_indices_per_vmesh']} индексов на VMesh; 16-битные пределы соблюдены.
- **{rig['frames']} поз** сопоставлены с сохранённым и заново открытым Blender-файлом.
- Максимальное расхождение проверенных вершин: `{rig['max_vertex_error']:.3g}` единицы модели.
- Изменение высоты крыльев: `{rig['wing_height_error']}`. Концы смещаются вперёд минимум на 2.83 и внутрь минимум на 2.46 единицы модели.
- Пересечений панелей крыльев с проверенными корпусом, рамой, стеклом, двигателями, дверями и противоположным механизмом не найдено.
- {len(rig['front_facing_cavity_rays'])} лучей проверяют лицевые поверхности задника, стоек остекления, пола и стенок трюма.
- Все каналы привязываются к реальным родителям; размеры frames и непрерывность launch → wing проверены.

[Геометрия и лимиты](checks.json) · [Кинематика и поверхности](rig_checks.json) · [Анимационные каналы](channel_checks.json).

Проверки пересечений не включают намеренные контакты собственных подшипников,
навесное оборудование и игровую физику. Это не утверждение о проверке SUR.
Общий генератор полигонов теперь учитывает вогнутые контуры: прежняя веерная
триангуляция могла разворачивать часть задника внутрь, что видно только с culling.

## Что отложено

Дальние LOD, новая SUR-физика, damage caps и финальная художественная UV-развёртка.
Существующий внешний атлас используется как рабочая текстура. В CMP нет нового
набора внешних MAT: для просмотра отдельно нужны исходные библиотеки этой сборки;
Blender и OBJ поставляются с экспортированными текстурами.

## Источники и воспроизведение

Модель: `{stats['source']}`. SHA-256: `{stats['source_sha256']}`.
Новый CMP: `{digest}`.

Из корня репозитория:

```powershell
python -B tools/procedural_ships/rh_concept_b_form.py
python -B tools/procedural_ships/check_rh_concept_b_form.py
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python tools/procedural_ships/rh_concept_b_render.py -- --revision 3 --video
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python tools/procedural_ships/check_rh_concept_b_form.py -- --blender-check
ffmpeg -y -framerate 24 -i out/ship_design/rh_elite/prototypes/concept_b/revision_03/animation_frames/%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart out/ship_design/rh_elite/prototypes/concept_b/revision_03/wing_mechanism.mp4
python -B tools/procedural_ships/rh_concept_b_report.py
python -B tools/procedural_ships/rh_concept_b_form.py --package-only
```
'''
    (OUT/'README.md').write_text(text,encoding='utf8')
    print('Review sheets and README ready:',OUT,flush=True)


if __name__=='__main__':main()
