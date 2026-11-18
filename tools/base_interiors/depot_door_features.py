"""Layered relief for the painted mechanical doors, in reviewed atlas pixels.

The full entrance door and the companion terminal panel share the body drawing.
The second atlas uses its own fitted body mapping and an independently drawn frame.
These replace the previous four isolated pockets on each panel.
"""
import numpy as np


def features():
    out=[]
    def add(mat,name,p,depth,bevel=1.5):
        p=np.asarray(p,float)
        if np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))<0:p=p[::-1]
        out.append(dict(id=f'door_{mat}_{len(out):02d}',material=mat,label='Door: '+name,
            points_px=p.tolist(),depth_world=depth,bevel_px=bevel,door_detail=True))

    # The visible door at the back of each of the four octagonal niches.
    add('14','raised outer frame',[(17,752),(17,437),(28,428),(62,361),
        (143,361),(184,423),(193,433),(193,752)],.045,2)
    add('14','recessed door face',[(24,746),(24,443),(45,437),(50,429),
        (45,424),(77,378),(86,373),(127,373),(169,424),
        (166,431),(187,442),(187,746)],-.078,2)
    # Painted top arch and the rounded crest inside it.
    add('14','upper chevron ridge',[(43,417),(77,375),(131,375),(166,417),
        (157,417),(127,383),(82,383),(52,417)],.042,1.4)
    add('14','arched upper crest',[(76,418),(79,406),(86,395),(92,384),
        (99,379),(105,378),(111,380),(119,386),(126,398),(132,409),
        (133,418)],.055,2)
    add('14','crest center inset',[(94,414),(96,407),(100,401),(104,398),
        (108,400),(114,407),(116,414)],-.024,1)

    # Body contours follow the painted silhouette: central shield, ribs and locks.
    body=[
        ('central shield',[(95,426),(109,426),(111,487),(121,492),(123,539),
            (116,548),(116,590),(125,597),(125,641),(117,668),
            (116,680),(116,723),(110,731),(97,731),(90,724),
            (90,680),(87,667),(80,642),(80,600),(90,591),
            (90,550),(81,541),(82,495),(94,488)],.088,2.1),
        ('upper left diagonal rib',[(84,435),(90,437),(73,486),(58,538),
            (51,548),(40,546),(58,502),(77,448)],.060,1.5),
        ('upper right diagonal rib',[(117,435),(124,436),(133,448),(153,503),
            (168,545),(158,548),(150,536),(132,486)],.060,1.5),
        ('lower left diagonal rib',[(40,602),(53,601),(68,639),(87,669),
            (86,681),(77,676),(61,651)],.055,1.5),
        ('lower right diagonal rib',[(153,601),(166,602),(146,652),(129,678),
            (120,680),(120,669),(139,639)],.055,1.5),
        ('upper left locking bar',[(25,551),(72,551),(76,557),(86,557),
            (86,565),(65,565),(60,560),(25,560)],.052,1.2),
        ('upper right locking bar',[(122,557),(132,557),(136,551),(181,551),
            (181,560),(145,560),(140,565),(122,565)],.052,1.2),
        ('lower left locking bar',[(29,586),(64,586),(70,580),(85,580),
            (85,590),(70,594),(33,594),(29,599)],.052,1.2),
        ('lower right locking bar',[(123,580),(139,580),(144,586),(179,586),
            (182,599),(177,594),(141,594),(123,590)],.052,1.2),
        ('central lock housing',[(92,552),(114,552),(114,590),(109,596),
            (98,596),(92,590)],.025,1.3),
        ('lock inset',[(101,568),(108,568),(108,587),(101,587)],-.032,.9),
        ('lower left prong',[(81,679),(89,679),(90,719),(95,725),
            (87,730),(80,721)],.050,1.2),
        ('lower right prong',[(118,679),(126,679),(126,721),(119,730),
            (113,725),(118,719)],.050,1.2),
        ('left lower latch stem',[(47,705),(52,705),(52,740),(47,740)],.032,.9),
        ('right lower latch stem',[(151,705),(156,705),(156,740),(151,740)],.032,.9),
        ('left lower latch crossbar',[(39,714),(59,714),(62,720),(54,720),
            (51,724),(47,724),(44,720),(36,720)],.025,.9),
        ('right lower latch crossbar',[(143,714),(163,714),(166,720),(158,720),
            (155,724),(151,724),(148,720),(140,720)],.025,.9),
    ]
    for name,p,depth,bevel in body:add('14',name,p,depth,bevel)

    # Room-04 has a flat top and different framing. Only the shared mechanical
    # body drawing is mapped; the entrance door's arch is deliberately not copied.
    add('04','companion raised frame',[(337,608),(337,301),(343,281),
        (365,279),(371,288),(421,288),(429,277),(447,277),
        (453,298),(453,608)],.035,1.5)
    add('04','companion recessed face',[(344,602),(344,304),(365,295),
        (425,295),(445,304),(445,602)],-.067,1.6)
    for name,p,depth,bevel in body:
        # This atlas has small worn sockets here, not the entrance's cross handles.
        if 'lower latch' in name:continue
        points=np.asarray(p,float)
        points[:,0]=332.0+points[:,0]*.61
        points[:,1]=293.0+(points[:,1]-426.0)*.97
        add('04','companion '+name,points,depth*.85,max(.65,bevel*.70))
    return out


REPLACED_LABEL_PREFIXES=('Niche shield ','Entry shield ')
