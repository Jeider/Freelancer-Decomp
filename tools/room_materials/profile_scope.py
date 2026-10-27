"""Runtime-only scope flag; does not alter generated DDS hashes or UVs."""

def normal_scale(material, texture, value):
    # Columbia/Forbes' pad atlas already contains painted building shadows and
    # markings. Treating those as height creates dark lumps across a flat apron.
    if (material+'|'+texture).lower() == 'detailmap_coldeck|pad.tga021206172714':
        return 0.0
    return value
def scope_flag(source, material, role):
    if role == 'skin' or material.lower() == 'space_trent_head':
        return 1.0  # native facial shading
    if role in ('eye', 'teeth'):
        return 0.0
    if role == 'cloth' and '/characters/' in source.replace('\\', '/').lower():
        return -0.25  # maximum clothing finish, independent of eyes and faces
    return -1.0 if '/bases/' in source.replace('\\', '/').lower() else 0.0
