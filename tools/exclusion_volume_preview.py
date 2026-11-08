"""Render Om15 palette references with the installed production D3D9 shaders.

Representative surrounding-cloud views, not game screenshots: no objects, hybrid sprites,
fullscreen retail fog or sky. Uses current walker settings and nebula colours.
"""
import ast
import io
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
from PIL import Image
from generate_station_lods import read_tree
from exclusion_palette_runtime import palette_sections

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/games/FL_MOD')
OUT = ROOT / 'src/obj/exclusion_volume'


def sections(text):
    return [(name, {k: v[-1] for k, v in values.items()}) for name, values in palette_sections(text)]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'tools/check_nebula_ice.cpp').read_text()
    source = source.replace('const int W=768,H=480;', 'const int W=384,H=240;')
    source = source.replace('std::string("DATA_EXTRA/SHADERS/")', 'std::string("D:/games/FL_MOD/DATA_EXTRA/SHADERS/")')
    source = source.replace('walker?"nebula_walker_ice.hlsl":"nebula_ice.hlsl"', '"nebula_volume.hlsl"')
    source = source.replace('"src/obj/tau37_ice_reference/white_circle_rgb.png"', '"src/obj/exclusion_volume/walker.png"')
    source = source.replace('walker?.46f:.58f', '.55f').replace('walker?.42f:.60f', '.35f')
    start = source.index('    const float quad[4][5]')
    source = source[:start] + '''
    FILE* input=fopen(argv[1],"rb"); if(!input)return 8;
    if(fread(c,sizeof(c),1,input)!=1)return 9; fclose(input);
    C(16,lo,inv,.5f,.4f); C(91,0,.8f,.2f,lo+.5f/inv);
''' + source[start:]
    start = source.index('    for(int frame=0;')
    end = source.index('        Check(d->SetTexture(1,vol))', start)
    source = source[:start] + '''    for(int frame=0;frame<6;++frame) {
        // Front/side/back key light, two spatial offsets. Stable samples for comparisons.
        const float z[3]={-.9f,0,.9f}; float kz=z[frame%3], ky=sqrtf(1-kz*kz);
        C(25,0,ky,kz,.7f); C(27,0,ky*1.3f,kz,.12f);
        C(92,0,ky/40000,kz/40000,1.f/(40000.f*40000.f));
        if(frame>=3){c[13][0]=.54f;c[14][0]=.98f;c[15][0]=.69f;}
''' + source[end:]
    source = source.replace('if(walker){cc[3][0]=1.1f;cc[3][3]=1;cc[18][1]=0;cc[23][3]=0;}',
                            'cc[3][0]=1.1f;cc[3][3]=1;cc[18][1]=0;cc[23][3]=0;')
    source = source.replace('for(int sky=0;sky<2;++sky)', 'for(int sky=0;sky<1;++sky)')
    start = source.index('        char path[160];')
    end = source.index('\n    }\n    return 0;', start)
    source = source[:start] + '''        char path[512];sprintf(path,"%s_%d.png",argv[2],frame);
        Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,back,nullptr,nullptr));
        printf("Rendered %s\\n",path);''' + source[end:]
    (OUT / 'preview.cpp').write_text(source)
    # Client's exact noise generator, as used by the existing GPU check.
    client = (ROOT / 'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
    noise = client[client.index('    unsigned int Hash(unsigned int X)'):client.index('    // Coverage (the fraction')]
    (OUT / 'nebula_noise_fixture.h').write_text('const unsigned long kNoiseSize=64;\nfloat Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}\n' + noise)
    # The included faceted header is unused but its relative include must resolve.
    source = (OUT / 'preview.cpp').read_text().replace('"../src/freelancer/Client/nebula_faceted_noise.h"',
                         '"D:/work/Freelancer-Decomp/src/freelancer/Client/nebula_faceted_noise.h"')
    (OUT / 'preview.cpp').write_text(source)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat')
    script = OUT / 'build.cmd'
    script.write_text(f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
        'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
        '/Isrc/RP9 /IC:/DXSDK_Jun10/Include src/obj/exclusion_volume/preview.cpp '
        '/Fosrc/obj/exclusion_volume/preview.obj /Fesrc/obj/exclusion_volume/preview.exe '
        '/link d3d9.lib C:/DXSDK_Jun10/Lib/x86/d3dx9.lib user32.lib\n')
    subprocess.run(['cmd', '/c', str(script)], cwd=ROOT, check=True)


def inputs():
    _, roots = read_tree((GAME / 'DATA/SOLAR/NEBULA/walker.txm').read_bytes())
    lib = next(n for n in roots[0].children if n.name.lower() == 'texture library')
    tex = next(n for n in lib.children if n.name.lower() == 'walker_clouds')
    leaf = next(n for n in tex.children if n.name.lower() in ('mip0', 'mips'))
    Image.open(io.BytesIO(leaf.blob)).save(OUT / 'walker.png')
    settings = sections((GAME / 'DATA_EXTRA/VOLUMETRIC/volumetric.ini').read_text())
    common = next(v for n, v in settings if n == 'nebula')
    style = next(v for n, v in settings if n == 'nebulastyle' and v.get('name') == 'walker')
    s = dict(common, **style)
    # Inside an exclusion the production volume is disabled: match the surrounding
    # clouds instead of inventing a volume pass inside the bubble.
    (OUT / 'settings.json').write_text(json.dumps({'settings': s, 'zone_radius': 40000,
        'exclusion': 'none; reference is the surrounding nebula', 'samples': 'two positions, three sun directions',
        'omitted': ['sky', 'hybrid sprites', 'retail fog overlay', 'objects', 'lightning']}, indent=2))
    tree = ast.parse((GAME / 'Assets/Pythonlancer/templates/nebula/om15_orange_nebula.py').read_bytes())
    cases = []
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef): continue
        template = next(ast.literal_eval(n.value) for n in cls.body if isinstance(n, ast.Assign) and n.targets[0].id == 'TEMPLATE')
        ini = dict(sections(template)); fog = ini['fog']; light = ini['nebulalight']; cloud = ini['clouds']
        c = [[0.] * 4 for _ in range(109)]
        def C(i, *v): c[i][:len(v)] = v
        def rgb(value): return [float(x) / 255 for x in value.split(',')]
        def val(k, default): return float(s.get(k, default))
        f = rgb(fog['color']); a = rgb(cloud['puff_colora']); b = rgb(cloud['puff_colorb'])
        ambient = rgb(light['ambient']); distance = float(fog['distance']); scale = distance * val('cloud_scale_fog_distances', 1.1)
        stretch = val('layer_stretch', 1.3); sigma = val('cloud_density',4)*val('density_scale',.8)/distance
        detail = float(cloud['puff_radius'])*val('detail_scale',6)
        scale = max(scale, 2*detail)
        C(0,1.00001,-1.00001,1); C(1,0,0,1,1); C(2,1,.625,.5/384,.5/240)
        C(3,1); C(4,0,1); C(5,0,0,1); C(7,1/40000); C(8,0,1/40000); C(9,0,0,1/40000)
        C(10,56,10000,1.4,1); C(11,-math.log(val('haze_transmittance_at_fog_distance',.18))*.8/distance,sigma,200)
        C(12,0,1,0,stretch-1); C(13,.31,.42,.17,1/(scale*4)); C(14,.6,.1,.4,1/(detail*8)); C(15,.23,.7,.5,1/(scale*2))
        C(17,scale*.95,120,1500,0); C(18,*[x/max(f)*.9 for x in f],1)
        C(19,*[x*.14 for x in f],1/200); C(20,*[x*.06 for x in f],.6)
        C(21,*[x*.7 for x in a],sigma*2*detail); C(22,*[x*.7 for x in b],1/1380)
        C(87,*[(y-x)*.7 for x,y in zip(a,b)])
        ao=.5*scale/stretch; C(23,*[x*.65 for x in ambient],sigma*ao); C(24,0,ao*stretch)
        # Rh05 starglow inner tint is resolved below from the installed stararch.
        stars = dict()
        for name, values in sections((GAME / 'DATA/SOLAR/stararch.ini').read_text()):
            if 'nickname' in values: stars[values['nickname'].lower()] = values
        glow = stars[stars['rh05_sun']['star_glow'].lower()]
        inner = [float(x) for x in glow['inner_color'].split(',')[:3]]
        burn=float(light['sun_burnthrough_intensity'])*.8
        C(26,*[(.5+.5*x/max(inner))*burn for x in inner],.2)
        C(28,.3,val('ms_extinction',.35),val('ms_phase',.5),val('ms_extinction',.35)**2)
        segment=scale/sum(1.6**i for i in range(4)); covered=0
        for i in range(4): C(29+i,covered+.5*segment,sigma*1.6*segment); covered+=segment; segment*=1.6
        C(35,0,0,0,1); C(36,192,120,2)
        C(77,10000,1/60000,.5,.7); C(78,1,4/240); C(79,600,16,64535); C(80,0,1/4000)
        C(88,1/.35,.05,.6,1); C(89,1.02,50,.005,1.1449); C(90,.3,.6,.1,3)
        for i in range(93,97): C(i,0,0,0,1e30)
        C(100,-1,-1,-1); C(103,.45,.7,1/400,1); C(104,0,0,.5,.5); C(105,.2,.4,.6,.55)
        C(106,1000,1/7000)
        path=OUT/f'{cls.name}.bin'; path.write_bytes(struct.pack('<436f',*(v for row in c for v in row)))
        cases.append((cls.name,path))
    return cases


if __name__ == '__main__':
    build()
    env=dict(os.environ, FREELANCER_SHADER_CACHE_DIR=str(OUT/'cache'))
    env['PATH']=str(ROOT/'bin')+os.pathsep+env.get('PATH','')
    for name,path in inputs():
        subprocess.run([str(OUT/'preview.exe'),str(path),str(OUT/(name+'_surrounding'))],cwd=ROOT,env=env,check=True)
