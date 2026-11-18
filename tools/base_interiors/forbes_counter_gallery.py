"""Reviewable offline deliverable for the focused Forbes bar counter upgrade."""
import html,json
from pathlib import Path
from PIL import Image,ImageDraw
from forbes_counter_audit import OUT
from native_common import ROOT,sha


def main():
    build=OUT/'modeled';native=json.loads((build/'native_validation.json').read_text())
    preview=json.loads((build/'preview_validation.json').read_text())
    check=json.loads((build/'surface_validation.json').read_text())
    assert preview['cmp_sha256']==native['exported_sha256']==check['cmp_sha256'] and check['all_passed']
    installed_path=build/'installed.json'
    installed=json.loads(installed_path.read_text()) if installed_path.exists() else {}
    is_installed=installed.get('verified') and installed.get('sha256')==native['exported_sha256']
    if is_installed:assert sha(Path(installed['target']).read_bytes())==installed['sha256']
    status='Установлено в игру; файл проверен после установки.' if is_installed else 'Офлайн-прототип, подготовлен отдельно от игры.'
    model_link=('<a href="modeled/installed.json">Отчёт об установленном CMP</a>' if is_installed else
                '<a href="modeled/package/DATA/BASES/LIBERTY/li_columbia_bar.cmp">Подготовленный CMP</a>')
    body=['<meta charset="utf-8"><style>body{background:#17212a;color:#e7eef4;font:17px system-ui;max-width:1500px;margin:30px auto;padding:20px}a{color:#81d5ff}img{width:100%;display:block}section{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:12px 0 32px}figure{margin:0}figcaption{padding:10px;background:#273743}p{line-height:1.55;max-width:1200px}</style>',
      '<h1>li_for_01_base — барная стойка</h1>',
      f'<p><b>{status}</b> Основная доработка — внешняя боковина стойки по всей дуге: '
      'панельные поля, золотистые пояски, решётка под столешницей и рамки центральных орнаментов. '
      'Дополнительно — панельные рамки за барменом.</p>',
      f'<p>Вся модель: {native["source_triangles"]:,} → {native["result_triangles"]:,} треугольников. '
      'Изменены две группы поверхностей. Сохранены текущие материалы, текстуры, мебель и остальные части комнаты. '
      'Один повреждённый угол второй UV-развёртки восстановлен по трём совпадающим соседним вершинам.</p>',
      '<p>Модель найдена по фактической привязке комнаты: <code>li_for_01_bar.ini → Li_03_Bar_ambi_int_01.thn → li_03_bar → li_columbia_bar.cmp</code>.</p>',
      f'<p>{model_link} · '
      '<a href="modeled/forbes_bar_counter.blend">Редактируемый Blender</a> · '
      '<a href="modeled/features.json">Контуры, глубины и выбранные поверхности</a> · '
      '<a href="modeled/surface_validation.json">Проверки UV, стыков и нормалей</a></p>',
      '<p>Изображения ниже — сравнение при одинаковом диагностическом освещении в Blender. '
      'Они показывают экспортированную геометрию и текущую основную текстуру; игровой шейдер и предметы из THN здесь не воспроизводятся.</p>',
      '<h2>Контуры на исходных текстурах</h2><p>Основные профили заданы вручную. Узкие отверстия решётки обведены по затемнённым участкам изображения из выбранных вручную рядов. Контуры проверены на текстурах.</p>',
      '<section><img src="modeled/front_contours.png"><img src="modeled/back_contours.png"></section>']
    labels={'counter_overview':'Стойка целиком','counter_front':'Передняя боковина','counter_left':'Левая часть дуги',
            'counter_right':'Правая часть дуги','back_bar':'Панели за барменом'}
    for view in preview['views']:
        body.append('<h2>'+labels.get(view,html.escape(view))+'</h2>')
        for style in ('textured','clay'):
            # The outside overview is useful with the native emissive artwork;
            # use the interior camera views to inspect geometry without it.
            if view=='counter_overview' and style=='clay':continue
            body.append('<section>')
            for mode,label in [('before','До'),('after','После')]:
                name=f'modeled/{view}_{style}_{mode}.png'
                body.append(f'<figure><a href="{name}"><img src="{name}" loading="lazy"></a><figcaption>{label} · {style}</figcaption></figure>')
            body.append('</section>')
    (OUT/'index.html').write_text(''.join(body),encoding='utf8')
    for style in ('textured','clay'):
        views=[v for v in preview['views'] if style!='clay' or v!='counter_overview']
        sheet=Image.new('RGB',(1280,474*len(views)),(20,27,34));draw=ImageDraw.Draw(sheet)
        for row,view in enumerate(views):
            for column,mode in enumerate(('before','after')):
                im=Image.open(build/f'{view}_{style}_{mode}.png').convert('RGB').resize((640,450))
                x=column*640;y=row*474;sheet.paste(im,(x,y+24));draw.text((x+8,y+5),view+' '+mode,fill='white')
        sheet.save(build/f'{style}_review.jpg',quality=93)
    index=ROOT/'out/base_interiors/index.html';content=index.read_text(encoding='utf8')
    link='li_for_01_base/bar/counter_rework/index.html'
    if link not in content:
        index.write_text(content.replace('<ul>','<ul><li><a href="'+link+'">Liberty, li_for_01_base — боковина барной стойки и панели за барменом</a></li>',1),encoding='utf8')
    print('COUNTER_GALLERY',OUT/'index.html')


if __name__=='__main__':main()
