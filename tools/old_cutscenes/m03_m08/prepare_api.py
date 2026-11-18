"""Stage typed native authoring features required by the master RTC scenes."""
import ast
import json
from pathlib import Path
from inventory import OUT, PL, sha

manifest = []


def write(relative, text):
    target = PL / relative
    original = target.read_bytes()
    data = text.replace('\n', '\r\n').encode('utf-8') if b'\r\n' in original else text.encode('utf-8')
    if relative.endswith('.py'):
        ast.parse(text)
    stage = OUT / 'api' / relative
    stage.parent.mkdir(parents=True, exist_ok=True)
    stage.write_bytes(data)
    manifest.append(dict(stage=str(stage), target=str(target), before=sha(original), after=sha(data)))


def replace(text, old, new):
    expected = 2 if "lip_group = f'motion_{index}'" in old else 1
    assert text.count(old) == expected, (old, text.count(old))
    return text.replace(old, new)


content = (PL / 'story/cutscenes/content.py').read_text(encoding='utf-8')


def change(cls, edits):
    global content
    start = content.index('class ' + cls + '(') if 'class ' + cls + '(' in content else content.index('class ' + cls + ':')
    end = content.find('\nclass ', start + 1)
    if end < 0:
        end = len(content)
    section = content[start:end]
    for old, new in edits:
        section = replace(section, old, new)
    content = content[:start] + section + content[end:]


