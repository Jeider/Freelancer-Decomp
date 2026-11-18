"""Publish the focused study with explicit scope and source verification."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/elite_focus'
records=json.loads((ROOT/'out/character_rounding/li/inventory.json').read_text())
rec=next(r for r in records if r['name']=='li_male_elite_body')
assert hashlib.sha256(Path(rec['source']).read_bytes()).hexdigest()==rec['sha256']
before=json.loads((OUT/'before.json').read_text());after=json.loads((OUT/'after.json').read_text())
p=np.array(before['points']);q=np.array(after['points']);assert np.isfinite(q).all()
assert q[:,0].min()>=p[:,0].min()-1e-7 and q[:,0].max()<=p[:,0].max()+1e-7
names=[('upper','Верх тела'),('cuff','Наруч крупно'),('cuff_clay','Наруч без текстуры'),('cuff_end','Отверстие наруча снизу'),('upper_clay','Верх без текстуры'),('shoulder','Плечи и ворот')]
parts=['''<!doctype html><html lang="ru"><meta charset="utf-8"><title>LI male elite — наручи и верх</title><style>body{max-width:1500px;margin:30px auto;padding:0 20px;background:#17202b;color:#e2eaf3;font:18px/1.55 system-ui}img{width:100%}a{color:#8acbff}section{margin:35px 0}strong{color:#fbd78c}</style><h1>li_male_elite_body: наручи и верх тела</h1><p><strong>Слева исходная модель, справа новый пробный вариант.</strong> В игру ничего не установлено. Здесь переработана геометрия, свет и текстуры одинаковые.</p><p>Приоритет: округлые наручи вокруг оси предплечья, сохранение внутренней посадки, плавные плечи и ворот. Диаметр запястья взят из исходной кромки: около 110 мм с обеих сторон. Общая ширина не превышает исходную. Низ и пояс не являются целью этого прохода.</p><p>Это более активный прототип, не готовый массовый экспорт. Наручи приближены к круглой форме; небольшие отклонения оставлены ради толщины и разделения вложенных поверхностей. Накладки стали менее выраженными — их чёткость нужно оценить отдельно. Веса и анимации этого варианта ещё не проверялись.</p>''']
for name,title in names:
 with Image.open(OUT/(name+'.png')) as im:im.verify()
 parts.append(f'<section><h2>{title}</h2><a href="{name}.png"><img src="{name}.png"></a></section>')
parts.append('<p><a href="elite_comparison.blend">Blender: сравнение верхней части</a></p></html>')
(OUT/'index.html').write_text(''.join(parts),encoding='utf8')
(OUT/'validation.json').write_text(json.dumps(dict(source_unchanged=True,finite_geometry=True,width_within_original=True,verified_previews=len(names),preview_only=True),indent=2))
print(OUT/'index.html')
