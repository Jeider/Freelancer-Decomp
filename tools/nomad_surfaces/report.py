"""Publish actual GPU captures as a small local comparison gallery (requires Pillow)."""
from pathlib import Path
import html
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'src/obj/nomad_surfaces'
DEST=ROOT/'docs/space_anomalies/nomad_previews'
def main():
    DEST.mkdir(parents=True,exist_ok=True)
    items=[('inside_flat','Внутри: контроль без бампа'),('inside_wet','Внутри: мощный мокрый рельеф'),('inside_light_shift','Тот же рельеф, другой свет'),('outside_relief','Снаружи: сухая плотная порода'),('dyson_relief','Dyson: облегчённый рельеф')]
    canvas=Image.new('RGB',(1440,3*580),(7,13,22));draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    sections=[]
    for i,(name,label) in enumerate(items):
        shutil.copy2(SOURCE/f'{name}.png',DEST/f'{name}.png')
        img=Image.open(SOURCE/f'{name}.png').convert('RGB');img.thumbnail((720,540))
        x=(i%2)*720;y=(i//2)*580;canvas.paste(img,(x,y+40));draw.text((x+18,y+12),label,font=font,fill='#d9e8dc')
        sections.append(f'<figure><a href="{name}.png"><img src="{name}.png" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>')
    canvas.save(DEST/'overview.jpg',quality=94)
    for name in ['validation.txt','route.txt']:
        if (SOURCE/name).exists():shutil.copy2(SOURCE/name,DEST/name)
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Nomad — мокрый рельеф</title><style>body{margin:32px auto;max-width:1500px;padding:0 24px;background:#070d16;color:#d9e8dc;font:18px/1.5 system-ui}h1{font-size:32px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:24px}figure{margin:0}img{width:100%}a{color:#85e6b3}figcaption{padding:10px}code{color:#b1f0ce}</style><h1>Nomad Lair: мощный склизкий бамп</h1><p>Реальные кадры D3D9/SM3 с исходными текстурами мода на изогнутом образце материала. Это лабораторный просмотр шейдера, не скриншоты миссии. Контроль слева использует тот же свет и материал с нулевой силой рельефа.</p><p>Внутри — параллакс впадин, складки, узкие мокрые блики и сохранённая illumination-текстура. Снаружи — матовая порода. Dyson использует облегчённый вариант без параллаксного поиска и выборок теней.</p><main>'''+''.join(sections)+'''</main><p><a href="validation.txt">GPU и frustum проверки</a> · <a href="route.txt">Маршрут RP9</a> · <a href="../../ru/space_anomalies/nomad.md">Описание реализации</a></p></html>'''
    (DEST/'report.html').write_text(page,encoding='utf8')
    print(DEST/'report.html')
if __name__=='__main__':main()