change('Point', [
    ('orientation=None, rotate=None):', 'orientation=None, rotate=None, matrix_scale=None):'),
    ('        self.name = name', '        self.name = name\n        self.matrix_scale = matrix_scale or [1, 1, 1]'),
    ('        mx = math.quat_to_matrix(self.orientation)',
     '        mx = math.quat_to_matrix(self.orientation)\n        mx = [[mx[i][j] * self.matrix_scale[j] for j in range(3)] for i in range(3)]'),
])
change('Compound', [
    ('use_ambient=False, matrix_scale=1, rotate_from_quat=False,',
     'use_ambient=False, matrix_scale=1, rotate_from_quat=False,\n                 use_dynamic=True, no_fog=False,'),
    ('        self.use_ambient = use_ambient',
     '        self.use_ambient = use_ambient\n        self.use_dynamic = use_dynamic\n        self.no_fog = no_fog'),
    ('            return self.point.matrix_from_quat', '            mx = math.quat_to_matrix(self.point.orientation)\n            mx = [[mx[i][j] * self.point.matrix_scale[j] for j in range(3)] for i in range(3)]'),
    ("        return '''\n", "        scale = self.matrix_scale if isinstance(self.matrix_scale, (tuple, list)) else [self.matrix_scale] * 3\n        if len(scale) != 3:\n            raise ValueError('Compound scale must have three components')\n        return '''\n"),
    *[(f'mx[{i}][{j}]*self.matrix_scale', f'mx[{i}][{j}]*scale[{j}]') for i in range(3) for j in range(3)],
    ('        flags = [LIT_DYNAMIC]', '        flags = [LIT_DYNAMIC] if self.use_dynamic else []'),
    ("            'usr_flg': self.USR_FLG,", "            'usr_flg': self.USR_FLG,\n            'no_fog': self.no_fog,"),
])
change('Character', [
    ('facial_indexes=1, bind_actor=True, *args, **kwargs):',
     'facial_indexes=1, bind_actor=True, name=None, appearance=None, actor_name=None, *args, **kwargs):'),
    ("        name = f'Char_{self.actor.NAME}'", "        name = name or f'Char_{self.actor.NAME}'\n        self.appearance = appearance\n        self.actor_name = actor_name"),
    ('        if not self.actor.CUTSCENE_APPEARANCE', '        if self.appearance is not None:\n            return self.appearance\n        if not self.actor.CUTSCENE_APPEARANCE'),
    ("params['actor'] = self.actor.get_game_actor() if self.bind_actor else None",
     "params['actor'] = (self.actor_name if self.actor_name is not None else self.actor.get_game_actor()) if self.bind_actor else None"),
    ('auto_anim_force=None, auto_anim_force_seconds=None):',
     'auto_anim_force=None, auto_anim_force_seconds=None, props=None, voice_actor=None):'),
    ('sound = self.root.lookup_single_sound(index)', 'sound = self.root.lookup_single_sound(index, props=props)'),
    ('if self.actor != sound.line.actor:', 'if (voice_actor or self.actor) != sound.line.actor:'),
    # A scene may combine two named dialogues with overlapping numeric indexes.
    ("            lip_group = f'motion_{index}'\n            self.root.clone_group", "            lip_group = f'motion_{sound.get_nickname()}_{len(self.root.events)}'\n            self.root.clone_group"),
])
change('MotionEvent', [
    ('loop=False, trans_time=None, *args, **kwargs):', 'loop=False, trans_time=None, trans_scale=None, *args, **kwargs):'),
    ('        self.trans_time = trans_time', '        self.trans_time = trans_time\n        self.trans_scale = trans_scale'),
    ("            'trans_time': self.trans_time,", "            'trans_time': self.trans_time,\n            'trans_scale': self.trans_scale,"),
])
change('MoveEvent', [
    ('rotate_y=0, *args, **kwargs):', 'rotate_y=0, offset=(0, 0, 0), *args, **kwargs):'),
    ('        self.rotate = (0, rotate_y, 0)', '        self.rotate = (0, rotate_y, 0)\n        self.offset = offset'),
    ('            rules.append(self.ADJUST_POS)', "            rules.append('pos = { ' + ', '.join(str(v) for v in self.offset) + ' }')"),
])
change('LookAtEvent', [
    ("target_type=TARGET_ROOT, *args, **kwargs):", "target_type=TARGET_ROOT, up=Y_AXIS, front=NEG_Z_AXIS, *args, **kwargs):"),
    ('        self.target_type = target_type', '        self.target_type = target_type\n        self.up = up\n        self.front = front'),
    ("            'target_type': self.target_type,", "            'target_type': self.target_type,\n            'up': self.up,\n            'front': self.front,"),
    ("            'point': self.point,", "            'point': self.point,\n            'point_name': self.point if isinstance(self.point, str) else self.point.name,"),
    ("            'focus': self.focus,", "            'focus': self.focus,\n            'focus_name': self.focus if isinstance(self.focus, str) else self.focus.name,"),
])
change('AttachEvent', [
    ('offset_x=0, offset_y=0, offset_z=0,', 'offset_x=0, offset_y=0, offset_z=0,\n                 orientation_relative=False, up=Y_AXIS, front=NEG_Z_AXIS,'),
    ('        self.entity_relative = entity_relative', '        self.entity_relative = entity_relative\n        self.orientation_relative = orientation_relative\n        self.up = up\n        self.front = front'),
    ("        return ' + '.join(flags)", "        if self.orientation_relative:\n            flags.append('ORIENTATION_RELATIVE')\n        return ' + '.join(flags)"),
    ("            'offset_z': self.offset_z,", "            'offset_z': self.offset_z,\n            'up': self.up,\n            'front': self.front,"),
])
change('PathAnimationEvent', [
    ('adjust_pos=True, adjust_orient=False, start_percent=0, stop_percent=1, *args, **kwargs):',
     'adjust_pos=True, adjust_orient=False, start_percent=0, stop_percent=1,\n                 curve_points=None, curve_period=-1000, *args, **kwargs):'),
    ('        self.stop_percent = stop_percent',
     '        self.stop_percent = stop_percent\n        self.curve_points = curve_points\n        self.curve_period = curve_period'),
    ("            'stop_percent': self.stop_percent,", "            'stop_percent': self.stop_percent,\n            'curve_points': self.curve_points,\n            'curve_period': self.curve_period,"),
])
change('AlchemyAnimEvent', [
    ('def __init__(self, object_name, duration, sparam, *args, **kwargs):',
     'def __init__(self, object_name, duration, sparam, smooth=False, *args, **kwargs):'),
    ('        self.sparam = sparam', '        self.sparam = sparam\n        self.smooth = smooth'),
    ("            'sparam': self.sparam,", "            'sparam': self.sparam,\n            'smooth': self.smooth,"),
])
change('Alchemy', [
    ('def __init__(self, particles, point_name=None, sparam=0, *args, **kwargs):',
     'def __init__(self, particles, point_name=None, sparam=0, light_group=0, sort_group=0,\n                 hidden=True, use_ambient=True, *args, **kwargs):'),
    ('        self.sparam = sparam', '        self.sparam = sparam\n        self.light_group = light_group\n        self.sort_group = sort_group\n        self.hidden = hidden\n        self.use_ambient = use_ambient'),
    ("            'sparam': self.sparam,", "            'sparam': self.sparam,\n            'light_group': self.light_group,\n            'sort_group': self.sort_group,\n            'flags': ' + '.join(([\"HIDDEN\"] if self.hidden else []) + [LIT_DYNAMIC] + ([LIT_AMBIENT] if self.use_ambient else [])),"),
])
change('Light', [
    ('range=2000, cutoff=90, theta=90, color=None, attenuation=None, *args, **kwargs):',
     'range=2000, cutoff=90, theta=90, color=None, attenuation=None, hidden=False,\n                 specular=None, rotate_from_quat=False, *args, **kwargs):'),
    ('        self.is_reference = is_reference', '        self.is_reference = is_reference\n        self.hidden = hidden'),
    ("            'is_reference': self.is_reference,", "            'is_reference': self.is_reference,\n            'hidden': self.hidden,"),
    ('        self.diffuse = diffuse', '        self.diffuse = diffuse\n        self.specular = [0, 0, 0] if specular is None else specular\n        self.rotate_from_quat = rotate_from_quat'),
    ("            'hidden': self.hidden,", "            'hidden': self.hidden,\n            'specular': ', '.join(str(i) for i in self.specular),\n            'rotate_from_quat': self.rotate_from_quat,"),
])
change('Camera', [
    ('def __init__(self, name, fov, farplane=5000, *args, **kwargs):',
     'def __init__(self, name, fov, farplane=5000, nearplane=0.2, aspect=1.85, *args, **kwargs):'),
    ('        self.farplane = farplane', '        self.farplane = farplane\n        self.nearplane = nearplane\n        self.aspect = aspect'),
    ("            'farplane': self.farplane,", "            'farplane': self.farplane,\n            'nearplane': self.nearplane,\n            'aspect': self.aspect,"),
])
write('story/cutscenes/content.py', content)

