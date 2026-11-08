"""Build PNG/PDF comparisons and a machine-readable audit from all GPU references."""
import io
import json
from pathlib import Path
import re
import statistics
import csv
from types import SimpleNamespace
from PIL import Image, ImageChops, ImageDraw, ImageStat
from generate_station_lods import read_tree
from exclusion_volume_all import OUT,DATA,PY,path,palette_sections,texture


def exclusions(text):
    entries=[]
    for section,values in palette_sections(text):
        if section!='exclusion zones':continue
        # Recover ordering between repeated entries from the original INI block.
    for block in re.findall(r'(?ims)^\[exclusion zones\](.*?)(?=^\[|\Z)',text):
        for raw in re.split(r'(?im)^exclusion\s*=',block)[1:]:
            d={}
            for line in raw.splitlines()[1:]:
                line=line.split(';',1)[0].strip()
                if '=' in line:
                    k,v=line.split('=',1);d[k.strip().lower()]=v.strip()
            if d.get('zone_shell'):entries.append(d)
    return list({(e['zone_shell'].lower(),e.get('exclusion_tint','255, 255, 255')):e for e in entries}.values())


def main():
    cases=json.loads((OUT/'cases.json').read_text());cache={};rows=[];report=[]
    ns={};exec(compile((PY/'templates/nebula/exclusion.py').read_bytes(),'exclusion.py','exec'),ns)
    stats={'protected':0,'no_shell':0,'rendered':0,'bright_shell':0,'dark_shell':0}
    W,H=1216,310
    def get_shell(relative):
        if relative not in cache:
            _,roots=read_tree(path(DATA,relative).read_bytes())
            lib=next(n for n in roots[0].children if n.name.lower()=='texture library')
            images=[];means=[]
            for tex in lib.children:
                leaf=next(n for n in tex.children if n.name.lower() in ('mip0','mips'))
                im=Image.open(io.BytesIO(leaf.blob)).convert('RGBA')
                means.append(ImageStat.Stat(im.convert('RGB'),im.getchannel('A')).mean)
                images.append(im)
            mean=[sum(m[c] for m in means)/len(means) for c in range(3)]
            cache[relative]=(images[0].convert('RGB').resize((296,210)),mean)
        return cache[relative]
    for case in cases:
        if case['status']!='rendered':
            raise RuntimeError(f'Incomplete rendering: {case["id"]}: {case["status"]}')
        stats['rendered']+=1
        prefix=OUT/'renders'/case['id'];colours=[]
        for i in range(6):
            im=Image.open(str(prefix)+f'_{i}.png').convert('RGB')
            pixels=sorted(im.get_flattened_data(),key=lambda p:.2126*p[0]+.7152*p[1]+.0722*p[2])
            mid=pixels[int(len(pixels)*.4):int(len(pixels)*.75)]
            colours.append([sum(p[c] for p in mid)/len(mid) for c in range(3)])
        target=[round(statistics.median(x[c] for x in colours),2) for c in range(3)]
        params=exclusions(case['text'])
        protected=case['attrs'].get('MATCH_EXCLUSION_PALETTE',True) is False or case['basename'].startswith('gen_sig8_')
        if not params:params=[None];stats['no_shell']+=1
        for variant,param in enumerate(params):
            row=Image.new('RGB',(W,H),'#202027');d=ImageDraw.Draw(row)
            title=f'{case["id"]} | {case["context"]["system"]} | {case["style"]}'
            d.text((8,5),title,fill='white')
            for x,index,label in [(8,1,'GPU volume: side light'),(312,0,'GPU volume: toward light')]:
                row.paste(Image.open(str(prefix)+f'_{index}.png').resize((296,210)),(x,43))
                d.text((x,27),label,fill='white')
            entry={'id':case['id'],'variant':variant,'system':case['context']['system'],'style':case['style'],
                'template':case['template'],'source':case['source'],'target_rgb':target,'notes':case['notes'],
                'protected':protected,'shader':case['shader'],'current':None,'candidate':None,'generator_next':None}
            if param:
                try:
                    shell,mean=get_shell(param['zone_shell'])
                    current=tuple(int(x.strip()) for x in param.get('exclusion_tint','255,255,255').split(','))
                    fit=[255*x/max(m,.001) for x,m in zip(target,mean)]
                    gamut=max(1,max(fit)/255);candidate=tuple(round(x/gamut) for x in fit)
                    if protected:candidate=current;stats['protected']+=1
                    before=[m*t/255 for m,t in zip(mean,current)]
                    weights=(.2126,.7152,.0722)
                    ratio=sum(w*x for w,x in zip(weights,before))/max(1,sum(w*x for w,x in zip(weights,target)))
                    if ratio>1.5:stats['bright_shell']+=1
                    if ratio<.67:stats['dark_shell']+=1
                    if case['attrs']:
                        next_params=ns['match_exclusion_palette'](SimpleNamespace(**case['attrs']),param)
                        entry['generator_next']=next_params.get('exclusion_tint')
                    for x,label,tint in [(616,'Current installed shell',current),(920,'PROTECTED: authored Sigma-8' if protected else 'Candidate (not applied)',candidate)]:
                        row.paste(ImageChops.multiply(shell,Image.new('RGB',shell.size,tint)),(x,43))
                        d.text((x,27),label,fill='#a5e6ad' if protected else 'white')
                    entry.update(shell=param['zone_shell'],current=current,candidate=candidate,luminance_ratio=round(ratio,3),
                                 max_alpha=param.get('max_alpha'),gamut_limited=gamut>1)
                    detail=f'RGB target {target}; tint {current} -> {candidate}; shell/reference luma {ratio:.2f}x; alpha {param.get("max_alpha","default")}'
                except (OSError,ValueError,StopIteration) as e:
                    entry['error']=str(e);detail='Shell unavailable: '+str(e)
            else:
                detail='No exclusion shell configured; volume reference only. No shell or tint invented.'
                d.text((650,140),'NO EXCLUSION SHELL',fill='#b9c4d8')
            d.text((8,260),detail,fill='white')
            notes='; '.join(case['notes']) or 'Controlled reference: no sky, geometry, lightning or live camera capture'
            d.text((8,277),notes[:185],fill='#d7bd8c')
            d.text((8,294),'Shell swatches omit alpha/background. Candidate matches volume midtones, not the full game composite.',fill='#b4b4bf')
            image_path=OUT/'comparisons'/f'{case["id"]}_{variant}.png';row.save(image_path)
            entry['comparison']=str(image_path);rows.append((row,case['basename']));report.append(entry)
    pages=[]
    for start in range(0,len(rows),5):
        chunk=rows[start:start+5];page=Image.new('RGB',(W,50+len(chunk)*H),'#15151d')
        ImageDraw.Draw(page).text((8,12),f'Nebula comparison {start//5+1} | Production GPU shaders; diagnostic views, not game screenshots | NO CONFIG CHANGES',fill='white')
        for i,(row,_) in enumerate(chunk):page.paste(row,(0,50+i*H))
        page.save(OUT/f'comparison_{start//5+1:02d}.png');pages.append(page)
        for entry in report[start:start+5]:entry['page']=start//5+1
    pages[0].save(OUT/'all_nebulae_comparison.pdf',save_all=True,append_images=pages[1:],resolution=130)
    for name,match in [('sigma8',lambda n:n.startswith('gen_sig8_')),('om15',lambda n:n.startswith('gen_om15_'))]:
        selected=[row for row,n in rows if match(n)]
        sheet=Image.new('RGB',(W,H*len(selected)))
        for i,row in enumerate(selected):sheet.paste(row,(0,i*H))
        sheet.save(OUT/f'{name}_comparison.png')
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    with (OUT/'index.csv').open('w',newline='',encoding='utf-8-sig') as file:
        writer=csv.writer(file);writer.writerow(['page','id','system','style','template','shell','current','candidate','generator_next','luminance_ratio','protected','notes'])
        for r in report:writer.writerow([r.get(k,'') for k in ['page','id','system','style','template','shell','current','candidate','generator_next','luminance_ratio','protected','notes']])
    templates=json.loads((OUT/'templates.json').read_text())
    assert len(templates)==37
    assert len({r['id'] for r in report})==len(cases)
    assert all(r['current']==r['candidate'] for r in report if r['protected'])
    stats.update(rows=len(rows),pages=len(pages),templates=len(templates),shell_errors=sum('error' in r for r in report))
    (OUT/'summary.json').write_text(json.dumps(stats,indent=2))
    (OUT/'README.txt').write_text('All nebulae comparison\n\n'
        'Scope: nebula INIs referenced by installed universe systems, all GENERATED nebula files, and all 37 Pythonlancer templates.\n'
        'Unmatched templates receive a separate fixed-light reference. Source file and context are in cases.json/index.csv.\n'
        'Each case uses its actual style/override, first active cloud layer (as production volume), texture atlas, sun hue where known, exposure and tonemap.\n'
        'Six GPU views: two noise offsets and three light directions in a common 40km sphere. These are diagnostic renders, NOT live screenshots.\n'
        'Candidate: match the unlit shell to median midtones (40-75 percentile) across six views. Uniform gamut compression retains hue.\n'
        'The shell swatch omits max_alpha and background blending. In-game hybrid sprites, retail fog, background, objects and lightning are omitted.\n'
        'Consequently brightness ratios identify candidates for review, not automatic in-game corrections.\n'
        'Sigma-8 is protected and keeps authored colours. No game or generator configuration was modified.\n\n'+json.dumps(stats,indent=2),encoding='utf-8')
    print(json.dumps(stats))


if __name__=='__main__':main()
