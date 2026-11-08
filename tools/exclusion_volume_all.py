"""Read-only nebula inventory and production-shader comparison gallery.

Controlled GPU references, not screenshots: common 40km sphere, two noise offsets,
three light directions. Sky, geometry, retail fog and hybrid sprites are excluded.
Those omissions and disabled/missing inputs are recorded per case, never hidden.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import statistics
import struct
import subprocess
from types import SimpleNamespace
from PIL import Image, ImageChops, ImageDraw, ImageStat
from generate_station_lods import read_tree
from exclusion_palette_runtime import palette_sections

ROOT=Path(__file__).resolve().parents[1]
GAME=Path('D:/games/FL_MOD'); DATA=GAME/'DATA'; PY=GAME/'Assets/Pythonlancer'
OUT=ROOT/'src/obj/exclusion_volume_all'


def read(path):
    data=path.read_bytes()
    if data.startswith(b'BINI'): raise ValueError('Binary INI requires decoding')
    try:return data.decode('utf-8-sig').replace('\r\n','\n')
    except UnicodeDecodeError:return data.decode('cp1251').replace('\r\n','\n')


def sections(text):
    return [(n,{k:v[-1] for k,v in d.items()}) for n,d in palette_sections(text)]


def norm(text):
    return repr([(n,d) for n,d in palette_sections(text) if n!='exclusion zones'])


def path(base,relative):return base/relative.replace('\\','/')


def inventory():
    cases=[]; templates=[]; errors=[]
    for file in sorted((PY/'templates/nebula').glob('*.py')):
        for cls in ast.parse(file.read_bytes()).body:
            if not isinstance(cls,ast.ClassDef):continue
            attrs={}
            for node in cls.body:
                if isinstance(node,ast.Assign):
                    for name in node.targets:
                        if isinstance(name,ast.Name) and name.id in ('TEMPLATE','EXCLUSION_TINT_BY_SHELL','MATCH_EXCLUSION_PALETTE'):
                            attrs[name.id]=ast.literal_eval(node.value)
            if 'TEMPLATE' in attrs:templates.append({'class':cls.name,'source':str(file),'attrs':attrs,'used':[]})
    stars={d['nickname'].lower():d for n,d in sections(read(DATA/'SOLAR/stararch.ini')) if 'nickname' in d}
    refs={}
    for n,s in sections(read(DATA/'UNIVERSE/universe.ini')):
        if n!='system' or 'file' not in s:continue
        system=path(DATA/'UNIVERSE',s['file'])
        try:ss=sections(read(system))
        except (OSError,ValueError) as e:errors.append({'file':str(system),'error':str(e)});continue
        star=next((d['star'] for n,d in ss if n=='object' and 'star' in d),None)
        for n,d in ss:
            if n=='nebula' and 'file' in d:
                refs.setdefault(d['file'].lower(),[]).append({'system':s.get('nickname',system.stem),
                    'star':star,'volumetric':d.get('volumetric','true').lower() not in ('0','false'),
                    'zone':d.get('zone','')})
    # Include generated files that are currently unreferenced, with an explicit label.
    for file in (DATA/'SOLAR/NEBULA_MOD/GENERATED').glob('*.ini'):
        refs.setdefault(str(file.relative_to(DATA)).replace('/','\\').lower(),[])
    for relative,contexts in sorted(refs.items()):
        file=path(DATA,relative)
        try:text=read(file)
        except (OSError,ValueError) as e:errors.append({'file':str(file),'error':str(e)});continue
        matches=[t for t in templates if norm(t['attrs']['TEMPLATE'])==norm(text)]
        for t in matches:t['used'].append(relative)
        # Separate contexts if sunlight differs between systems.
        contexts=contexts or [{'system':'unreferenced','star':None,'volumetric':True}]
        unique={}
        for ctx in contexts:unique.setdefault((ctx['star'],ctx['volumetric']),ctx)
        for ctx in unique.values():
            cases.append({'source':str(file),'text':text,'basename':file.stem,'context':ctx,
                'template':matches[0]['class'] if matches else None,
                'attrs':matches[0]['attrs'] if matches else {},'kind':'installed'})
    for t in templates:
        if t['used']:continue
        # Templates not matching the installed output get their own rows, not silently dropped.
        cases.append({'source':t['source'],'text':t['attrs']['TEMPLATE'],
            'basename':t['class'],'context':{'system':'template only','star':None,'volumetric':True},
            'template':t['class'],'attrs':t['attrs'],'kind':'template'})
    (OUT/'inventory_errors.json').write_text(json.dumps(errors,indent=2))
    return cases,templates,stars


def defaults():
    src=read(ROOT/'src/freelancer/Client/nebula_volume.cpp')
    block=src[src.index('FNebulaVolumeSettings DefaultSettings()'):src.index('struct FRegisteredNebula')]
    values=dict(re.findall(r'S\.(\w+)\s*=\s*(-?[\d.]+)f?;',block))
    keys=dict(re.findall(r'\{"([a-z_]+)", &FNebulaVolumeSettings::(\w+)\}',src))
    out={k:values[v] for k,v in keys.items() if v in values}
    out.update(key_light_dir='0.3, 0.8, 0.5',key_light_colour='0, 0, 0',fog_colour='-1, -1, -1')
    return out


def style_for(text):
    fallback=''
    for section,values in palette_sections(text):
        for key,items in values.items():
            if (section=='clouds' and key=='puff_shape') or (section=='texturepanels' and key=='file' and not fallback):
                for item in items:
                    base=item.replace('\\','/').split('/')[-1].lower()
                    for family in ('crow','edge','walker','generic'):
                        if base.startswith(family+'_'):
                            if section=='clouds':return family
                            fallback=family
    return fallback


def texture(file,name):
    _,roots=read_tree(file.read_bytes())
    lib=next(n for n in roots[0].children if n.name.lower()=='texture library')
    tex=next(n for n in lib.children if n.name.lower()==name.lower())
    leaf=next(n for n in tex.children if n.name.lower() in ('mip0','mips'))
    return Image.open(io.BytesIO(leaf.blob)).convert('RGBA')


def shape_texture(text,shape):
    for section,values in palette_sections(text):
        if section!='texturepanels':continue
        for panel in values.get('file',[]):
            f=tex=current=None
            for raw in read(path(DATA,panel)).splitlines():
                line=raw.split(';',1)[0].strip()
                if '=' not in line:continue
                k,v=(x.strip() for x in line.split('=',1))
                if k=='file':f=v
                elif k=='texture_name':tex=v
                elif k=='shape_name':current=v
                elif k=='dim' and current==shape:
                    return texture(path(DATA,f),tex),[float(x) for x in v.split(',')]
    raise ValueError('Texture shape not resolved: '+str(shape))


def build():
    source=read(ROOT/'tools/check_nebula_ice.cpp')
    source=source.replace('const int W=768,H=480;','const int W=384,H=240;')
    source=source.replace('const bool walker=argc>1 && !strcmp(argv[1],"--walker");',
        'const bool walker=!strcmp(argv[3],"nebula_walker_ice.hlsl");')
    source=source.replace('std::string("DATA_EXTRA/SHADERS/")','std::string("D:/games/FL_MOD/DATA_EXTRA/SHADERS/")')
    source=source.replace('"nebula_walker_ice.hlsl","nebula_composite.hlsl"','"nebula_walker_ice.hlsl","nebula_edge_fibre.hlsl","nebula_alien.hlsl","nebula_composite.hlsl"')
    source=source.replace('walker?"nebula_walker_ice.hlsl":"nebula_ice.hlsl"','argv[3]')
    source=source.replace('"src/obj/tau37_ice_reference/white_circle_rgb.png"','argv[4]')
    source=source.replace('"../src/freelancer/Client/nebula_faceted_noise.h"','"D:/work/Freelancer-Decomp/src/freelancer/Client/nebula_faceted_noise.h"')
    a=source.index('    float c[109][4]');b=source.index('    const float quad[4][5]',a)
    source=source[:a]+'''
    float c[112][4]={}, tone[4]={};
    auto C=[&](int i,float x=0,float y=0,float z=0,float w=0){c[i][0]=x;c[i][1]=y;c[i][2]=z;c[i][3]=w;};
    FILE* input=fopen(argv[1],"rb");if(!input)return 8;
    if(fread(c,sizeof(c),1,input)!=1 || fread(tone,sizeof(tone),1,input)!=1)return 9;fclose(input);
    // Coverage remap uses the exact production noise histogram (faceted where selected).
    double above=0;int low=0,high=255;bool got=false;
    float coverage=c[16][0],softness=c[16][1];
    double count=walker?128.*128*128:noise.size();
    for(int b=255;b>=0;--b){above+=hist[b];if(!got&&above>=coverage*(1-softness)*count){high=b;got=true;}
        if(above>=coverage*count){low=b;break;}}
    float lo=coverage>0?low/255.f:1000.f,inv=1.f/std::max((high-low)/255.f,.01f);
    c[16][0]=lo;c[16][1]=inv;c[91][3]=lo+.5f/inv;
    const float initialG=c[25][3],stretch=c[12][3]+1,backWeight=c[27][3];
''' +source[b:]
    a=source.index('    for(int frame=0;');b=source.index('        Check(d->SetTexture(1,vol))',a)
    source=source[:a]+'''    for(int frame=0;frame<6;++frame) {
        const float z[3]={-.9f,0,.9f};float kz=z[frame%3],ky=sqrtf(1-kz*kz);
        C(25,0,ky,kz,initialG);C(27,0,ky*stretch,kz,backWeight);
        C(92,0,ky/40000,kz/40000,1.f/(40000.f*40000.f));
        if(frame>=3){c[13][0]=.54f;c[14][0]=.98f;c[15][0]=.69f;}
''' +source[b:]
    source=source.replace(',&c[0][0],109)',',&c[0][0],112)')
    source=source.replace('if(walker){cc[3][0]=1.1f;cc[3][3]=1;cc[18][1]=0;cc[23][3]=0;}',
        'memcpy(cc[3],tone,16);cc[18][1]=0;cc[23][3]=0;')
    source=source.replace('for(int sky=0;sky<2;++sky)','for(int sky=0;sky<1;++sky)')
    a=source.index('        char path[160];');b=source.index('\n    }\n    return 0;',a)
    source=source[:a]+'''        char path[512];sprintf(path,"%s_%d.png",argv[2],frame);
        Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,back,nullptr,nullptr));
''' +source[b:]
    (OUT/'preview.cpp').write_text(source)
    client=read(ROOT/'src/freelancer/Client/nebula_volume.cpp')
    noise=client[client.index('    unsigned int Hash(unsigned int X)'):client.index('    // Coverage (the fraction')]
    (OUT/'nebula_noise_fixture.h').write_text('const unsigned long kNoiseSize=64;\nfloat Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}\n'+noise)
    script=OUT/'build.cmd';vc='C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat'
    script.write_text(f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
        'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /IC:/DXSDK_Jun10/Include '
        'src/obj/exclusion_volume_all/preview.cpp /Fosrc/obj/exclusion_volume_all/preview.obj '
        '/Fesrc/obj/exclusion_volume_all/preview.exe /link d3d9.lib C:/DXSDK_Jun10/Lib/x86/d3dx9.lib user32.lib\n')
    subprocess.run(['cmd','/c',str(script)],cwd=ROOT,check=True)


def constants(case,common,styles,overrides,stars):
    ini=sections(case['text']);fog=next((v for n,v in ini if n=='fog'),{})
    light=next((v for n,v in ini if n=='nebulalight'),{})
    cloud=next((v for n,v in ini if n=='clouds'),{})
    override=overrides.get(case['basename'].lower(),{})
    family=override.get('style',style_for(case['text']))
    s={**common,**styles.get(family,{}),**override}
    case['style']=family or 'default';case['settings']=s;case['notes']=[]
    if not case['context']['volumetric'] or float(s.get('enabled',1))==0:
        case['status']='volume disabled';return
    if not fog:case['status']='no fog section';return
    def v(k,d=0):return float(s.get(k,d))
    def rgb(x):return [float(a)/255 for a in x.split(',')]
    f=rgb(fog.get('color','0,0,0')); custom=[float(x) for x in s['fog_colour'].split(',')]
    if min(custom)>=0:f=custom
    a=rgb(cloud.get('puff_colora',','.join(str(min(255,x*510)) for x in f)))
    b=rgb(cloud.get('puff_colorb',','.join(str(x*255) for x in a)))
    ambient=rgb(light.get('ambient','0,0,0'))
    dist=max(1,float(fog.get('distance',3000)));near=max(0,float(fog.get('near',0)))
    density=v('density_scale',1);sigma=v('cloud_density',6)*density/dist
    haze=-math.log(max(.0001,min(.9999,v('haze_transmittance_at_fog_distance',.5))))*density/dist
    radius=float(cloud.get('puff_radius',100));detail=radius*max(.05,v('detail_scale',4))
    scale=v('cloud_scale_m') or max(2*detail,min(10000,dist*v('cloud_scale_fog_distances',2.5)))
    stretch=max(.05,v('layer_stretch',1.6))
    cap=v('max_march_distance')
    if cap<=0:cap=near+min(dist*30,max(dist,-math.log(v('march_end_transmittance',.02))/max(haze,1e-9)))
    fade=[float(x) for x in cloud.get('near_fade_distance','0,1').split(',')]
    fa=v('cloud_near_fade_start',-1);fb=v('cloud_near_fade_end',-1)
    if fa<0:fa=fade[0]*v('cloud_near_fade_scale',1)
    if fb<=fa:fb=max(fa+1,fade[-1]*v('cloud_near_fade_scale',1))
    mode='nebula_walker_ice.hlsl' if v('faceted_clouds')>.5 else 'nebula_edge_fibre.hlsl' if v('fibre_clouds')>.5 else 'nebula_alien.hlsl' if v('alien_veins')>0 else 'nebula_ice.hlsl' if v('ice_crystal')>.5 else 'nebula_volume.hlsl'
    case['shader']=mode
    c=[[0.]*4 for _ in range(112)]
    def C(i,*values):c[i][:len(values)]=values
    C(0,1.00001,-1.00001,1);C(1,0,0,1,1);C(2,1,.625,.5/384,.5/240)
    C(3,1);C(4,0,1);C(5,0,0,1);C(7,1/40000);C(8,0,1/40000);C(9,0,0,1/40000)
    C(10,v('step_count',96),cap,v('step_distribution',1.5),v('jitter',1));C(11,haze,sigma,near)
    C(12,0,1,0,stretch-1);C(13,.31,.42,.17,1/(scale*4));C(14,.6,.1,.4,1/(detail*8));C(15,.23,.7,.5,1/(scale*2))
    C(16,v('coverage',.4),v('cloud_softness',.6),v('erosion',.5),v('wispiness',.35))
    C(17,scale*v('warp',.3),fa,fb,v('haze_tail',1))
    C(18,*[x/max(max(f),1e-4)*v('haze_albedo',.15) for x in f],float(v('cloud_near_fade_start',-1)>=0))
    C(19,*[x*v('haze_emission',.6) for x in f],1/near if near else 0)
    C(20,*[x*v('emission',.25) for x in f],v('powder_strength',.6))
    if v('ice_crystal')>.5:
        a=[.09,.18,.26];b=[.38,.57,.62];C(20,*[x*v('emission') for x in (.32,.65,.72)],v('powder_strength'))
    C(21,*[x*v('cloud_brightness',1) for x in a],sigma*2*detail)
    C(22,*[x*v('cloud_brightness',1) for x in b],1/max(1,fb-fa));C(87,*[(y-x)*v('cloud_brightness',1) for x,y in zip(a,b)])
    ao=v('ao_distance') or .5*scale/stretch
    C(23,*[x*v('ambient_scale',1.5) for x in ambient],sigma*ao*v('ao_strength',1));C(24,0,ao*stretch)
    burn=float(light.get('sun_burnthrough_intensity',0));star=case['context']['star'];key=None
    if star and burn>0 and v('key_light_source')<.5:
        st=stars.get(star.lower(),{});glow=stars.get(st.get('star_glow','').lower(),{})
        if 'inner_color' in glow:
            inner=[float(x) for x in glow['inner_color'].split(',')[:3]]
            key=[(.5+.5*x/max(max(inner),1e-9))*burn*v('key_light_intensity',3) for x in inner]
    if key is None:
        colour=[float(x) for x in s['key_light_colour'].split(',')]
        if sum(colour)<=0:colour=[.5+.5*x/max(max(a),1e-9) for x in a]
        key=[x*v('key_light_fixed_intensity',1.5) for x in colour]
        if not star and v('key_light_source')<.5:case['notes'].append('No system sun context: fixed-light fallback; not a calibrated in-game brightness')
    case['key_rgb']=key
    C(25,0,1,0,v('phase_g',.6));C(26,*key,v('phase_back_g',.3));C(27,0,stretch,0,v('phase_back_weight',.2))
    C(28,v('ms_strength',.5),v('ms_extinction',.35),v('ms_phase',.5),v('ms_extinction',.35)**2)
    steps=max(0,min(6,round(v('shadow_steps',6))));distance=v('shadow_distance') or scale
    segment=distance/sum(1.6**i for i in range(steps)) if steps else 0;covered=0;pair=[]
    for i in range(steps):
        C(29+i,covered+.5*segment,sigma*v('shadow_density',1)*segment)
        pair.append((covered,segment));covered+=segment;segment*=1.6
        if i%2==1:
            length=sum(p[1] for p in pair);C(81+i//2,pair[0][0]+length*.5,sigma*v('shadow_density',1)*length);pair=[]
    C(35,0,0,0,1);C(36,192,120,v('tonemap_white',2));C(77,10000,1/60000,.5,.7);C(78,1,4/240)
    C(79,800,16,64535);C(80,0,1/v('cloud_distance_fade') if v('cloud_distance_fade')>1 else 0)
    width=max(.001,v('shell_width',.35));amp=v('shell_noise',.05);extent=max(.001,v('halo_extent',.02))
    C(88,1/width,amp,1-width-amp,v('shell_cloud_falloff',1));C(89,1+extent,1/extent,v('halo_density',.005),(1+extent+amp)**2)
    C(90,.3,.6,.1,v('shell_noise_scale',.1));C(91,0,v('far_cloud_softening',.8),v('far_detail_fade',.2))
    for i in range(93,97):C(i,0,0,0,1e30)
    C(100,-1,-1,-1)
    shape=next((d['puff_shape'][0] for n,d in palette_sections(case['text']) if n=='clouds' and 'puff_shape' in d),None)
    if v('ice_crystal')>.5:shape='white_circle'
    if shape:
        im,uv=shape_texture(case['text'],shape);C(103,v('puff_texture_density'),v('puff_texture_colour'),1/max(1,radius*v('puff_texture_scale',8)),1);C(104,*uv)
    else:im=Image.new('RGBA',(1,1),'white')
    texture_path=OUT/'textures'/f'{case["id"]}.png';im.save(texture_path);case['texture']=str(texture_path)
    C(105,.2,.4,.6,v('cloud_billow'));C(106,v('fog_ramp_start'),1/v('fog_ramp_distance') if v('fog_ramp_distance')>1 else 0)
    C(107,v('vein_emission'),v('vein_pulse'),0)
    if v('alien_veins')>0:
        C(109,*[float(x) for x in s.get('alien_vein_colour','.3,.9,1').split(',')],v('alien_veins'))
        C(110,1/max(10,v('alien_vein_scale_m',1500)),v('alien_vein_sharpness',6),v('alien_vein_stretch',.85))
        C(111,v('alien_vein_density',1))
    tone=[v('exposure',1),v('tonemap',2),v('tonemap_white',2),v('upsample_blur',1)]
    (OUT/'inputs'/f'{case["id"]}.bin').write_bytes(struct.pack('<452f',*(x for row in c for x in row),*tone))
    if v('hybrid_clouds')>.5 or v('replace_clouds',1)<.5:case['notes'].append('Hybrid/retail cloud sprites are active in game and omitted here')
    if v('replace_fog_overlay',1)<.5:case['notes'].append('Retail fog overlay omitted')
    case['status']='ready'


def prepare():
    for folder in ('textures','inputs','renders','comparisons'): (OUT/folder).mkdir(parents=True,exist_ok=True)
    cases,templates,stars=inventory()
    configs=sections(read(GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini'))
    common={**defaults(),**next(v for n,v in configs if n=='nebula')}
    styles={v['name']:v for n,v in configs if n=='nebulastyle'}
    overrides={v['file'].lower():v for n,v in configs if n=='nebulaoverride'}
    for i,case in enumerate(cases):
        case['id']=f'{i+1:03d}_{case["basename"]}'
        try:constants(case,common,styles,overrides,stars)
        except Exception as e:case['status']='input error';case['error']=str(e)
    (OUT/'cases.json').write_text(json.dumps(cases,indent=2))
    (OUT/'templates.json').write_text(json.dumps(templates,indent=2))
    print(json.dumps({'cases':len(cases),'templates':len(templates),'status':{s:sum(c['status']==s for c in cases) for s in {c['status'] for c in cases}}}))


def render():
    build();cases=json.loads((OUT/'cases.json').read_text())
    env=dict(os.environ,FREELANCER_SHADER_CACHE_DIR=str(OUT/'cache'));env['PATH']=str(ROOT/'bin')+os.pathsep+env.get('PATH','')
    for i,c in enumerate(cases):
        if c['status'] not in ('ready','rendered'):continue
        prefix=OUT/'renders'/c['id']
        if all(Path(str(prefix)+f'_{j}.png').exists() for j in range(6)):c['status']='rendered';continue
        p=subprocess.run([str(OUT/'preview.exe'),str(OUT/'inputs'/f'{c["id"]}.bin'),str(prefix),c['shader'],c['texture']],cwd=ROOT,env=env,capture_output=True,text=True)
        (OUT/'renders'/f'{c["id"]}.log').write_text(p.stdout+'\n'+p.stderr)
        c['status']='rendered' if p.returncode==0 else 'render error'
        print(f'{i+1}/{len(cases)} {c["basename"]}: {c["status"]}',flush=True)
        (OUT/'cases.json').write_text(json.dumps(cases,indent=2))
    (OUT/'cases.json').write_text(json.dumps(cases,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('prepare','render'))
    {'prepare':prepare,'render':render}[parser.parse_args().action]()
