"""Publish only successfully rendered realistic-study images; never invent previews.

Requires the separately authorized build/render, --checks, and Pillow.
"""
from pathlib import Path
import hashlib
import html
import json
import shutil
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'src/obj/space_anomalies/realistic'
DEST=ROOT/'docs/space_anomalies/realistic_previews'

def main():
    presets=json.loads(Path(__file__).with_name('presets.realistic.json').read_text(encoding='utf8'))
    final_log=(WORK/'final/render.log').read_text(encoding='utf8')
    check_log=(WORK/'checks/render.log').read_text(encoding='utf8')
    for log in [final_log,check_log]:
        assert 'LOOK realistic quality=2' in log
        assert 'PASS shader compilation' in log and 'finite_nonnegative=FAIL' not in log
    # A quiet, non-accreting black hole is physically static. Do not require
    # invented temporal noise just to satisfy the earlier theatrical checks.
    metrics={}
    def difference(a,b):
        return ImageChops.difference(Image.open(a).convert('RGB'),Image.open(b).convert('RGB')).getbbox() is not None
    for p in presets:
        name=p['id'];stem=WORK/'checks'/name
        assert difference(stem.with_suffix('.png'),Path(str(stem)+'_orbit.png')),name
        moving=difference(stem.with_suffix('.png'),Path(str(stem)+'_time.png'))
        assert moving==(name!='01_monkey'),(name,moving)
        metrics[name]={'motion':moving,'orbit_changed':True}
        assert Image.open(WORK/f'final/{name}.png').size==(3840,2160)
    assert not difference(WORK/'checks/01_monkey.png',WORK/'checks/01_monkey_repeat.png')
    assert difference(WORK/'checks/05_magnetar.png',WORK/'checks/05_magnetar_flare.png')
    DEST.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(1600,4*500),(3,5,8));draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    cards=[]
    for i,p in enumerate(presets):
        filename=p['id']+'.png';shutil.copy2(WORK/'final'/filename,DEST/filename)
        im=Image.open(WORK/'final'/filename).convert('RGB');im.thumbnail((800,450))
        x=(i%2)*800;y=(i//2)*500;sheet.paste(im,(x,y));draw.text((x+14,y+459),p['title'],font=font,fill='#d5d9df')
        cards.append(f'<article><h2>{html.escape(p["title"])}</h2><a href="{filename}"><img src="{filename}" alt="{html.escape(p["title"])}"></a><p>{html.escape(p["description"])}</p></article>')
    sheet.save(DEST/'overview.jpg',quality=95)
    source_files=list((ROOT/'DATA_EXTRA/SHADERS/ANOMALIES').glob('*'))+[Path(__file__).with_name('presets.realistic.json'),Path(__file__).with_name('render.cpp')]
    manifest={'renderer':'D3D9 HAL, SM3, FP16 HDR','style':'realistic','quality':'epic','resolution':[3840,2160],
        'checks':metrics,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files if p.is_file()},
        'limitation':'GPU laboratory captures, not in-game screenshots or a full physical/spectral simulation.'}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    shutil.copy2(WORK/'checks/render.log',DEST/'validation.txt')
    shutil.copy2(WORK/'final/render.log',DEST/'render_4k.txt')
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Аномалии — реалистичные прототипы</title><style>body{max-width:1800px;margin:40px auto;padding:0 28px;background:#030508;color:#d5d9df;font:18px/1.5 system-ui}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:32px}img{width:100%}h2{font-size:23px}a{color:#a8bfd3}</style><h1>Аномалии: реалистичный вариант максимального качества</h1><p>Реальные рендеры прототипов, 3840×2160. Спектральный отклик и художественные допущения описаны в <a href="../../ru/space_anomalies/realistic.md">отчёте</a>.</p><main>'''+''.join(cards)+'''</main><p><a href="validation.txt">Проверки GPU</a> · <a href="manifest.json">Параметры и происхождение</a></p></html>'''
    (DEST/'report.html').write_text(page,encoding='utf8')
    print(DEST/'report.html')
if __name__=='__main__':main()
