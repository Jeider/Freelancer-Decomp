"""Rebuild the Rheinland review gallery from the actual exported assets."""
from rheinland_audit import *
from html import escape
import re
from PIL import Image,ImageDraw

LABELS=['Бар линкора','Берлин — бар','Бремен — станционный бар','Штутгарт — бар','Бисмарк — оборудование','Берлин — оборудование','Штутгарт — оборудование','Депо — depot deck','Линкор — deck']

def main():
    summary=json.loads((BATCH/'geometry_summary.json').read_text());mats=json.loads((BATCH/'material_validation.json').read_text())
    receipt_path=BATCH/'installed.json'
    installed=False
    if receipt_path.exists():
        receipt=json.loads(receipt_path.read_text())
        installed=receipt.get('verified',False) and all(
            (GAME/r['relative']).exists() and sha((GAME/r['relative']).read_bytes())==r['prepared']
            for r in receipt['files'])
    html=['''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Рейнланд — рельеф интерьеров</title>
<style>body{background:#141b22;color:#e0e8ee;font:16px/1.5 system-ui;max-width:1600px;margin:auto;padding:26px}a{color:#86d3ff}h1,h2,h3{font-weight:500}article{margin:38px 0;border-top:1px solid #405363;padding-top:18px}section{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0}img{width:100%;display:block}figcaption{background:#263441;padding:8px}.check{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.inspection{filter:brightness(var(--gain,1.65))}table{border-collapse:collapse}td,th{text-align:left;padding:7px 18px;border-bottom:1px solid #405363}.controls{position:sticky;top:0;background:#141b22ef;padding:10px;z-index:2}p{max-width:1250px}code{color:#b8d7e9}</style>
<h1>Рейнланд: рельеф стен и оборудования</h1>
<p>Пакет расширен до девяти моделей: добавлены depot deck и палуба рейнландского линкора. Углубления панелей, вентиляционные ниши, рёбра решёток и канавки перенесены с текущих текстур в геометрию. <b>Пакет подготовлен, в игру пока не установлен.</b></p>
<p>Неиспользуемый commercial-вариант депо, общие интерьеры других регионов и уже установленный бар Бисмарка исключены. Пол и поверхности с готовым объёмом не подразделялись. Исходные материалы, текстуры, анимации, лучи света и обе UV-развёртки сохранены.</p>
<p>Это рендеры Blender из экспортированных CMP, не скриншоты игры. Внешние декорации и персонажи отсутствуют. Освещение и смешивание материалов здесь приблизительные; игровые THN и параметры материалов не меняются. Дополнительные карты нормалей подготовлены для существующего игрового шейдера и в этих геометрических сравнениях не включены.</p>
<p>Контуры выбраны вручную по материалам; размещение во всех подходящих UV-экземплярах, проверка перекрытий и экспорт автоматизированы. Оранжевые контуры на атласах показывают кандидатов: пол и уже объёмные поверхности отсеяны при проверке модели. Сложные и неоднозначные рисунки пока сохранены без нового рельефа.</p>
<div class="controls"><label>Яркость только диагностических деталей <input type="range" min="1" max="3" step=".05" value="1.65" oninput="document.documentElement.style.setProperty('--gain',this.value)"></label> · слева исходник, справа результат</div><table><tr><th>Модель</th><th>Треугольники: было → стало</th><th>Материалы с новой геометрией</th></tr>''']
    for label,v in zip(LABELS,summary):
        names={r['material'] for r in v['changed_groups'] if r['source_triangles_with_relief']}
        html.append(f'<tr><td>{label}</td><td>{v["source_triangles"]:,} → {v["result_triangles"]:,}</td><td>{len(names)}</td></tr>')
    html.append('</table><p>Пересчитано карт нормалей и шероховатости: '+str(len(mats['records']))+'. Коэффициенты профилей сохранены. Для '+str(len(mats['skipped']))+' материалов сохранены прежние карты из-за общей идентичности с моделями вне пакета; подробности — в отчёте.</p>')
    for model,label,v in zip(MODELS,LABELS,summary):
        dest=BATCH/model;inspection=json.loads((dest/'inspection.json').read_text())
        assert inspection['prepared_sha256']==v['prepared_sha256']
        assert json.loads((dest/'preview.json').read_text())['prepared_sha256']==v['prepared_sha256']
        html.append(f'<article id="{model}"><h2>{label}</h2><p><code>{model}.cmp</code> · <a href="{model}/rheinland_relief.blend">Полная сцена Blender</a> · <a href="{model}/contour_review.jpg">Контуры на текстурах</a> · <a href="{model}/validation.json">Проверка CMP</a></p><section>')
        for mode,caption in [('before','Исходный интерьер'),('after','Интерьер с рельефом')]:html.append(f'<figure><a href="{model}/{mode}_room.png"><img loading="lazy" src="{model}/{mode}_room.png"></a><figcaption>{caption}</figcaption></figure>')
        html.append('</section><h3>Все изменённые материалы: исходник / результат / геометрия</h3>')
        board=Image.new('RGB',(1440,len(inspection['materials'])*390),(20,27,34));draw=ImageDraw.Draw(board)
        for n,r in enumerate(inspection['materials']):
            html.append(f'<p><code>{escape(r["material"])}</code></p><div class="check">')
            draw.text((10,n*390+4),r['material'],fill='white')
            for j,mode in enumerate(('before','after','clay')):
                rel=f'{model}/inspection/{r["stem"]}_{mode}.png';assert (BATCH/rel).is_file()
                html.append(f'<a href="{rel}"><img class="inspection" loading="lazy" src="{rel}" alt="{mode}"></a>')
                im=Image.open(BATCH/rel).convert('RGB').resize((480,360))
                # Identical exposure adjustment for a diagnostic contact sheet.
                im=Image.fromarray(np.minimum(np.asarray(im,float)*1.65,255).astype('uint8'));board.paste(im,(480*j,390*n+24))
            html.append('</div>')
        board.save(dest/'inspection_review.jpg',quality=92)
        html.append('</article>')
    html.append('<p>Установщик: <code>python tools/base_interiors/install.py --rheinland --apply</code>. Сначала проверяет исходные хеши, создаёт резервную копию, затем записывает пакет через DataFolder. При запущенной игре установка прекращается. Все материалы пакета: <a href="material_validation.json">отчёт</a>.</p></html>')
    document=''.join(html)
    if installed:
        document=document.replace('Пакет подготовлен, в игру пока не установлен.',
                                  'Пакет установлен в D:\\Games\\FL_MOD; все файлы проверены. Установочные копии удалены.')
    (BATCH/'index.html').write_text(document,encoding='utf8')
    topic=ROOT/'out/base_interiors/index.html';text_=topic.read_text(encoding='utf8')
    if 'rheinland_batch/index.html' not in text_:text_=text_.replace('<ul>','<ul><li><a href="rheinland_batch/index.html">Рейнланд — бары, оборудование и палубы, превью рельефа</a></li>',1)
    text_=text_.replace('Рейнланд — семь баров и комнат оборудования, превью рельефа','Рейнланд — девять интерьеров, включая depot deck и палубу линкора')
    text_=text_.replace('Общий каталог исследований и прототипов. Существующие эксперименты сохранены на прежних местах.',
                       'Текущие пакеты и сохранённые исследования. Промежуточные версии удалены при очистке диска.')
    text_=re.sub(r'<li><a href="([^"]+)">.*?</a></li>',
                 lambda m:m.group(0) if '://' in m[1] or (topic.parent/m[1]).exists() else '',text_,flags=re.S)
    topic.write_text(text_,encoding='utf8')
    print('Gallery:',BATCH/'index.html')

if __name__=='__main__':main()
