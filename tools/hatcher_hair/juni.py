"""Juni's concept bob, preserving the installed white streak and facial data."""
import argparse
from io import BytesIO
import numpy as np
from PIL import Image
from scipy.ndimage import label
import darcy
from build import ROOT,child,blob,arr,triangles,faces

def prepare(root):
    image=np.asarray(Image.open(BytesIO(blob(child(child(root,'Texture library'),'pl_female4_head03.TGA'),'MIP0'))).convert('RGB'))/255.
    # Connected hair region includes the white lock, but excludes isolated
    # eyebrows/eyes. Original texture bytes are never changed.
    grey=np.ptp(image,axis=2)<.10
    regions,_=label(grey);counts=np.bincount(regions[:100].ravel());counts[0]=0
    mask=regions==counts.argmax()
    def hair(s):
        u,v=s
        return mask[int((1-v)%1*(image.shape[0]-1)),int(u%1*(image.shape[1]-1))]
    for mesh in child(root,'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):continue
        groups=child(mesh,'Face_groups');geo=child(mesh,'Geometry')
        targets=[g for g in groups.children if g.children and blob(g,'Material_name').startswith(darcy.HAIR_PREFIX)]
        if not targets:continue
        target=targets[0];selected=triangles(target)
        uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
        for group in groups.children:
            if not group.children or blob(group,'Material_name').rstrip(b'\0')!=b'pl_female4_head03':continue
            retained=[]
            for t in triangles(group):
                samples=uv[ui[t]]
                tests=list(samples)+[samples.mean(axis=0)]+[(samples[i]+samples[(i+1)%3])/2 for i in range(3)]
                (selected if all(hair(s) for s in tests) else retained).append(t)
            faces(group,retained)
        faces(target,selected)

def sculpt(pos,normal,mask,level):
    x,y,z=pos;q=pos.copy()
    high=float(np.clip((y-.085)/.065,0,1))
    # Constant azimuth forms straight generators down the bob. No height-varying
    # phase: that produced the unwanted wavy/transverse creases. The subsequent
    # cheek-lock taper carries these same lines toward its pointed end.
    angle=np.arctan2(x-.018,z-.005)
    phase=angle*20
    rib=(1-abs((phase/(2*np.pi))%1-.5)*4)*.5
    strength=(1.,.7,.4,.2,0.,0.)[level]
    # Fade at the part rather than converge into a jagged crown of radial spikes.
    crown=float(np.clip((.158-y)/.045,0,1))
    crown=crown*crown*(3-2*crown)
    q+=normal*(rib*.0055*mask*strength*crown)
    # Slightly accentuate the existing side part without splitting the scalp.
    part=np.exp(-((x-.018+.12*z)/.006)**2)*high
    q[1]-=mask*.003*part
    # Lengthen and taper the long cheek-side lock into a clear asymmetric point.
    left=float(np.clip((-x-.035)/.025,0,1))
    front=float(np.clip((z-.005)/.055,0,1))
    low=float(np.clip((.06-y)/.08,0,1))
    bang=mask*left*front*low
    q[1]-=.013*bang
    q[0]+=.005*bang
    q[2]+=.003*bang
    tip=mask*left*float(np.clip((z-.005)/.035,0,1))*float(np.clip((.025-y)/.045,0,1))
    q[0]+=(-.066-q[0])*tip*.85
    q[2]+=(.073-q[2])*tip*.80
    q[1]-=.007*tip
    # Tighten the rear lower edge; leave the short undercut at the nape intact.
    if -.025<y<.035 and z<-.025:
        blend=mask*float(np.clip((.035-y)/.055,0,1))*.32
        q[1]+=(.006-y)*blend
    return q

darcy.OUT=ROOT/'out/juni_hair'
darcy.REL='CHARACTERS/HEADS/pl_female4_head.dfm'
darcy.HAIR_PREFIX=b'short_hair_pl_female4'
darcy.PREPARE=prepare
darcy.SCULPT=sculpt
darcy.FOLDED_LOCKS=False
darcy.SUBDIVISION_DEPTH=(3,2,1,0,0,0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    # The sculpted/ribbed mesh was rejected. Keep the public entry point on the
    # original-mesh UV/normal workflow so rebuilding cannot reinstall it.
    import juni_surface
    darcy.install() if args.apply else juni_surface.build()
