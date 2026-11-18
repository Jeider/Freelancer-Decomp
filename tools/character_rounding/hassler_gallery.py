"""Build the offline Hassler review page and UV editing guides."""
import gzip,json,html,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/hassler'

def main():
    validation=json.loads((OUT/'validation.json').read_text());uv=json.loads((OUT/'uv_regions.json').read_text())
    wire=json.loads(gzip.decompress((OUT/'uv_wire.json.gz').read_bytes()));size=uv['atlas_size']
    image=Image.new('RGBA',(size,size));draw=ImageDraw.Draw(image)
    for face in wire:
        pts=[(round(u*(size-1)),round((1-v)*(size-1))) for u,v in face]
        draw.line(pts+[pts[0]],fill=(235,243,250,125),width=1)
    image.save(OUT/'textures/hassler_uv_wire.png')
    thumb=Image.open(OUT/'textures/hassler_color.png').convert('RGB').resize((1600,1600));draw=ImageDraw.Draw(thumb)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    for i,region in enumerate(uv['regions']):
        (x0,y0),(x1,y1)=region['bounds'];rect=(int(x0*1600),int((1-y1)*1600),int(x1*1600),int((1-y0)*1600))
        draw.rectangle(rect,outline=(90,195,255),width=2);label=str(i+1)+' '+region['name']
        box=draw.textbbox((rect[0]+3,rect[1]+3),label,font=font);draw.rectangle(box,fill=(15,23,31));draw.text((rect[0]+3,rect[1]+3),label,font=font,fill='white')
    thumb.save(OUT/'uv_guide.jpg',quality=92)
    cards=''.join('<figure><img src="preview/'+name+'.png"><figcaption>'+title+'</figcaption></figure>' for name,title in
                 [('front','Спереди'),('back','Сзади'),('upper','Воротник, эполеты и пояс'),('elbows','Сгиб локтей — синтетическая проверка'),('step','Шаг — синтетическая проверка')])
    page='''<!doctype html><meta charset="utf-8"><title>Хасслер — Blender-прототип</title>
<style>body{background:#151a21;color:#e7edf4;font:17px system-ui;max-width:1450px;margin:35px auto;padding:0 25px}a{color:#79c4ff}h1{font-size:32px}p{max-width:1050px;line-height:1.55}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}figure{margin:0;background:#242c36}img{width:100%;display:block}figcaption{padding:12px}.uv{max-width:1100px}</style>
<h1>Хасслер: Meshy → скелет rh_male_elite_body</h1>
<p><a href="hassler_rigged.blend">Открыть Blender</a> · <a href="README.txt">Как редактировать</a> · <a href="validation.json">Проверки</a></p>
<p>Отдельный офлайн-прототип. Голова и перчатки — штатные детали костюма Хасслера. Кобура удалена, пояс восстановлен. Исходники Meshy и исходное тело сохранены в скрытых коллекциях. Установленных моделей и настроек игра не затрагивает.</p>
<p>Тело: '''+str(validation['body_triangles'])+''' треугольников; скелет — 28 костей. Проверен диапазон 16-битных индексов DFM. Это не проверка игрового экспорта или настоящих игровых анимаций.</p>
<p>Таймлайн: 1 — исходная поза; 30 — локти; 60 — плечи; 90 — шаг; 120 — поворот; 150 — исходная поза.</p><div class="grid">'''+cards+'''</div>
<h2>UV по участкам одежды</h2><p>Сохранён исходный слой Meshy. Новый слой — EDIT — clothing charts. Общий атлас 4096×4096 и отдельные карты цвета, нормалей, шероховатости и металличности. Для рисования: <a href="textures/hassler_color.png">цвет</a> · <a href="textures/hassler_uv_wire.png">прозрачная сетка</a> · <a href="uv_regions.json">индекс участков</a>.</p><img class="uv" src="uv_guide.jpg">
<p>Предварительная посадка одежды и синтетические позы проверены. Перед игровым применением нужны игровые анимации, дальнейшая настройка весов по результатам просмотра и отдельные LOD. Главная цель этой версии — оценить образ и работу тела на родном скелете.</p>'''
    (OUT/'index.html').write_text(page,encoding='utf8')
    print('GALLERY',OUT/'index.html')

if __name__=='__main__':main()
