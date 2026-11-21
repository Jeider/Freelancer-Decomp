"""Build a one-LOD Higa body on the ku_kym_body_gen skeleton and mounts."""
import hashlib
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/hatcher_hair'))
from build import GAME, DataFolder, read_tree, write_tree, child, blob
from generate_station_lods import Node

OUT = ROOT / 'out/character_rounding/higa/game_body'
REL = 'CHARACTERS/BODIES/higa_body.dfm'
DONOR = 'BODIES/ku_kym_body_gen.dfm'
TEXTURE = Path('D:/work/MESHY/higa1/Meshy_AI_Golden_Armored_Warrior_20261119_texture.png')


def branch(name, children):
    node = Node(name)
    node.children = children
    return node


def array(name, values, kind):
    return Node(name, np.asarray(values, dtype=kind).tobytes())


def dds_bytes(image):
    levels, header = [], None
    image = image.convert('RGB')
    while True:
        stream = io.BytesIO()
        image.save(stream, format='DDS', pixel_format='DXT1')
        raw = stream.getvalue()
        if header is None:
            header = bytearray(raw[:128])
        levels.append(raw[128:])
        if image.size == (1, 1):
            break
        image = image.resize((max(1, image.width // 2), max(1, image.height // 2)), Image.Resampling.BOX)
    struct.pack_into('<I', header, 8, struct.unpack_from('<I', header, 8)[0] | 0x20000)
    struct.pack_into('<I', header, 28, len(levels))
    struct.pack_into('<I', header, 108, 0x401008)
    return bytes(header) + b''.join(levels)


def chains(weights):
    first, counts, ids, values = [], [], [], []
    for row in weights:
        idx = np.flatnonzero(row)
        first.append(len(ids))
        counts.append(len(idx))
        ids.extend(int(i) for i in idx)
        values.extend(float(row[i]) for i in idx)
    return first, counts, ids, values


def main():
    mesh = np.load(OUT / 'mesh.npz', allow_pickle=True)
    points, normals, uv = mesh['points'], mesh['normals'], mesh['uv']
    weights, names = mesh['weights'], mesh['bone_names'].tolist()
    costume, skin = mesh['costume'], mesh['skin_cap']
    assert len(points) < 65536
    assert np.max(np.abs(weights.sum(1) - 1)) < 1e-4
    source = (GAME / 'DATA/CHARACTERS' / DONOR).read_bytes()
    header, roots = read_tree(source)
    root = roots[0]
    bone_ids = {
        blob(part, 'Object name').rstrip(b'\0').decode(): struct.unpack('<I', blob(part, 'Index'))[0]
        for part in child(root, 'Cmpnd').children if any(x.name == 'Index' for x in part.children)
    }
    # Weight columns follow armature order. Remap them to this file's bone indices.
    order = [bone_ids[name] for name in names]
    remapped = np.zeros_like(weights)
    for column, bone_id in enumerate(order):
        remapped[:, bone_id] = weights[:, column]
    # Cmpnd Index is the skin index used by Deformable, which matches 3db order here.
    used = remapped
    first, counts, ids, values = chains(used)
    geometry = branch('Geometry', [
        array('Points', points, '<f4'), array('Vertex_normals', normals, '<f4'),
        array('Point_indices', np.arange(len(points)), '<u4'),
        array('UV0', uv, '<f4'), array('UV0_indices', np.arange(len(points)), '<u4'),
        array('Point_bone_first', first, '<u4'), array('Point_bone_count', counts, '<u4'),
        array('Bone_id_chain', ids, '<u4'), array('Bone_weight_chain', values, '<f4')])
    groups = [branch('Group0', [Node('Material_name', b'higa_body\0'), array('Face_indices', costume, '<u2')])]
    if len(skin):
        groups.append(branch('Group1', [Node('Material_name', b'higa_skin\0'), array('Face_indices', skin, '<u2')]))
    child(root, 'MultiLevel').children = [array('Fractions', [1.0], '<f4'), branch('Mesh0', [
        branch('Face_groups', [array('Count', [len(groups)], '<u4')] + groups), geometry])]
    costume_tex = dds_bytes(Image.open(TEXTURE))
    skin_image = Image.new('RGB', (64, 64), (184, 128, 98))
    skin_tex = dds_bytes(skin_image)
    materials = [
        branch('higa_body', [Node('Type', b'DcDt\0'), Node('Dt_name', b'higa_body.tga\0'), array('Dt_flags', [64], '<u4')]),
        branch('higa_skin', [Node('Type', b'DcDt\0'), Node('Dt_name', b'higa_skin.tga\0'), array('Dt_flags', [64], '<u4')])]
    child(root, 'Material library').children = [array('Material count', [2], '<u4')] + materials
    child(root, 'Texture library').children = [
        branch('higa_body.tga', [Node('MIPS', costume_tex)]),
        branch('higa_skin.tga', [Node('MIPS', skin_tex)])]
    payload = write_tree(header, roots)
    body_ini = (
        '[DetailSwitchTable]\r\nswitch = 100, 50000\r\n\r\n'
        '[PetalAnimations]\r\n'
        'anim = characters\\animations\\BodyGenericFemale.anm\r\n'
        'anim = characters\\animations\\BodyStoryFemale.anm\r\n'
        'anim = characters\\animations\\Special.anm\r\n\r\n'
        '[Skeleton]\r\nsex = female\r\n\r\n'
        '[Body]\r\nnickname = higa_body\r\nmesh = characters\\bodies\\higa_body.dfm\r\n')
    costume_ini = (
        '[Costume]\r\nnickname = higa\r\nhead = ku_kym_head_gen\r\nbody = higa_body\r\n'
        'righthand = benchmark_female_hand_right\r\nlefthand = benchmark_female_hand_left\r\n')
    stage = DataFolder(root=OUT / 'stage')
    stage.sync_data_file(REL, payload)
    live = DataFolder(root=GAME)
    files = {REL: payload}
    for rel, addition, token in (
            ('CHARACTERS/bodyparts.ini', body_ini.encode(), b'nickname = higa_body'),
            ('CHARACTERS/costumes.ini', costume_ini.encode(), b'nickname = higa\r\n')):
        original = live.data_path(rel).read_bytes()
        if token in original:
            updated = original
        else:
            updated = original.rstrip(b'\r\n') + b'\r\n\r\n' + addition
        stage.sync_data_file(rel, updated)
        files[rel] = updated
    sha = lambda b: hashlib.sha256(b).hexdigest()
    manifest = {
        'body': 'higa_body', 'costume': 'higa', 'head': 'ku_kym_head_gen',
        'mount': 'ku_kym_body_gen hardpoints, same female skeleton',
        'points': len(points), 'costume_tris': len(costume), 'skin_tris': len(skin),
        'neck': 'Meshy head removed; skin cap only', 'installed': False,
        'files': {rel: {'after': sha(data)} for rel, data in files.items()},
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print(json.dumps({k: manifest[k] for k in ('body', 'points', 'costume_tris', 'skin_tris', 'head')}))


if __name__ == '__main__':
    main()
