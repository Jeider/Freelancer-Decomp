"""Compare courier poses with Pythonlancer and native matrix/quaternion conversion."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PYTHONLANCER=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT=ROOT/'src/obj/train_courier/orientation'

if '--reference' in sys.argv:
    import importlib.util
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('story_math',PYTHONLANCER/'story/math.py')
    math=importlib.util.module_from_spec(spec);spec.loader.exec_module(math)
    catalog=json.loads((ROOT/'out/train_courier/catalog.json').read_text(encoding='utf-8'))
    yaws={0,90,-90,180,-180,360,-360}
    for base in catalog['bases'].values():
        for point in base['points']:
            x,y,z=point['rotation'];assert x==0 and z==0
            yaws.add(y)
    cases=[dict(yaw=y,matrix=math.euler_to_matrix(0,y,0),quaternion=math.euler_to_quat(0,y,0)) for y in sorted(yaws)]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'reference.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
    raise SystemExit(0)

subprocess.run([str(PYTHONLANCER/'.venv/Scripts/python.exe'),'-B',__file__,'--reference'],check=True)
cases=json.loads((OUT/'reference.json').read_text(encoding='utf-8'))
source=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
start=source.index('Matrix pointOrientation(');end=source.index('\n}',start)+2
function=source[start:end]
rows=[]
def number(x):return repr(float(x))+'f'
for case in cases:
    values=[case['yaw']]+[v for row in case['matrix'] for v in row]+case['quaternion']
    rows.append('{'+','.join(map(number,values))+'}')
cpp=r'''
#include "common_csys.h"
#include "DALib.h"
#include "x86math.h"
#include <cassert>
#include <cmath>
#include <cstdio>
'''+function+'\nfloat cases[][14]={'+','.join(rows)+r'''};
int main(){
    assert(DALib::Startup(nullptr,"check_dacom.ini"));
    struct {AGGDESC base;void* reserved;} desc{{12,"3DMathEngine"},nullptr};
    void* instance=nullptr;DACOM_Acquire()->CreateInstance(&desc.base,&instance);
    auto* math=static_cast<I3DMathEngine*>(instance);assert(math);
    for(auto const& c:cases){
        Matrix matrix=pointOrientation(c[0]);
        FQuaternion reference{c[10],c[11],c[12],c[13]},native;
        FMatrix fromReference,roundtrip;
        math->QuaternionToMatrix(fromReference,reference);
        math->MatrixToQuaternion(native,reinterpret_cast<FMatrix const&>(matrix));
        math->QuaternionToMatrix(roundtrip,native);
        for(int i=0;i<9;++i){
            float expected=c[i+1];
            assert(std::isfinite(matrix.E[i/3][i%3]));
            assert(std::abs(matrix.E[i/3][i%3]-expected)<2e-6f);
            assert(std::abs(fromReference.D[i/3][i%3]-expected)<2e-6f);
            assert(std::abs(roundtrip.D[i/3][i%3]-expected)<2e-6f);
        }
        // A horizontal train must always have world up +Y, never an inverted roll.
        assert(std::abs(roundtrip.D[0][1])<2e-6f && roundtrip.D[1][1]>.99999f && std::abs(roundtrip.D[2][1])<2e-6f);
    }
    printf("PASS: %zu yaw cases, all catalog headings match Pythonlancer matrices and WXYZ quaternions through native x86math; wagon up is +Y\n",sizeof(cases)/sizeof(*cases));
}
'''
(OUT/'check.cpp').write_text(cpp,encoding='utf-8')
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
compiler,env=compiler_env()
env['PATH']=str(ROOT/'bin')+';'+env['PATH']
shutil.copy2(ROOT/'src/obj/train_consist/check_dacom.ini',OUT/'check_dacom.ini')
subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/MD',
    '/D_ITERATOR_DEBUG_LEVEL=1','/I'+str(ROOT/'src/include'),str(OUT/'check.cpp'),
    '/Fecheck.exe','/Focheck.obj','/link','/LIBPATH:'+str(ROOT/'bin'),'DALib.lib','dacom.lib'],env=env,cwd=OUT,check=True)
subprocess.run([str(OUT/'check.exe')],env=env,cwd=OUT,check=True,timeout=60)
