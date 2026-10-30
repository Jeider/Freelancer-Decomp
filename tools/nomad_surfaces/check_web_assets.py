"""Read-only alpha/compression checks; run with the existing Pillow environment."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
report=[]
for name in ('web-outer-v1','web-inner-v1'):
    records=[]
    for path in (ROOT/f'assets/nomad_membranes/{name}.png',ROOT/f'src/obj/nomad_membrane/{name}.dds'):
        image=Image.open(path)
        assert image.mode=='RGBA',(path,image.mode)
        hist=image.getchannel('A').histogram();n=image.width*image.height
        holes=sum(hist[:16])/n;dense=sum(hist[224:])/n
        assert holes>.20 and dense>.20,(path,holes,dense)
        assert image.width==image.height
        if path.suffix=='.dds':
            raw=path.read_bytes();assert int.from_bytes(raw[28:32],'little')==11
            assert raw[84:88]==b'DXT5' and image.size==(1024,1024)
        records.append(dict(path=str(path.relative_to(ROOT)),size=image.size,open_fraction=round(holes,4),dense_fraction=round(dense,4)))
    assert abs(records[0]['open_fraction']-records[1]['open_fraction'])<.04,'Alpha lost in DDS conversion'
    report.append(records)
out=ROOT/'src/obj/nomad_web';out.mkdir(parents=True,exist_ok=True)
(out/'alpha-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print('PASS true alpha holes, dense fibres, DXT5 format, full mip chain, retained coverage.')
