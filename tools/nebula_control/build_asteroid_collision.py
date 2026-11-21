"""Offline Omega-15 convex collision shells from the installed visible geometry."""
from pathlib import Path
import sys, json, struct, hashlib, subprocess
import numpy as np
from scipy.spatial import ConvexHull
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/performance'
GAME=Path('D:/Games/FL_MOD')
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from tools.train_sur.build import make_hull,encode_surface
from tools.tradelane.docking_surface import parts
from repair_panel_normals import leaves,triangles
from build_asf_hq import compiler_env

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    from PIL import Image,ImageDraw
    stage=OUT/'collision';originals=stage/'originals';originals.mkdir(parents=True,exist_ok=True)
    report={'passed':False,'models':[],'game_launched':False,'method':'one closed convex hull of actual render vertices; original centre and inertia retained'}
    preview=Image.new('RGB',(1200,1240),'#eeeeee');draw=ImageDraw.Draw(preview)
    draw.text((20,10),'Visible mesh (grey), collision outline (orange)',fill='black')
    for row,letter in enumerate('abc'):
        model=GAME/f'DATA/SOLAR/ASTEROIDS_MOD/om15/ast_o15_nrml_{letter}.3db'
        source=model.with_suffix('.sur');reference=originals/source.name
        if not reference.exists():reference.write_bytes(source.read_bytes())
        nodes=leaves(model.read_bytes())[1]
        blob=next(b for n,_,b in nodes if n.lower().endswith('/vmeshdata'))
        groups=triangles(blob)[2]
        points=np.array([struct.unpack('<8f',v)[:3] for group in groups for v in group])
        tris=points.reshape(-1,3,3);hull=make_hull(points,0)
        surface,lo,hi=encode_surface([hull]);surface=bytearray(surface)
        parsed=parts(reference.read_bytes());assert len(parsed)==1 and parsed[0][0]==0
        old=dict(parsed[0][1])[b'surf'];surface[:24]=old[:24]
        centre=np.array(struct.unpack_from('<3f',old));radius=np.linalg.norm(points-centre,axis=1).max()
        struct.pack_into('<f',surface,24,float(radius)*1.000001)
        result=bytearray(b'vers'+struct.pack('<fII',2.,0,len(parsed[0][1])))
        for tag,data in parsed[0][1]:
            if tag==b'surf':data=surface;result+=tag+struct.pack('<I',len(data))+data
            elif tag==b'exts':result+=tag+struct.pack('<6f',*lo,*hi)
            elif tag==b'hpid':result+=tag+struct.pack('<I',len(data)//4)+data
            else:result+=tag+data
        target=stage/source.name;target.write_bytes(result);assert parts(result)[0][0]==0
        convex=ConvexHull(hull.points);eq=convex.equations
        assert (points@eq[:,:3].T+eq[:,3]).max()<.001
        # Independent radial surface comparison: nearest visible triangle hit vs hull.
        n=2048;i=np.arange(n);y=1-2*(i+.5)/n;theta=i*np.pi*(3-5**.5)
        dirs=np.column_stack((np.sqrt(1-y*y)*np.cos(theta),y,np.sqrt(1-y*y)*np.sin(theta)))
        origin=(lo+hi)/2;gap=[]
        e1=tris[:,1]-tris[:,0];e2=tris[:,2]-tris[:,0];tv=origin-tris[:,0]
        for direction in dirs:
            cross=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,cross)
            good=np.abs(det)>1e-8;inv=np.zeros_like(det);inv[good]=1/det[good]
            u=np.einsum('ij,ij->i',tv,cross)*inv;q=np.cross(tv,e1);v=q@direction*inv
            t=np.einsum('ij,ij->i',e2,q)*inv
            good&=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>0)
            assert good.any(),'model must enclose centre'
            native=t[good].min();denom=eq[:,:3]@direction;valid=denom>1e-8
            collision=np.min(-(eq[valid,:3]@origin+eq[valid,3])/denom[valid])
            gap.append(float(collision-native))
        assert min(gap)>-.002 and max(gap)<radius*.23,(letter,max(gap),radius)
        for col,(a,b) in enumerate(((0,1),(0,2),(2,1))):
            def xy(p):return (int(col*400+200+p[a]*3.5),int(row*400+240-p[b]*3.5))
            for tri in tris:draw.line([xy(p) for p in tri[[0,1,2,0]]],fill='#999999')
            projected=ConvexHull(hull.points[:,[a,b]]);outline=hull.points[projected.vertices][:,[a,b]]
            draw.line([(int(col*400+200+p[0]*3.5),int(row*400+240-p[1]*3.5)) for p in np.vstack((outline,outline[0]))],fill='#e85b25',width=3)
            draw.text((col*400+20,row*400+60),f'{letter}: {"XYZ"[a]}/{"XYZ"[b]}',fill='black')
        report['models'].append({'model':str(model),'model_sha256':digest(model),'target':str(source),
            'original_sha256':digest(reference),'staged_sha256':digest(target),'staged':str(target),
            'old_bytes':len(reference.read_bytes()),'new_bytes':len(result),'hulls':1,'triangles':len(hull.faces),
            'ray_gap_m':{'p95':float(np.percentile(gap,95)),'max':max(gap)},'radius':float(radius),
            'centre_inertia_unchanged':surface[:24]==old[:24]})
    preview.save(stage/'outlines.png')
    # Use installed engine's real loader and IVP topology accessors, not just our serializer.
    probe=stage/'probe';probe.mkdir(exist_ok=True);compiler,env=compiler_env()
    env['INCLUDE']=str(ROOT/'src/include')+';'+env['INCLUDE']
    env['PATH']=str(GAME/'bin')+';'+env['PATH']
    args=[str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc','/D_ITERATOR_DEBUG_LEVEL=1',
          str(ROOT/'tools/train_sur/check.cpp'),'/Fecheck.exe','/link',str(OUT/'build/imports/Common.lib'),
          str(ROOT/'bin/DALib.lib'),str(ROOT/'bin/dacom.lib')]
    for name,cmd in [('build',args),('engine',[str(probe/'check.exe'),*[m['staged'] for m in report['models']]])]:
        result=subprocess.run(cmd,cwd=probe,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (stage/(name+'.log')).write_bytes(result.stdout)
        print(result.stdout.decode(errors='replace'));result.check_returncode()
    report['passed']=True;report['sources']={str(Path(__file__).relative_to(ROOT)):digest(Path(__file__)),
        'tools/train_sur/build.py':digest(ROOT/'tools/train_sur/build.py')}
    (stage/'checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['models'],indent=2))

if __name__=='__main__':main()
