"""Local review index for the installed/staged regional depot family."""
import argparse,json,html
from pathlib import Path
from PIL import Image,ImageDraw
from depot_family_audit import paths,REGIONS,FAMILY
from native_common import ROOT

STYLE='<meta charset="utf-8"><style>body{background:#161d24;color:#e7edf3;font:17px system-ui;max-width:1500px;margin:32px auto;padding:20px}a{color:#7fcef5}img{width:100%;display:block}section{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:30px}figure{margin:0}figcaption{padding:10px;background:#263340}p{max-width:1100px;line-height:1.5}td,th{padding:10px;text-align:left}</style>'


def gallery(region):
    out,live,_,_=paths(region);build=out/'modeled'
    native=json.loads((build/'native_validation.json').read_text())
    preview=json.loads((build/'preview_validation.json').read_text())
    assert preview['cmp_sha256']==native['exported_sha256'],'Preview must match the current export'
    installed=(build/'installed.json').exists()
    body=[STYLE,f'<h1>{REGIONS[region]} — depot deck</h1>',
        '<p>'+('Установлено в игру.' if installed else 'Подготовлено к установке.')+
        f' Треугольники: {native["source_triangles"]:,} → {native["result_triangles"]:,}. '
        'Стены, углубления, панели и двери. Сохранены текущие материалы, текстуры и механизмы.</p>',
        '<p>Ниже — офлайн-рендеры с одинаковым диагностическим светом, не кадры из игры. '
        'Контуры вручную перенесены с RH после проверки рисунков региональных атласов. '
        'Исходные заменённые поверхности в Blender скрыты и во вьюпорте, и в рендере.</p>',
        f'<p><a href="{region}_depot_deck_relief.blend">Редактируемый Blender</a> · '
        '<a href="features.json">Контуры и привязки</a> · <a href="contour_review.jpg">Контуры на текстурах</a> · '
        '<a href="surface_validation.json">Проверка UV</a> · <a href="door_validation.json">Все повторения дверей</a></p>']
    for view in preview['views']+preview['door_views']:
        body.append(f'<h2>{html.escape(view)}</h2>')
        for style in ('textured','clay'):
            body.append('<section>')
            for mode,label in [('before','До'),('after','После')]:
                name=f'{view}_{style}_{mode}.png'
                body.append(f'<figure><a href="{name}"><img loading="lazy" src="{name}"></a><figcaption>{label} · {style}</figcaption></figure>')
            body.append('</section>')
    (build/'index.html').write_text(''.join(body),encoding='utf8')
    # Compact sheets for the agent's visual audit, with matched pairs.
    for kind,views,width,height in [('walls',preview['views'],560,420),('doors',preview['door_views'],420,560)]:
        sheet=Image.new('RGB',(width*2,(height+24)*len(views)),(20,27,34));draw=ImageDraw.Draw(sheet)
        for row,view in enumerate(views):
            for column,mode in enumerate(('before','after')):
                im=Image.open(build/f'{view}_textured_{mode}.png').convert('RGB').resize((width,height))
                x=column*width;y=row*(height+24);sheet.paste(im,(x,y+24));draw.text((x+8,y+5),view+' '+mode,fill='white')
        sheet.save(build/f'{kind}_review.jpg',quality=92)
    print('GALLERY',build/'index.html')


def index():
    rows=[]
    for region in REGIONS:
        out,*_=paths(region);p=out/'modeled/native_validation.json'
        if not p.exists():continue
        n=json.loads(p.read_text());state='Установлено' if (out/'modeled/installed.json').exists() else 'Подготовлено'
        rows.append(f'<tr><td><a href="{region}_depot_deck/modeled/index.html">{REGIONS[region]}</a></td>'
            f'<td>{n["source_triangles"]:,}</td><td>{n["result_triangles"]:,}</td><td>{state}</td></tr>')
    body=STYLE+'<h1>Depot deck — Liberty, Bretonia, Kusari</h1><p>Перенос геометрической доработки RH: стены, ниши и механические двери. '
    body+='Каждый вариант использует свои текущие текстуры. Все базы с соответствующим общим CMP получают эту геометрию автоматически.</p>'
    body+='<table><tr><th>Регион</th><th>До, треуг.</th><th>После, треуг.</th><th>Состояние</th></tr>'+''.join(rows)+'</table>'
    body+='<p><a href="../rheinland_batch/rh_depot_deck/rework/modeled/index.html">Исходная доработка RH</a></p>'
    (FAMILY/'index.html').write_text(body,encoding='utf8')
    topic=ROOT/'out/base_interiors/index.html';content=topic.read_text(encoding='utf8')
    if 'depot_family/index.html' not in content:
        content=content.replace('<ul>','<ul><li><a href="depot_family/index.html">Depot deck — перенос рельефа на LI, BR и KU</a></li>',1)
        topic.write_text(content,encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('regions',nargs='+',choices=list(REGIONS));args=ap.parse_args()
    for region in args.regions:gallery(region)
    index()
