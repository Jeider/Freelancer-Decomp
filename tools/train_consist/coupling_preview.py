"""Orthographic closeups of the actual meshes at the new coupling axes."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'train_sur'))
import build as sur
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/train_consist'
parts=sur.read_cmp(OUT/'train_consist.cmp')
im=Image.new('RGB',(1000,750),'#f4f6fa');draw=ImageDraw.Draw(im)
for row,(parent,child) in enumerate([('Root','TrainWagon01'),('TrainWagon01','TrainWagon02')]):
    a,b=parts[parent],parts[child]
    pivot=np.array(a.hardpoints['HpCoupleRear'])
    draw.text((25,20+row*375),parent+' -> '+child+'; side Z/Y; red = shared pivot',fill='#162737')
    def screen(tri):
        return [(500+float(p[2]-pivot[2])*27,320+row*375-float(p[1]+4)*17) for p in tri]
    for tris,color in [(a.triangles,'#778b9b'),(b.triangles+b.translation,'#d19950')]:
        for t in sorted(tris,key=lambda t:t[:,0].mean()):
            if abs(t[:,2].mean()-pivot[2])<16:
                draw.polygon(screen(t),fill=color,outline='#334f5c')
    x,y=screen([pivot])[0]
    draw.line([(x,55+row*375),(x,340+row*375)],fill='#d42932',width=2)
    draw.ellipse((x-4,y-4,x+4,y+4),fill='#d42932')
im.save(OUT/'coupling_axes.png')
