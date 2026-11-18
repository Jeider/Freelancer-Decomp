"""Seeded image-edge tracing, not approximate rectangle extrusion."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,map_coordinates,gaussian_filter1d
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'out/base_interiors/rh_biz_01_base/bar';OUT=BASE/'prototype_v8';OUT.mkdir(exist_ok=True)
sources={'r_bar_15':'ac1251d209bf','r_bar_09':'c0766e36365e'}
seeds={'r_bar_15':[
 [[9,450],[197,594],[127,670],[3,541]],
 [[233,657],[416,738],[378,826],[163,719]],
 [[496,760],[676,784],[670,887],[438,849]],
 [[735,785],[937,743],[973,842],[735,886]]],
 'r_bar_09':[[[790,758],[886,692],[940,758],[790,852]],[[910,671],[1005,592],[1005,691],[955,730]]]}
features={};reports={}
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def triangulate(p):
 ids=list(range(len(p)));tris=[]
 while len(ids)>3:
  for k,j in enumerate(ids):
   a,b,c=ids[k-1],j,ids[(k+1)%len(ids)]
   if cross(p[b]-p[a],p[c]-p[b])<1e-7:continue
   contains=False
   for q in ids:
    if q in (a,b,c):continue
    if min(cross(p[b]-p[a],p[q]-p[a]),cross(p[c]-p[b],p[q]-p[b]),cross(p[a]-p[c],p[q]-p[c]))>=-1e-7:contains=True;break
   if contains:continue
   tris.append([a,b,c]);ids.pop(k);break
  else:raise ValueError('Non-simple traced polygon')
 tris.append(ids);return tris
for name,file in sources.items():
 im=Image.open(BASE/'prototype_v1/textures'/f'{file}.png').convert('RGB');rgb=np.array(im,dtype=float)/255
 lum=gaussian_filter(rgb@np.array([.3,.5,.2]),1.4)
 def sample(points):return map_coordinates(lum,[points[...,1],points[...,0]],order=1,mode='nearest')
 output=[];paths=[];metrics=[]
 for panel,raw in enumerate(seeds[name]):
  p=np.array(raw,float)
  if sum(cross(a,b) for a,b in zip(p,np.roll(p,-1,axis=0)))<0:p=p[::-1]
  traced=[]
  for edge,(a,b) in enumerate(zip(p,np.roll(p,-1,axis=0))):
   direction=b-a;normal=np.array([direction[1],-direction[0]])/np.linalg.norm(direction)
   ts=np.linspace(.05,.95,40);line=a+ts[:,None]*direction
   shifts=np.arange(-24,25,dtype=float);points=line[:,None,:]+shifts[None,:,None]*normal
   contrast=sample(points+normal*4)-sample(points-normal*4)
   # Prefer the field/frame transition, while suppressing noisy texture detail.
   score=contrast/max(np.quantile(abs(contrast),.9),.008)-.0009*shifts[None,:]**2
   cost=-score[0];back=[];penalty=.055*(shifts[:,None]-shifts[None,:])**2
   for row in score[1:]:
    matrix=cost[:,None]+penalty;idx=np.argmin(matrix,axis=0);back.append(idx);cost=matrix[idx,np.arange(len(shifts))]-row
   j=int(np.argmin(cost));selected=[j]
   for idx in back[::-1]:j=int(idx[j]);selected.append(j)
   offsets=shifts[np.array(selected[::-1])]
   # Curved top/bottom, straight structural sides. Fit is local to each painted edge.
   degree=2 if edge in (0,2) else 1;fit=np.polyfit(ts,offsets,degree)
   t=np.linspace(0,1,13);curve=a+t[:,None]*direction+np.polyval(fit,t)[:,None]*normal
   traced.append(curve);metrics.append({'panel':panel,'edge':edge,'median_shift_px':float(np.median(offsets)),'fit_rms_px':float(np.sqrt(np.mean((np.polyval(fit,ts)-offsets)**2)))})
  # Join adjacent curves at their intersection, retaining the measured curved spans.
  for k in range(4):
   prev=traced[k-1];cur=traced[k];a=prev[-1];b=cur[0];u=prev[-1]-prev[-2];v=cur[1]-cur[0]
   try:q=a+np.linalg.solve(np.column_stack((u,-v)),b-a)[0]*u
   except np.linalg.LinAlgError:q=(a+b)/2
   dp=q-prev[-1];dc=q-cur[0]
   for n in range(3):prev[-1-n]+=dp*(1-n/3);cur[n]+=dc*(1-n/3)
  outer=np.concatenate([c[:-1] for c in traced])
  keep=[i for i in range(len(outer)) if abs(cross(outer[i]-outer[i-1],outer[(i+1)%len(outer)]-outer[i]))>1e-5]
  outer=outer[keep];center=outer.mean(0)
  # Narrow bevel follows the measured border; no displaced UVs and no floating rails.
  inner=center+(outer-center)*.955;depth=-.035
  for j in range(len(outer)):
   k=(j+1)%len(outer);quad=np.array([outer[j],outer[k],inner[k],inner[j]])
   output.append({'label':f'{name}_traced_panel_{panel}_bevel_{j}','uv':(quad/1024).tolist(),'depth':depth,'inset':1,'heights':[0,0,depth,depth]})
  for j,ids in enumerate(triangulate(inner)):
   output.append({'label':f'{name}_traced_panel_{panel}_floor_{j}','uv':(inner[ids]/1024).tolist(),'depth':depth,'inset':1})
  paths.append(outer.tolist())
 features[name]=output;reports[name]={'edge_fits':metrics,'panel_contours_px':paths}
 # Diagnostic overlay only: original game textures are never modified.
 draw=ImageDraw.Draw(im)
 for path in paths:draw.line([tuple(x) for x in path+[path[0]]],fill=(0,255,180),width=2)
 im.save(OUT/(name+'_contour_check.png'))
(OUT/'registered_features.json').write_text(json.dumps(features,indent=2));(OUT/'trace_report.json').write_text(json.dumps(reports,indent=2))
print('Traced six curved panel fields on two material textures. See contour-check images before building.')
