"""Comparison plates from actual offline renders, with identical cameras."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]/'out/hatcher_body_full_smooth'
def plate(view,items,target):
    images=[Image.open(ROOT/(mode+'_'+view+'.png')).convert('RGB') for mode,_ in items]
    width,height=images[0].size
    plate=Image.new('RGB',(width*len(items),height+70),'#252525');draw=ImageDraw.Draw(plate)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',32)
    for i,(im,(_,title)) in enumerate(zip(images,items)):
        plate.paste(im,(i*width,70));draw.text((i*width+width/2,35),title,font=font,fill='white',anchor='mm')
    plate.save(ROOT/target)
items=[('before','Original mesh'),('geometry','Rounded mesh - LOD0 only')]
for name in ['full','vest','bracer','back','vest_clay','bracer_clay','boots','legs','belt','full_clay','boots_clay','legs_clay','belt_clay','back_clay']:
    plate(name,items,'comparison_'+name+'.png')
