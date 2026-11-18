"""Matched rear render comparison for the angular engine shape prototype."""
import json
from PIL import Image,ImageDraw,ImageFont
from rh_freighter_engines import PREVIOUS,OUT,f

def main():
    build=json.loads((OUT/'build.json').read_text(encoding='utf8'))
    check=json.loads((OUT/'blender_check.json').read_text(encoding='utf8'))
    assert build['cmp_sha256']==check['cmp_sha256']==f.digest(OUT/'rh_pir_freighter.cmp')
    assert not check['collisions'] and len(check['recessed_engine_exhaust_rays'])==10
    sheet=Image.new('RGB',(2400,950),(37,42,47));draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
    for i,(folder,label) in enumerate(((PREVIOUS,'BEFORE / uv_02'),(OUT,'AFTER / engines_03'))):
        im=Image.open(folder/'textured_rear.png').convert('RGB');im.thumbnail((1200,900))
        sheet.paste(im,(1200*i,50));draw.text((1200*i+24,12),label,font=font,fill='white')
    sheet.save(OUT/'comparison_rear.jpg',quality=95)
    print('Comparison ready; matching CMP/Blender hash; 10 exhaust rays; no motion collisions.')

if __name__=='__main__':main()
