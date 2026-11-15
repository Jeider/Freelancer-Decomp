"""Build and install top-right NeuroNet icons in both models and montage tiles."""
import argparse,json,subprocess
from io import BytesIO
from PIL import Image,ImageDraw,ImageChops,ImageFont
import base_icons as b
from check import ROOT,VC,compiler_env
OUT=ROOT/'out/nn_icons'
PREVIEW=ROOT/'src/obj/nn_icons'
NAMES=('nn_map','nn_inventory','nn_storystar','nn_playerstatus','nn_info','nn_chat','nn_request','nn_grouprequest')
ATLAS='INTERFACE/buttontextures.txm'
STORY_ONLY=False
def build():
    PREVIEW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/DNOMINMAX',
        f'/I{ROOT/"src/freelancer/Client"}',str(ROOT/'tools/cursors/nn_export.cpp'),'/Fenn_export.exe'],
        cwd=PREVIEW,env=compiler_env(),check=True)
    subprocess.run([str(PREVIEW/'nn_export.exe'),str(PREVIEW)],check=True)
    game=b.DataFolder(root=b.GAME);originals=b.DataFolder(root=OUT/'originals');stage=b.DataFolder(root=OUT/'stage')
    manifest={};old_images={}
    def source(rel):
        live=game.data_path(rel).read_bytes()
        if not originals.data_path(rel).exists():originals.sync_data_file(rel,live)
        original=originals.data_path(rel).read_bytes()
        manifest[rel]={'before':b.digest(live),'original':b.digest(original)}
        return live if STORY_ONLY else original
    def save(rel,blob):
        stage.sync_data_file(rel,blob);manifest[rel]['after']=b.digest(blob)
    def raster(name,size):
        return Image.frombytes('RGBA',(size,size),(PREVIEW/f'{name}_{size}.bgra').read_bytes(),'raw','BGRA')
    def encode(im):return b.tga(im.tobytes('raw','BGRA'),im.width)
    for name in NAMES:
        rel=f'INTERFACE/NEURONET/ICONS/{name}.3db'
        h,tree=b.read_tree(source(rel));before={p:n.blob for p,n in b.walk(tree) if n.blob is not None}
        textures=[n for p,n in b.walk(tree) if '/Texture library/' in p and n.blob is None and any(c.name=='MIP0' for c in n.children)]
        assert len(textures)==1
        texture=textures[0]
        old_images[name]=Image.open(BytesIO(next(n.blob for n in texture.children if n.name=='MIP0'))).convert('RGBA')
        texture.children=[n for n in texture.children if not n.name.startswith('MIP')]
        for level,size in enumerate((512,256,128,64,32,16)):
            im=raster(name,size);blob=encode(im)
            assert Image.open(BytesIO(blob)).convert('RGBA').tobytes()==im.tobytes()
            texture.children.append(b.Node(f'MIP{level}',blob))
        blob=b.write_tree(h,tree);_,check=b.read_tree(blob)
        after={p:n.blob for p,n in b.walk(check) if n.blob is not None}
        assert all(after[p]==value for p,value in before.items() if '/Texture library/' not in p)
        save(rel,blob)
    # Read the actual runtime mapping, counting every tile exactly as LoadButtonMontage.
    mapping={};index=0;size=0;texture=0
    ini=game.data_path('INTERFACE/buttonmontage.ini').read_bytes()
    for line in ini.decode('utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith(';'):continue
        if line.startswith('['):index=0;size=0;texture=0;continue
        key,value=(s.strip() for s in line.split('=',1))
        if key.lower()=='size':size=int(value);index=0;continue
        if key.lower()=='texture':texture=int(value);continue
        if key.lower()=='num_pages':continue
        name=key.replace('\\','/').rsplit('/',1)[-1].lower().removesuffix('.3db')
        if name in NAMES:
            assert texture==0 and size in (32,64)
            mapping[name]=(f'Montage{size}',index%(256//size),index//(256//size),256//size)
        index+=1
    assert set(mapping)==set(NAMES)-{'nn_grouprequest'}
    h,tree=b.read_tree(source(ATLAS));before={p:n.blob for p,n in b.walk(tree) if n.blob is not None}
    changed=set();atlas_refs={};rect_count=0;gpu_mapping=[]
    for path,node in b.walk(tree):
        entries=[(name,*slot[1:]) for name,slot in mapping.items() if node.name==slot[0]]
        if not entries:continue
        for mip in node.children:
            if not mip.name.startswith('MIP') or not mip.blob:continue
            original=Image.open(BytesIO(mip.blob)).convert('RGBA');im=original.copy()
            mask=Image.new('L',im.size);mark=ImageDraw.Draw(mask)
            for name,col,row,count in entries:
                side=im.width//count;x=col*side;y=im.height-(row+1)*side
                if mip.name=='MIP0':
                    atlas_refs[name]=im.crop((x,y,x+side,y+side)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                rendered=raster(name,side) if side in (16,32,64,128,256,512) else raster(name,128).resize((side,side),Image.Resampling.LANCZOS)
                # TGA montage UVs are bottom-up relative to PIL; individual models
                # use their original mesh UVs. Flip ONLY the generated atlas cell.
                im.paste(rendered.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(x,y))
                mark.rectangle((x,y,x+side-1,y+side-1),fill=255);rect_count+=1
            outside=ImageChops.invert(mask)
            for channel in ImageChops.difference(im,original).split():
                assert ImageChops.multiply(channel,outside).getbbox() is None,'Unrelated atlas pixels changed'
            mip.blob=encode(im)
            assert Image.open(BytesIO(mip.blob)).convert('RGBA').tobytes()==im.tobytes()
            if mip.name=='MIP0':
                gpu_file=node.name+'_engine.bgra'
                # DecodeTgaTexture copies descriptor=8 bytes unchanged to the GPU.
                (PREVIEW/gpu_file).write_bytes(mip.blob[18:])
                for name,col,row,count in entries:gpu_mapping.append(f'{name} {gpu_file} {im.width} {col} {row} {count}')
            changed.add(path+'/'+mip.name)
    blob=b.write_tree(h,tree);_,check=b.read_tree(blob)
    after={p:n.blob for p,n in b.walk(check) if n.blob is not None}
    assert all(after[p]==value for p,value in before.items() if p not in changed)
    save(ATLAS,blob)
    # Mapping is read-only but must not change between staging and installation.
    manifest['INTERFACE/buttonmontage.ini']={'before':b.digest(ini),'after':b.digest(ini),'original':b.digest(ini)}
    stage.sync_data_file('INTERFACE/buttonmontage.ini',ini)
    sheet=Image.new('RGBA',(256*len(NAMES),900),(12,20,32,255));draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(NAMES):
        draw.text((i*256+3,3),name+' original model',fill='white')
        sheet.alpha_composite(old_images[name].resize((256,256)),(i*256,25))
        draw.text((i*256+3,300),'original montage (upright)',fill='white')
        sheet.alpha_composite(atlas_refs.get(name,old_images[name]).resize((256,256)),(i*256,325))
        draw.text((i*256+3,600),'new geometry',fill='white')
        sheet.alpha_composite(raster(name,256),(i*256,625))
        raster(name,256).save(PREVIEW/(name+'.png'))
    sheet.convert('RGB').save(PREVIEW/'comparison_v4.png')
    if STORY_ONLY:
        # Compare the installed artwork, not the retail backup. Rasterize the
        # new vector at each displayed size to show actual small-icon coverage.
        comparison=Image.new('RGB',(800,440),(12,22,30));d=ImageDraw.Draw(comparison)
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
        small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
        d.text((24,16),'STORY STAR — ДО / ПОСЛЕ',font=font,fill='white')
        old=old_images['nn_storystar'];new=raster('nn_storystar',256)
        for col,(label,art) in enumerate((('ДО',old),('ПОСЛЕ',new))):
            x=24+col*390;d.text((x,55),label,font=font,fill=(178,217,237))
            for row,bg in enumerate(((15,31,43),(56,85,88))):
                y=92+row*165;d.rectangle((x,y,x+365,y+145),fill=bg)
                for size,offset in ((32,16),(64,76),(128,175)):
                    tile=art.resize((size,size),Image.Resampling.LANCZOS) if col==0 else raster('nn_storystar',size)
                    comparison.paste(tile,(x+offset,y+(130-size)//2),tile)
                    d.text((x+offset,y+127),str(size)+' px',font=small,fill='white')
        comparison.save(PREVIEW/'comparison.png')
        print('Comparison:',PREVIEW/'comparison.png')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (PREVIEW/'atlas_gpu.txt').write_text('\n'.join(gpu_mapping)+'\n')
    print(f'PASS: {len(NAMES)} models, {6*len(NAMES)} mip levels, {rect_count} montage cells; unchanged other pixels, mesh and material leaves; TGA roundtrip')
    print('Preview:',PREVIEW/'comparison_v4.png')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--story-star',action='store_true');args=parser.parse_args()
    if args.story_star:
        STORY_ONLY=True;NAMES=('nn_storystar',);OUT=ROOT/'out/nn_story_star';PREVIEW=ROOT/'src/obj/nn_story_star'
    if args.apply:b.OUT=OUT;b.install('NeuroNet')
    else:build()

