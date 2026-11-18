"""Record completed native installation beside the existing interior prototypes."""
from native_common import *

installed=json.loads((OUT/'installed.json').read_text(encoding='utf8'))
native=json.loads((OUT/'native_validation.json').read_text())
maps=json.loads((OUT/'material_validation.json').read_text())
assert installed['verified']
dump(OUT/'gpu_validation.json',dict(command='python tools/room_materials/check.py --startup-build',passed=True,
    native_single_layer_delta=0,native_two_layer_delta=0,authored_uv_transform_delta=0,
    normal_response_delta=62,game_launched=False,limitation='Standalone GPU fixture; actual room was not launched.'))
page='''<!doctype html><meta charset="utf-8"><title>Бисмарк — установка v8</title>
<style>body{background:#161d24;color:#e7edf3;font:17px system-ui;max-width:1250px;margin:32px auto;padding:20px}a{color:#7fcef5}img{max-width:100%}p,li{line-height:1.5}</style>
<h1>Бисмарк: бар, интеграция v8</h1><p>Установлено в рабочую игру D:\\Games\\FL_MOD. Игра агентом не запускалась.</p>
<ul><li>47 материалов и 53 встроенные текстуры сохранены побайтно, включая исходные параметры.</li>
<li>Вентиляторы, лучи света, старые записи креплений, hardpoints и wireframe сохранены.</li>
<li>11 групп рельефа перенесены из прототипа v8. Оба UV-набора получены из исходных треугольников; второй слой не пересоздавался проекцией.</li>
<li>5 770 → 26 989 треугольников. Два VMesh-блока в пределах uint16; дополнительная часть закреплена неподвижно на Root. Удалены только 113 вырожденных треугольников отсечения.</li>
<li>11 карт нормалей/микрошероховатости пересчитаны из текущих диффузных текстур с mip-уровнями. Используется установленный интерьерный шейдер. Оценка рельефа по изображению не восстанавливает физическую поверхность и не удаляет запечённый свет из оригинальных текстур.</li>
<li>Профили сохраняют исходные коэффициенты; изменены ссылки на дополнительные карты. Они привязаны к существующим идентификаторам материалов и используются также там, где встречаются те же идентификаторы. Геометрия заменена только в rh_bizmark_bar.cmp.</li>
<li>Автономная GPU-проверка: PASS. Базовое освещение, два слоя и трансформации UV совпали с нативным результатом (дельта 0). Проверка в самой игре не проводилась.</li></ul>
<p><a href="../prototype_v8/index.html">Превью и контуры v8</a> · <a href="native_validation.json">Проверка CMP</a> · <a href="material_validation.json">Карты и профили</a> · <a href="installed.json">Установка и резервная копия</a> · <a href="native_roundtrip.blend">Blender после обратного чтения CMP</a></p>
<h2>Контроль обратного чтения</h2><p>Это офлайн-рендер из экспортированной геометрии с приближёнными материалами Blender. Передние механизмы скрыты только на этом изображении для осмотра стены; в игре и сохранённом blend они присутствуют.</p><img src="native_arch_wall.png">
'''
(OUT/'index.html').write_text(page,encoding='utf8')
index=ROOT/'out/base_interiors/index.html';content=index.read_text(encoding='utf8')
link='<li><a href="rh_biz_01_base/bar/integration_v8/index.html">Бисмарк — интеграция v8 в игру, исходные материалы сохранены</a></li>'
if 'bar/integration_v8/index.html' not in content:index.write_text(content.replace('<ul>','<ul>'+link,1),encoding='utf8')
(OUT/'restore.txt').write_text('Backup: '+installed['backup']+'\n\nFrom repository root:\npython tools/base_interiors/install.py --restore "'+installed['backup']+'"\n',encoding='utf8')
print('Integration record and topic index updated.')
