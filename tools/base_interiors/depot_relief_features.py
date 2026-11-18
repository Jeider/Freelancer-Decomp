"""Manually traced architectural features, independent of native mesh batches.

Coordinates refer to the 768px review atlases. Regions other than RH must supply
their own material/UV bindings; geometry processing and the feature schema are shared.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from depot_surface_audit import OUT

BUILD = OUT / 'modeled'


def features():
    result = []

    def add(mat, name, points, depth=-.075, bevel=3):
        p = np.asarray(points, float)
        if np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1)) < 0:
            p = p[::-1]
        result.append(dict(id=f'{mat}_{len(result):03d}', material=mat, label=name,
                           points_px=p.tolist(), depth_world=depth, bevel_px=bevel))

    def box(mat, name, x0, y0, x1, y1, depth=-.075, bevel=3):
        add(mat, name, [(x0,y0),(x1,y0),(x1,y1),(x0,y1)], depth, bevel)

    def slot(mat, name, x0, y0, x1, y1, depth=-.07):
        r=min(3,(x1-x0)*.22)
        add(mat,name,[(x0+r,y0),(x1-r,y0),(x1,y0+r),(x1,y1-r),
                     (x1-r,y1),(x0+r,y1),(x0,y1-r),(x0,y0+r)],depth,min(1.6,r*.6))

    # Side walls: the broad architectural transitions, not just a few louvres.
    add('15','Large stepped side-wall field',[(167,28),(294,104),(370,105),(370,540),
        (342,540),(342,606),(312,606),(179,721),(166,720)],-.11,4)
    slot('15','Long vertical service channel',72,112,111,577,-.12)
    add('15','Lower stepped service-panel field',[(418,609),(463,609),(463,527),
        (533,481),(586,465),(586,392),(625,392),(625,416),(739,416),
        (739,672),(418,672)],-.07,3)
    add('15','Service hatch recessed field',[(623,200),(741,200),(741,343),
        (711,375),(651,375),(623,346)],-.12,3)
    # The black service opening lies inside the broad panel and gets additional depth.
    box('15','Narrow black service opening',274,248,321,414,-.09,2)
    for j,(x0,x1,y) in enumerate([(220,239,270),(220,239,298),(220,239,324),
        (220,239,354),(220,239,383),(220,239,411)]):
        box('15',f'Side ventilation inset {j+1}',x0,y,x1,y+7,-.035,1.2)
    for j,y in enumerate([453,477,502,526]):
        box('15',f'Right broad louvre {j+1}',630,y,732,y+9,-.065,1.6)
    for j,y in enumerate([487,507,527]):
        box('15',f'Companion louvre {j+1}',478,y,569,y+7,-.05,1.2)

    # Central panel: all three fields and its diagonal braces read as geometry.
    add('20','Central wall left inset panel',[(120,382),(180,382),(180,552),
        (283,552),(283,700),(101,700),(53,657),(53,417),(120,417)],-.09,3)
    box('20','Inset field below service pipes',115,599,269,678,-.04,2)
    add('20','Left angled header field',[(67,246),(194,246),(194,348),
        (119,348),(69,389),(42,389),(42,275)],-.065,3)
    box('20','Upper long recessed panel',43,118,480,231,-.08,4)
    slot('20','Long companion vertical channel',654,40,688,585,-.075)

    add('23','Central shield left triangular recess',[(39,115),(118,115),(39,195)],-.09,3)
    add('23','Central shield right triangular recess',[(322,116),(405,116),(405,195)],-.09,3)
    box('23','Central shield lower left field',39,260,117,321,-.065,2)
    box('23','Central shield lower right field',323,260,405,321,-.065,2)
    box('23','Central shield lower center field',141,270,296,324,-.065,2)
    for j,x in enumerate([129,166,202,239,275,311]):
        slot('23',f'Central shield vertical slot {j+1}',x,134,x+13,227,-.08)
    # Secondary lower field on the same atlas, used by large wall repeats.
    add('23','Lower wall step-shaped inset',[(30,476),(310,476),(310,592),
        (354,592),(354,730),(29,730)],-.08,3)

    # Frames around the terminals. These follow the actual long inset borders.
    add('13','Upper right long frame field',[(528,84),(589,50),(642,25),
        (642,311),(528,311)],-.075,3)
    add('13','Lower left long frame field',[(147,378),(218,340),(243,326),
        (243,714),(202,702),(147,652)],-.075,3)
    slot('13','Right frame vertical recessed stripe',606,113,617,279,-.055)
    slot('13','Left frame vertical recessed stripe',200,490,211,642,-.055)
    box('13','Upper straight structural field',66,37,171,177,-.065,3)
    box('13','Tall lower plain structural field',377,505,681,744,-.065,4)

    add('04','Terminal rear-wall large inset',[(13,365),(239,365),(239,402),
        (219,402),(219,474),(245,474),(245,681),(151,681),
        (141,650),(120,650),(110,681),(13,681)],-.065,3)
    add('04','Terminal upper zigzag recessed band',[(5,316),(25,316),(42,292),
        (84,292),(106,318),(155,318),(178,293),(223,293),
        (242,319),(258,319),(258,351),(5,351)],-.05,2.5)
    box('04','Upper service field',88,111,234,179,-.07,2.5)
    add('04','Hatch lower left recessed field',[(57,424),(115,424),(115,493),
        (99,493),(99,601),(111,630),(111,640),(75,640)],-.05,2)
    add('04','Hatch lower right recessed field',[(150,424),(211,424),(190,640),
        (152,640),(152,629),(168,603),(168,492),(150,492)],-.05,2)
    # Tall shields inside the entry niches: preserve ribs and lower their fields.
    add('04','Niche shield upper left field',[(344,302),(374,302),(362,348),
        (351,400),(343,399)],-.065,2)
    add('04','Niche shield upper right field',[(414,302),(439,302),(439,399),
        (430,399),(416,349)],-.065,2)
    add('04','Niche shield lower left field',[(347,466),(367,466),(378,543),
        (368,545),(350,506)],-.065,2)
    add('04','Niche shield lower right field',[(420,466),(439,466),(437,506),
        (418,545),(407,543)],-.065,2)

    # Companion shield in a different material: trace its own image, not a reused UV box.
    add('14','Entry shield upper left field',[(27,445),(72,445),(57,498),(45,535),(27,535)],-.075,2.5)
    add('14','Entry shield upper right field',[(127,445),(174,445),(174,535),(154,535),(143,498)],-.075,2.5)
    add('14','Entry shield lower left field',[(28,602),(53,602),(74,666),(74,701),(47,701),(28,637)],-.075,2.5)
    add('14','Entry shield lower right field',[(148,602),(174,602),(174,637),(152,701),(125,701),(125,666)],-.075,2.5)
    add('14','Upper stepped service field',[(391,94),(634,94),(634,113),
        (599,141),(392,141)],-.055,2.5)
    # Retain already modelled support forms; add only painted fields inside them.
    add('12','Upper brace large field',[(490,69),(596,69),(596,165),
        (580,180),(490,180)],-.085,3)
    add('12','Upper brace lower triangular field',[(492,273),(596,211),(596,298),(492,298)],-.085,3)
    add('12','Lower support inner field',[(57,553),(174,442),(174,611),(57,611)],-.08,3)
    add('12','Lower support right field',[(217,397),(294,397),(294,547),(217,617)],-.08,3)
    add('12','Lower support bottom field',[(176,705),(292,597),(292,745),(137,745)],-.08,3)
    # Reject ambiguous large fields: their drawn borders coincide with lighting
    # transitions or incomplete atlas islands, rather than an authored recess.
    rejected={'Lower stepped service-panel field','Left angled header field',
              'Upper long recessed panel','Lower wall step-shaped inset',
              'Tall lower plain structural field'}
    from depot_door_features import features as door_features, REPLACED_LABEL_PREFIXES
    return [f for f in result if f['label'] not in rejected and not f['label'].startswith(REPLACED_LABEL_PREFIXES)]+door_features()


def main():
    BUILD.mkdir(exist_ok=True)
    items=features()
    (BUILD/'features.json').write_text(json.dumps(dict(coordinate_size=768,
        authoring='Manual contours following the current RH artwork. No old feature definitions reused.',
        depth_units='native world units',features=items),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for mat in sorted({f['material'] for f in items}):
        im=Image.open(OUT/f'textures/review_{mat}.jpg').convert('RGB');draw=ImageDraw.Draw(im)
        for f in (f for f in items if f['material']==mat):
            p=[tuple(v) for v in f['points_px']]
            draw.line(p+[p[0]],fill=(60,230,255) if f['depth_world']>0 else (255,170,35),width=2)
        im.save(BUILD/f'contours_{mat}.png')
        if mat in ('14','04'):
            crop=(0,340,220,768) if mat=='14' else (325,268,464,620)
            detail=BUILD/'door_detail';detail.mkdir(exist_ok=True)
            view=im.crop(crop);view.resize((view.width*3,view.height*3)).save(detail/f'contours_{mat}.png')
    print('Manual features',len(items),'materials',len({f['material'] for f in items}))


if __name__=='__main__':main()
