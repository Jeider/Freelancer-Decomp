"""Regional bindings of the reviewed RH architectural contours."""
import argparse,copy,json
from PIL import Image,ImageDraw
from native_common import dump
from depot_family_audit import REGIONS,paths
from depot_relief_features import features

# Matched by atlas imagery, including the complete door/shield drawing and
# support-panel layout. Native group numbers are not shared between regions.
MATERIALS={
 'li':{'04':'04','12':'10','13':'11','14':'12','15':'13','20':'18','23':'21'},
 'br':{'04':'04','12':'10','13':'11','14':'12','15':'13','20':'18','23':'21'},
 'ku':{'04':'05','12':'09','13':'10','14':'11','15':'12','20':'16','23':'19'},
}


def generate(region):
    out,*_=paths(region);build=out/'modeled';items=[]
    for source in features():
        f=copy.deepcopy(source);f['source_rh_id']=f['id'];f['source_rh_material']=f['material']
        f['id']=region+'_'+f['id'];f['material']=MATERIALS[region][f['material']]
        items.append(f)
    dump(build/'features.json',dict(coordinate_size=768,region=region,features=items,
        authoring='Manually authored RH contours transferred through inspected regional atlas layouts; UV placement and native holes validated separately.',
        material_mapping=MATERIALS[region],depth_units='native world units',
        redundant_source_faces=([
            dict(group='room_03',drop=130,keep=95,max_position_delta=.003),
            dict(group='room_03',drop=131,keep=62,max_position_delta=.003),
        ] if region=='br' else []),
        native_cleanup_note='BR has two overlapping companion-panel triangles with identical UVs and normals, offset by less than 2.7 mm. Keep each complete native panel once; verify the matching triangles before removal.'))
    mats=sorted({f['material'] for f in items});sheet=Image.new('RGB',(1536,((len(mats)+1)//2)*792),(20,27,34));labels=ImageDraw.Draw(sheet)
    for i,mat in enumerate(mats):
        im=Image.open(out/f'textures/review_{mat}.jpg').convert('RGB');draw=ImageDraw.Draw(im)
        for f in items:
            if f['material']!=mat:continue
            points=[tuple(p) for p in f['points_px']]
            draw.line(points+[points[0]],fill=(60,230,255) if f['depth_world']>0 else (255,170,35),width=2)
        im.save(build/f'contours_{mat}.png');x=i%2*768;y=i//2*792
        sheet.paste(im,(x,y+24));labels.text((x+8,y+5),region.upper()+' atlas '+mat,fill='white')
    sheet.save(build/'contour_review.jpg',quality=93)
    print(region,'features',len(items),'atlas mapping',MATERIALS[region])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('regions',nargs='*',choices=list(REGIONS));args=ap.parse_args()
    for region in args.regions or REGIONS:generate(region)
