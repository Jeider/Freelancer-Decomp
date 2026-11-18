"""Reference comparison, including both endpoints of the authored wing channel."""
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import style_audit as a

rows=a.inventory()[0]
old=next(r for r in rows if r['model'].endswith('/rh_elite.cmp'))
alt=next(r for r in rows if r['model'].endswith('/rh_alt_elite.cmp'))
loaded=[a.load(old),a.load(alt,('Sc_extend wing',0)),a.load(alt,('Sc_extend wing',1))]
points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for s,_,_ in loaded for g in s])
bounds=(points.min(axis=0),points.max(axis=0))
size=620
sheet=Image.new('RGB',(size*3,2*(size+40)+65),(24,29,37));d=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',21)
names=['rh_elite / current source','rh_alt_elite / channel first frame','rh_alt_elite / channel last frame']
for col,((scene,mats,stats),name) in enumerate(zip(loaded,names)):
    d.text((col*size+12,10),name,font=font,fill='white')
    for row,camera in enumerate(((1,.85,-1.4),(0,1,.001))):
        sheet.paste(a.image_for(scene,mats,camera,size,'texture',bounds),(col*size,45+row*(size+40)))
    d.text((col*size+12,sheet.height-32),f"{stats['triangles']} triangles / {len(stats['parts'])} mesh parts",font=font,fill='white')
sheet.save(a.OUT/'rh_comparison.jpg',quality=95)
comparison=dict(old=loaded[0][2],alternative=loaded[1][2],
                note='Same scale/cameras. First and last frames of Sc_extend wing only; no claim about live animation sequencing.')
(a.OUT/'rh_comparison.json').write_text(json.dumps(comparison,indent=2))
print('Saved rh_comparison.jpg and rh_comparison.json')
