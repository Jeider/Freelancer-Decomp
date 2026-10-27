"""Interpreted math/source checks only. Never invokes a compiler or graphics API.

Independent acceptance targets: conserved null-geodesic energy, analytic photon
sphere/capture boundary, weak deflection, step convergence, preset/include validity.
This is not evidence that the HLSL compiles or that its GPU images look correct.
"""
from pathlib import Path
import ast
import json
import math
import re

ROOT=Path(__file__).resolve().parents[2]
SHADERS=ROOT/'DATA_EXTRA/SHADERS/ANOMALIES'

def trace(impact,observer=30.0,step=.0125,budget=1024):
    sine=impact*math.sqrt(1-1/observer)/observer
    assert 0<sine<1
    u=1/observer;w=math.sqrt(1-sine*sine)/impact;phi=0
    initial=w*w+u*u-u*u*u;worst=0
    def rhs(u,w):return w,-u+1.5*u*u
    for count in range(budget):
        a=rhs(u,w);b=rhs(u+a[0]*step/2,w+a[1]*step/2)
        c=rhs(u+b[0]*step/2,w+b[1]*step/2);d=rhs(u+c[0]*step,w+c[1]*step)
        un=u+step*(a[0]+2*b[0]+2*c[0]+d[0])/6
        wn=w+step*(a[1]+2*b[1]+2*c[1]+d[1])/6
        worst=max(worst,abs(wn*wn+un*un-un*un*un-initial))
        if un<=.00001:
            phi+=step*u/(u-un)
            return 'escape',phi-(math.pi-math.asin(sine)),worst,count+1
        if un>=1:return 'capture',0,worst,count+1
        phi+=step;u,w=un,wn
    return 'unresolved',0,worst,budget

def main():
    critical=3*math.sqrt(3)/2
    assert abs(-2/3+1.5*(2/3)**2)<1e-14
    lower=trace(critical*(1-1e-4));upper=trace(critical*(1+1e-4))
    assert lower[0]=='capture' and upper[0]=='escape',(lower,upper)
    # Weak-field result 4M/b = 2/b; at b=100 r_s the next-order correction is small.
    weak=trace(100,observer=10000)
    assert weak[0]=='escape' and abs(weak[1]/.02-1)<.025,weak
    coarse=trace(3.2);fine=trace(3.2,step=.00625,budget=2048)
    assert coarse[0]==fine[0]=='escape'
    assert abs(coarse[1]-fine[1])<2e-6,(coarse,fine)
    assert max(lower[2],upper[2],weak[2],coarse[2])<1e-7
    presets=json.loads((ROOT/'tools/space_anomalies/presets.realistic.json').read_text(encoding='utf8'))
    assert len(presets)==8 and len({p['id'] for p in presets})==8
    for p in presets:
        assert (SHADERS/p['shader']).is_file()
        assert all(math.isfinite(p[k]) for k in ['time','inclination','yaw','exposure','distance','flare','sensor'])
        assert p['distance']>1 and p['exposure']>0 and 0<=p['sensor']<=1
    for path in SHADERS.glob('realism*'):
        source=path.read_text(encoding='utf8')
        for inc in re.findall(r'#include\s+"([^"]+)"',source):assert (path.parent/inc).is_file(),inc
        clean=re.sub(r'//[^\n]*|/\*.*?\*/','',source,flags=re.S)
        for a,b in [('(',')'),('{','}'),('[',']')]:assert clean.count(a)==clean.count(b),str(path)
        assert not re.search(r'\b(?:float\d?|int)\s+(?:texture|pass|sample)\b',clean),str(path)
    for filename in ['build.py','report_realistic.py','check_realism.py']:
        ast.parse((ROOT/'tools/space_anomalies'/filename).read_text(encoding='utf8'))
    result={'scope':'CPU double-precision math and static source checks only; no compilation or GPU validation',
            'photon_sphere_rs':1.5,'critical_impact_rs':critical,'near_critical_inside':lower,'near_critical_outside':upper,
            'weak_deflection_b100':weak,'rk4_coarse':coarse,'rk4_fine':fine,'presets':len(presets),'status':'PASS'}
    out=ROOT/'src/obj/space_anomalies/realistic';out.mkdir(parents=True,exist_ok=True)
    (out/'math_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
