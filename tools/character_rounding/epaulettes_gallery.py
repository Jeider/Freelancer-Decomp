"""Publish the two offline shoulder studies and their editable sources."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
import epaulettes as e


def main():
    installed={name:json.loads((e.OUT/name/'installed.json').read_text()) for name in e.TARGETS if (e.OUT/name/'installed.json').exists()}
    all_installed=set(installed)==set(e.TARGETS) and all(r['verified'] for r in installed.values())
    status='Установлено в игру; файлы проверены после записи.' if all_installed else 'Подготовлено отдельно от игры.'
    body=['<meta charset="utf-8"><style>body{background:#192028;color:#e4edf4;font:17px system-ui;max-width:1450px;margin:28px auto;padding:18px}a{color:#88d9ff}section{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:26px}figure{margin:0}img{width:100%;display:block}figcaption{padding:8px;background:#29333e}p{line-height:1.5}</style>',
          f'<h1>Эполеты Райхмана и Дитриха</h1><p><b>{status}</b> Уточнена кривизна выступающих накладок и внешних кромок. '
          'Сохранены текущие текстуры, исходное поле нормалей, веса костей и улучшенные наручи. '
          'Новая геометрия находится только в дополнительном Mesh0; исходный Mesh1 и остальные LOD сохранены.</p>',
          '<p>Сравнения ниже сделаны при одинаковом освещении в Blender. Это офлайн-превью, игровой шейдер здесь не воспроизводится. '
          'Проверки движения — синтетические преобразования костей, а не воспроизведение катсцен в игре.</p>']
    labels={'upper_front':'Верх тела спереди','upper_back':'Верх тела сзади','right_front':'Правое плечо спереди',
            'right_top':'Правое плечо сверху','right_rear':'Правое плечо сзади','left_front':'Левое плечо спереди'}
    for name,title in [('rh_reichman_body','Райхман'),('rh_deidrich_body','Дитрих')]:
        folder=e.OUT/name;report=json.loads((folder/'report.json').read_text())
        native=json.loads((folder/'native_validation.json').read_text());preview=json.loads((folder/'preview_validation.json').read_text())
        surface=json.loads((folder/'surface_validation.json').read_text())
        assert native['geometry_sha256']==report['geometry_sha256']==preview['geometry_sha256']==surface['geometry_sha256']
        assert native['all_passed'] and surface['all_passed'] and preview['reopened']
        assert e.c.digest((folder/'epaulettes.blend').read_bytes())==preview['blend_sha256']
        is_installed=name in installed
        if is_installed:
            receipt=installed[name]
            assert receipt['verified'] and e.c.digest(Path(receipt['target']).read_bytes())==receipt['sha256']==native['dfm_sha256']
        model_link=(f'<a href="{name}/installed.json">Отчёт об установленном DFM</a>' if is_installed else
                    f'<a href="stage/DATA/CHARACTERS/BODIES/{name}.dfm">Подготовленный DFM</a>')
        body.extend([f'<h2 id="{name}">{title}</h2><p>Всё тело: <b>{report["triangles_before"]} → {report["triangles_after"]} треугольников</b>. '
                     f'Исходный LOD1: {json.loads((folder/"source.json").read_text())["lods"]["Mesh1"]["triangles"]}. '
                     'Количество материалов сохранено.</p>',
                     f'<p><a href="{name}/epaulettes.blend">Blender с UV и весами</a> · '
                     f'{model_link} · '
                     f'<a href="{name}/native_validation.json">Проверка экспорта</a> · '
                     f'<a href="{name}/surface_validation.json">Проверка пересечений</a></p>'])
        for view in preview['views']:
            body.append('<h3>'+labels[view]+'</h3>')
            for style in ('textured','clay'):
                body.append('<section>')
                for mode,label in [('before','До улучшения' if is_installed else 'Установлено сейчас'),('after','Установленный вариант' if is_installed else 'Новый вариант')]:
                    path=f'{name}/{view}_{style}_{mode}.png'
                    body.append(f'<figure><a href="{path}"><img loading="lazy" src="{path}"></a><figcaption>{label} · {style}</figcaption></figure>')
                body.append('</section>')
        for style in ('textured','clay'):
            sheet=Image.new('RGB',(1200,474*len(preview['views'])),(20,27,34));draw=ImageDraw.Draw(sheet)
            for row,view in enumerate(preview['views']):
                for col,mode in enumerate(('before','after')):
                    im=Image.open(folder/f'{view}_{style}_{mode}.png').convert('RGB').resize((600,450))
                    sheet.paste(im,(col*600,row*474+24));draw.text((col*600+6,row*474+4),view+' '+mode,fill='white')
            sheet.save(folder/f'{style}_review.jpg',quality=94)
    (e.OUT/'index.html').write_text(''.join(body),encoding='utf8')
    index=e.OUT.parent/'README.txt';text=index.read_text(encoding='utf8')
    topic_line='Эполеты Райхмана и Дитриха: epaulettes/index.html — '+('установлены, файлы проверены.' if all_installed else 'отдельные прототипы, пока не установлены.')
    if 'epaulettes/index.html' not in text:
        text=topic_line+'\nИсточники и порядок пересборки: ../../tools/character_rounding/EPAULETTES.txt.\n\n'+text
    else:
        text=''.join(topic_line+'\n' if line.startswith('Эполеты Райхмана и Дитриха: epaulettes/index.html') else line for line in text.splitlines(keepends=True))
    index.write_text(text,encoding='utf8')
    print('GALLERY',e.OUT/'index.html')


if __name__=='__main__':main()
