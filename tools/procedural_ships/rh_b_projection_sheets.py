"""Label matched offline renders; retain every original full-size frame."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parents[2]/'out/ship_design/rh_elite/prototypes/concept_b/final_v2/lod_refinement'
FONT='C:/Windows/Fonts/arial.ttf'


def sheet(name,columns,views,width=560):
    height=round(width*2/3);header=56;caption=42
    canvas=Image.new('RGB',(width*len(columns),header+(height+caption)*len(views)),(27,31,36))
    draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(FONT,20)
    draw.text((18,16),'RH concept B · проекции собственной модели · Blender',font=font,fill='white')
    for y,view in enumerate(views):
        for x,(prefix,title) in enumerate(columns):
            row=header+y*(height+caption)
            draw.text((x*width+14,row+10),title,font=font,fill=(224,226,229))
            im=Image.open(OUT/(prefix+'_'+view+'.png')).convert('RGB').resize((width,height),Image.Resampling.LANCZOS)
            canvas.paste(im,(x*width,row+caption))
    canvas.save(OUT/name)


def main():
    counts=json.loads((OUT/'validation.json').read_text())['lod_triangles']
    sheet('comparison_lods.png',[(p,'LOD'+str(i)+' · '+str(counts[i])+' треугольников') for i,p in enumerate(('near','after_lod1','after_lod2'))],['iso','side','top'])
    sheet('comparison_before_after.png',[('before_lod1','LOD1 до'),('after_lod1','LOD1 с проекциями'),('before_lod2','LOD2 до'),('after_lod2','LOD2 с проекциями')],['iso','side'],480)
    # Small images are an illustration of apparent distance, not game footage
    # or a measurement of the renderer's LOD switch distances.
    canvas=Image.new('RGB',(1080,550),(27,31,36));d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype(FONT,18)
    for row,w in enumerate((300,160)):
        for col,(prefix,label) in enumerate((('near','LOD0'),('after_lod1','LOD1'),('after_lod2','LOD2'))):
            x=col*360;y=row*260
            d.text((x+18,y+16),label+' · кадр шириной '+str(w)+' px',font=font,fill='white')
            im=Image.open(OUT/(prefix+'_iso.png')).convert('RGB').resize((w,round(w*2/3)),Image.Resampling.LANCZOS)
            canvas.paste(im,(x+(360-w)//2,y+55))
    canvas.save(OUT/'distance_comparison.png')
    print('Comparison sheets ready')


if __name__=='__main__':main()
