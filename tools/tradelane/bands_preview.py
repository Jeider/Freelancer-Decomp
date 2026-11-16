"""Offline large-band art studies. Never installs or writes into the game tree."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
mix='--mix' in sys.argv
OUT=ROOT/('out/tradelane_mix' if mix else 'out/tradelane_bands')
OUT.mkdir(parents=True,exist_ok=True)
GAME=Path('D:/Games/FL_MOD')
SHADER=GAME/'DATA_EXTRA/SHADERS/tradelane_corridor.hlsl'
# Protect the installed effect and active binaries/config against accidental changes.
protected=[SHADER]+[GAME/'bin'/p for p in ('freelancer.exe','RP9.dll','port.ini')]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):digest(p) for p in protected}
base=SHADER.read_text()
variants=[('current','Текущий эффект',0),('ribbons','A · Широкие ленты',1),
          ('sheets','B · Крупные мягкие полосы',2),('segments','C · Длинные прерывистые полосы',3)]
if mix:variants=[('sheets','Sheets · исходный вариант',2),('mix','Микс · sheets + кольца + вращение',4)]
function=r'''
// Offline study: large longitudinal bands. World-depth clipping and transitions
// remain the same as the installed corridor. Camera never rolls.
float PreviewBand(float3 P,float4 F)
{
    float Angle=atan2(P.y,P.x);
    float Drift=sin(-P.z*.00065+Travel.y*.42)*.75+(F.w)*1.2;
    #if BAND_MODE == 4
    // Screen Y is inverted: increasing the sampled angle moves the material
    // clockwise on screen. Sixteen degrees/second; the camera stays fixed.
    Angle+=Travel.y*.279252680;
    Drift=sin(-P.z*.00065)*.75+F.w*.7;
    #endif
    float Wave=.5+.5*cos(Angle*BAND_COUNT+Drift);
    float Band=smoothstep(BAND_LOW,BAND_HIGH,Wave);
    float Modulation=(.62+.38*sin(-P.z*.002+Travel.x*3.2+Angle*2.0))*(.35+.65*smoothstep(.22,.70,F.y));
    #if BAND_MODE == 3
    float Packet=.5+.5*cos((-P.z/1700.0+Travel.x*1600.0/1700.0)*6.28318530718+sin(Angle*5)*2.0);
    Band*=smoothstep(.23,.55,Packet);
    #endif
    return Band*Modulation;
}
float PreviewDonut(float3 P,float4 F)
{
    // Rings are integrated separately: sparse radial volume slices otherwise
    // split one distant torus into several thin concentric aliases.
    return 0;
}
float3 PreviewRings(float3 Ray,float SceneRay)
{
    float3 Color=0;
    #if BAND_MODE == 4
    if(Ray.z>=-.01)return 0;
    float Slope=length(Ray.xy)/(-Ray.z);
    // Keep 2880 m/s in the preview; double spacing halves frequency to .8/s.
    float Phase=frac(Travel.x*1600.0*2.0/3600.0+.3);
    [loop]for(int Ring=0;Ring<6;++Ring){
        float Forward=(Ring+1-Phase)*3600.0;
        float Distance=Forward/(-Ray.z);
        float Visibility=smoothstep(60.0,240.0,Forward)*(1-smoothstep(6000.0,9400.0,Forward))*smoothstep(0.0,120.0,SceneRay-Distance);
        if(Visibility<=0)continue;
        float3 P=Ray*Distance;
        float4 F=SampleFlow(FlowPosition(P));
        float Angle=atan2(P.y,P.x);
        float Radius=340.0+sin(Angle*9.0)*4.0+F.w*10.0;
        // Triple the torus cross-section, retaining its radius and material.
        float Width=3.0*sqrt(65.0*65.0+130.0*130.0*Slope*Slope);
        float Section=(length(P.xy)-Radius)/Width;
        float Body=1-smoothstep(.35,1.25,abs(Section));
        // Thin broken ribbons replace the solid torus. The same membrane/vein
        // noise as the original corridor lends them an irregular filament edge.
        float Membrane=pow(saturate(1-abs(F.x-.515)*22),3);
        float Veins=pow(saturate(1-abs(F.y-.52)*15),5)*Membrane;
        float Wave=.5+.5*sin(Section*20+F.w*24+sin(Angle*11+F.y*8)*2.5);
        float Strands=smoothstep(.72,.94,Wave)*smoothstep(.38,.60,F.z);
        // Filter subpixel ribbons toward mean coverage instead of sparkling.
        float PixelPhase=Forward*1.1547005*Warp.y/Width*20;
        Strands=lerp(.16,Strands,1-smoothstep(.7,2.4,PixelPhase));
        float Filaments=saturate(Strands+Veins*.35);
        float3 Tint=lerp(float3(.10,.38,.55),float3(.65,.92,1.0),saturate(Veins*.65+Strands*.3));
        Color+=Tint*Body*Filaments*Visibility*1.15*.5;
    }
    #endif
    return Color;
}
'''
for name,title,mode in variants:
    folder=OUT/name;folder.mkdir(exist_ok=True)
    source=base
    if mode:
        count,low,high={1:(9,.38,.67),2:(5,.20,.65),3:(8,.42,.72),4:(5,.20,.65)}[mode]
        prefix=f'#define BAND_MODE {mode}\n#define BAND_COUNT {count}.0\n#define BAND_LOW {low}\n#define BAND_HIGH {high}\n'
        source=prefix+source.replace('float4 PSMain(Interp In, float2 Pixel:VPOS):COLOR0',function+'\nfloat4 PSMain(Interp In, float2 Pixel:VPOS):COLOR0',1)
        marker='        float Alpha = 1.0 - exp2(-Density * min(27.0 / Transverse, 150.0) * 0.012);'
        assert source.count(marker)==1
        source=source.replace(marker,'''        float Band=PreviewBand(P,F);
        float Donut=PreviewDonut(P,F);
        Density=Density*.12+(Band*(.65+.35*F.x)+Donut*.95)*Shell*Far*smoothstep(0.0,120.0,Remaining);
'''+marker)
        marker='        Color *= 1.35;'
        assert source.count(marker)==1
        source=source.replace(marker,'''        // Broad luminous bodies take precedence over the former fine filaments.
        float3 BandColor=lerp(float3(.015,.13,.25),float3(.16,.48,.62),saturate(.35+F.x*.65));
        Color=Color*.30+BandColor*Band*(.65+Lighting*.7);
        Color+=BandColor*Donut*(1.25+Lighting*.8);
'''+marker)
        source=source.replace('    float3 Volume = Accumulated;', '    Accumulated+=PreviewRings(Ray,SceneRay);\n    float3 Volume = Accumulated;',1)
    (folder/'corridor.hlsl').write_text(source)

vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK_Jun10/Include')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]+[Path('C:/DXSDK_Jun10/Lib/x86')]))
exe=OUT/'bands_preview.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/D_CRT_SECURE_NO_WARNINGS',str(ROOT/'tools/tradelane/bands_preview.cpp'),'/Fe'+str(exe),'/link','d3d9.lib','d3dx9.lib','user32.lib'],cwd=OUT,env=env,check=True)
ffmpeg='C:/ffmpeg/bin/ffmpeg.exe'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
sheet=Image.new('RGB',(1920,590*((len(variants)+1)//2)),(10,14,22));draw=ImageDraw.Draw(sheet)
for i,(name,title,mode) in enumerate(variants):
    folder=OUT/name;args=[str(exe),str(folder/'corridor.hlsl'),str(folder)+os.sep]
    subprocess.run([*args,'still'],cwd=ROOT,check=True)
    x=(i%2)*960;y=(i//2)*590
    sheet.paste(Image.open(folder/'preview.png').convert('RGB'),(x,y+50))
    draw.text((x+18,y+12),title,font=font,fill='white')
    label=Image.new('RGB',(960,50),(10,14,22));ImageDraw.Draw(label).text((18,12),title,font=font,fill='white');label.save(folder/'label.png')
    if '--stills-only' in sys.argv:continue
    with (folder/'render.log').open('w') as log:
        renderer=subprocess.Popen([*args,'video'],cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
        try:
            subprocess.run([ffmpeg,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','bgra','-video_size','960x540','-framerate','60','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(folder/(name+'.mp4'))],stdin=renderer.stdout,check=True)
        finally:
            renderer.stdout.close();code=renderer.wait()
        if code:raise RuntimeError(f'{name} renderer exit {code}')
    print('Rendered',name,flush=True)
sheet.save(OUT/'comparison.png')
if '--stills-only' not in sys.argv:
    args=[ffmpeg,'-y','-hide_banner','-loglevel','error']
    for name,_,_ in variants:args+=['-i',str(OUT/name/(name+'.mp4'))]
    for name,_,_ in variants:args+=['-i',str(OUT/name/'label.png')]
    count=len(variants)
    graph=';'.join(f'[{i+count}:v][{i}:v]vstack=inputs=2[t{i}]' for i in range(count))
    graph+=(';[t0][t1]hstack=inputs=2[v]' if mix else ';[t0][t1][t2][t3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]')
    subprocess.run(args+['-filter_complex',graph,'-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'comparison.mp4')],check=True)
after={str(p):digest(p) for p in protected}
if before!=after:raise RuntimeError('Protected game files changed during preview; investigate before claiming unchanged')
(OUT/'manifest.json').write_text(json.dumps({'scope':'Offline GPU art previews on a synthetic starfield. Not game footage; no game installation.','game_files_before':before,'game_files_after':after,'variants':[v[0] for v in variants],'seconds':8,'fps':60,'size':[960,540],'mix_rotation_degrees_per_second':16 if mix else 0,'mix_ring_speed_multiplier':2 if mix else None,'mix_ring_spacing_metres':3600 if mix else None,'mix_ring_passages_per_second':.8 if mix else None,'ring_width_multiplier':3 if mix else None,'ring_emission_multiplier':.5 if mix else None,'ring_material':'thin broken ribbons with original corridor membrane/vein noise' if mix else None},indent=2))
print(OUT/'comparison.png')
if '--stills-only' not in sys.argv:print(OUT/'comparison.mp4')