scene = (PL / 'story/cutscenes/scene.py').read_text(encoding='utf-8')
scene = replace(scene, '        self.props = props', '        self.props = props\n        self.dialogue_props = []')
scene = replace(scene, "orientation=value.get('orientation', [1, 0, 0, 0]),", "orientation=value.get('orientation', [1, 0, 0, 0]),\n                matrix_scale=value.get('matrix_scale'),")
scene = replace(scene, 'source, rotate=None, orientation=None):', 'source, rotate=None, orientation=None, matrix_scale=None):')
scene = replace(scene, '            orientation=orientation,', '            orientation=orientation,\n            matrix_scale=matrix_scale,')
scene = replace(scene, '    def lookup_single_sound(self, index):\n        for sound in self.props.get_sounds():',
                '    def lookup_single_sound(self, index, props=None):\n        selected = props or self.props\n        if selected is not self.props and selected not in self.dialogue_props:\n            self.dialogue_props.append(selected)\n        for sound in selected.get_sounds():')
scene = replace(scene, "        return STRING_DIVIDER.join([s.get_thorn() for s in self.props.get_sounds()])",
                "        sounds = {s.get_nickname(): s for props in [self.props, *self.dialogue_props] for s in props.get_sounds()}\n        return STRING_DIVIDER.join(s.get_thorn() for s in sounds.values())")
write('story/cutscenes/scene.py', scene)

edits = {
    'event/look_at.lua': [('up=Y_AXIS', 'up={{ up }}'), ('front=NEG_Z_AXIS', 'front={{ front }}'),
                          ('{{ point.name }}', '{{ point_name }}'), ('{{ focus.name }}', '{{ focus_name }}')],
    'event/attach.lua': [('    0,', '    {{ time }},'), ('up=Y_AXIS', 'up={{ up }}'), ('front=NEG_Z_AXIS', 'front={{ front }}')],
    'event/motion.lua': [('     }', '     {% if trans_scale != None %}, trans_scale={{ trans_scale }} {% endif %}\n     }')],
    'event/path_anim.lua': [('        {% if smooth %}', '        {% if curve_points %}\n        , param_curve={CLSID="FreeFormPCurve", points={ {% for p in curve_points %}{ {{ p|join(",") }} }{% if not loop.last %},{% endif %}{% endfor %} }},\n        pcurve_period={{ curve_period }}\n        {% elif smooth %}')],
    'event/alchemy_anim.lua': [('            sparam={{ sparam }}\n        }', '            sparam={{ sparam }}\n        }\n        {% if smooth %}, param_curve={CLSID="FreeFormPCurve",points={ {0,0,0,0},{1,1,0,0} }}, pcurve_period=-1000{% endif %}')],
    'entity/prop.lua': [('        category="Prop"', '        category="Prop"{% if no_fog %}, NoFog="Y"{% endif %}')],
    'entity/alchemy.lua': [('lt_grp=0', 'lt_grp={{ light_group }}'), ('srt_grp=0', 'srt_grp={{ sort_group }}'), ('flags=HIDDEN + LIT_DYNAMIC + LIT_AMBIENT', 'flags={{ flags }}')],
    'entity/light.lua': [('    {% if is_reference %} flags=REFERENCE, {% endif %}', '    {% if is_reference %} flags=REFERENCE, {% elif hidden %} flags=HIDDEN, {% endif %}'),
                         ('            0,\n            0,\n            0', '            {{ specular }}'),
                         ('            {1,0,0},\n            {0,1,0},\n            {0,0,1}', '            {% if rotate_from_quat %}{{ point.matrix_from_quat }}{% else %}{1,0,0},{0,1,0},{0,0,1}{% endif %}')],
    'entity/camera.lua': [('hvaspect=1.85', 'hvaspect={{ aspect }}'), ('nearplane=0.2', 'nearplane={{ nearplane }}')],
    'entity/camera_static.lua': [('hvaspect=1.85', 'hvaspect={{ aspect }}'), ('nearplane=0.2', 'nearplane={{ nearplane }}')],
}
for relative, changes in edits.items():
    relative = 'templates/cutscenes/' + relative
    text = (PL / relative).read_text(encoding='utf-8')
    for old, new in changes:
        text = replace(text, old, new)
    write(relative, text)
(OUT / 'api_plan.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(f'Staged {len(manifest)} native API/template files')
