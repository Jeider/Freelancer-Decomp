"""Comparison plates from actual offline renders, with identical cameras."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]/'out/reichman_body_test_v3'
def plate(view,items,target):
    images=[Image.open(ROOT/(mode+'_'+view+'.png')).convert('RGB') for mode,_ in items]
    width,height=images[0].size
    plate=Image.new('RGB',(width*len(items),height+70),'#252525');draw=ImageDraw.Draw(plate)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',32)
    for i,(im,(_,title)) in enumerate(zip(images,items)):
        plate.paste(im,(i*width,70));draw.text((i*width+width/2,35),title,font=font,fill='white',anchor='mm')
    plate.save(ROOT/target)
items=[('before','Исходник'),('previous','Первый вариант'),('full','Первый вариант + рельеф отделки')]
plate('quarter',items,'comparison_quarter.png')
plate('chest',items,'comparison_chest.png')
plate('full',items,'comparison_full.png')
plate('back',items,'comparison_back.png')
plate('clay',[('previous','Геометрия первого варианта'),('geometry','Локальный рельеф до 1,5 мм')],'comparison_clay.png')
print(ROOT/'comparison_quarter.png')
