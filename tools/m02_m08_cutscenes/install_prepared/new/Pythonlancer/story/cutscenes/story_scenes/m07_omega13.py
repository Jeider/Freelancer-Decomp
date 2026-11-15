"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_planet_1(Solar):
    COMPOUND_TEMPLATE_NAME = 'planet_mercury_5000'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_blackhole(Solar):
    COMPOUND_TEMPLATE_NAME = 'BlackHoleSun'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_the_stars(Prop):
    COMPOUND_TEMPLATE_NAME = 'new_generic'
    SRT_GRP = -100
    USR_FLG = 1


class Asset_obj_the_background(Prop):
    COMPOUND_TEMPLATE_NAME = 'om13_nebula'
    SRT_GRP = -100
    USR_FLG = 1


class Asset_obj_gun01(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_mass_driver'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_gun02(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_mass_driver'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_launcher01(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_slugger_launcher'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_cockpit_gun01(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_mass_driver'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_cockpit_gun02(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_mass_driver'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_missile01(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_slugger_missile'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_missile02(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_weapons_br_slugger_missile'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_rockford_chair(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_pilot_chair'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_rockford_front(Ship):
    COMPOUND_TEMPLATE_NAME = 'ge_fighter6'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_PlayerShip(Ship):
    COMPOUND_TEMPLATE_NAME = 'PlayerShip'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_the_cockpit(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_cockpit'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_case(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_case'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_panel(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_panel'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crystal(Prop):
    COMPOUND_TEMPLATE_NAME = 'Blixx_crystal'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_tome(Prop):
    COMPOUND_TEMPLATE_NAME = 'tome_075'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_chair(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_pilot_chair'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_rockford_cockpit(Ship):
    COMPOUND_TEMPLATE_NAME = 'ge_fighter6'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_omega13'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_DX_m07_omega13_0010_trent = Sound(root=self, name='DX_m07_omega13_0010_trent', sound='DX_m07_omega13_0010_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_omega13_0010_trent, {'template_name': 'DX_m07_omega13_0010_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_omega13_0050b_trent = Sound(root=self, name='DX_m07_omega13_0050b_trent', sound='DX_m07_omega13_0050b_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_omega13_0050b_trent, {'template_name': 'DX_m07_omega13_0050b_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_music_background = Sound(root=self, name='music_background', sound='rtc_m07_the_hitman', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_background, {'template_name': 'rtc_m07_the_hitman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_Light_SPACE_background = Light(root=self, name='Light_SPACE_background', point_name='Light_SPACE_background', extra_name='', light_group=7, diffuse=[1, 0.8823529, 0.7058824], ambient=[0.05, 0.05, 0.05], direction=[-1, 0, 1], light_type='L_DIRECT', on=True, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_SPACE_background, {'template_name': '', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [1, 0.8823529, 0.7058824], 'specular': [1, 1, 1], 'ambient': [0.05, 0.05, 0.05], 'direction': [-1, 0, 1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_SPACE_playership = Light(root=self, name='Light_SPACE_playership', point_name='Light_SPACE_playership', extra_name='', light_group=4, diffuse=[1, 0.8823529, 0.7058824], ambient=[0.05, 0.05, 0.05], direction=[-1, 0, -1], light_type='L_DIRECT', on=True, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_SPACE_playership, {'template_name': '', 'lt_grp': 4, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [1, 0.8823529, 0.7058824], 'specular': [1, 1, 1], 'ambient': [0.05, 0.05, 0.05], 'direction': [-1, 0, -1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_SPACE_playership_shield_fx = Light(root=self, name='Light_SPACE_playership_shield_fx', point_name='Light_SPACE_playership_shield_fx', extra_name='', light_group=4, diffuse=[0, 0, 0], ambient=[0, 0, 0], direction=[-1, 0, -1], light_type='L_DIRECT', on=False, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_SPACE_playership_shield_fx, {'template_name': '', 'lt_grp': 4, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'N', 'color': [255, 255, 255], 'diffuse': [0, 0, 0], 'specular': [1, 1, 1], 'ambient': [0, 0, 0], 'direction': [-1, 0, -1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_SPACE_rockford_intro = Light(root=self, name='Light_SPACE_rockford_intro', point_name='Light_SPACE_rockford_intro', extra_name='', light_group=5, diffuse=[1, 0.8823529, 0.7058824], ambient=[0.05, 0.05, 0.05], direction=[-1, 0, -1], light_type='L_DIRECT', on=True, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_SPACE_rockford_intro, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [1, 0.8823529, 0.7058824], 'specular': [1, 1, 1], 'ambient': [0.05, 0.05, 0.05], 'direction': [-1, 0, -1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_SPACE_rockford_front = Light(root=self, name='Light_SPACE_rockford_front', point_name='Light_SPACE_rockford_front', extra_name='', light_group=5, diffuse=[1, 0.8823529, 0.7058824], ambient=[0.05, 0.05, 0.05], direction=[-1, 0, 1], light_type='L_DIRECT', on=False, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_SPACE_rockford_front, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'N', 'color': [255, 255, 255], 'diffuse': [1, 0.8823529, 0.7058824], 'specular': [1, 1, 1], 'ambient': [0.05, 0.05, 0.05], 'direction': [-1, 0, 1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_ROOM = Light(root=self, name='Light_ROOM', point_name='Light_ROOM', extra_name='', light_group=0, diffuse=[0.6, 0.6, 0.6], ambient=[0.15, 0.15, 0.15], direction=[0, 0, -1], light_type='L_DIRECT', on=True, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_ROOM, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.6, 0.6, 0.6], 'specular': [1, 1, 1], 'ambient': [0.15, 0.15, 0.15], 'direction': [0, 0, -1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_shield_damage = Light(root=self, name='Light_shield_damage', point_name='Light_shield_damage', extra_name='', light_group=0, diffuse=[0, 0, 0], ambient=[0, 0, 0], direction=[0, 0, -1], light_type='L_DIRECT', on=True, range=5000, cutoff=98.999977, theta=90, color=[255, 255, 255], attenuation=[1, 0, 0])
        preserve_entity(obj_Light_shield_damage, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0, 0, 0], 'specular': [0, 0, 0], 'ambient': [0, 0, 0], 'direction': [0, 0, -1], 'range': 5000, 'cutoff': 98.999977, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 0]}})
        obj_Light_ROOM_backside = Light(root=self, name='Light_ROOM_backside', point_name='Light_ROOM_backside', extra_name='', light_group=0, diffuse=[0.5, 0.5, 0.5], ambient=[0.25, 0.25, 0.25], direction=[0, 0, 1], light_type='L_DIRECT', on=False, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_ROOM_backside, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'N', 'color': [255, 255, 255], 'diffuse': [0.5, 0.5, 0.5], 'specular': [1, 1, 1], 'ambient': [0.25, 0.25, 0.25], 'direction': [0, 0, 1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_ROOM_backside_nomad_light = Light(root=self, name='Light_ROOM_backside_nomad_light', point_name='Light_ROOM_backside_nomad_light', extra_name='', light_group=0, diffuse=[0.6, 0.5, 0.9], ambient=[0.6, 0.1, 0.8], direction=[0, 0, 1], light_type='L_DIRECT', on=False, range=2000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_ROOM_backside_nomad_light, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'N', 'color': [255, 255, 255], 'diffuse': [0.6, 0.5, 0.9], 'specular': [1, 1, 1], 'ambient': [0.6, 0.1, 0.8], 'direction': [0, 0, 1], 'range': 2000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Light_gun01_flash = Light(root=self, name='Light_gun01_flash', point_name='Light_gun01_flash', extra_name='', light_group=5, diffuse=[0, 0, 0], ambient=[0, 0, 0], direction=[0, 0, 1], light_type='L_POINT', on=True, range=3, cutoff=98.999977, theta=90, color=[255, 255, 255], attenuation=[0.8000000119, 0, 0.0399999991])
        preserve_entity(obj_Light_gun01_flash, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0, 0, 0], 'specular': [0, 0, 0], 'ambient': [0, 0, 0], 'direction': [0, 0, 1], 'range': 3, 'cutoff': 98.999977, 'type': 'L_POINT', 'theta': 90, 'atten': [0.8000000119, 0, 0.0399999991]}})
        obj_Light_gun02_flash = Light(root=self, name='Light_gun02_flash', point_name='Light_gun02_flash', extra_name='', light_group=5, diffuse=[0, 0, 0], ambient=[0, 0, 0], direction=[0, 0, 1], light_type='L_POINT', on=True, range=3, cutoff=98.999977, theta=90, color=[255, 255, 255], attenuation=[0.8000000119, 0, 0.0399999991])
        preserve_entity(obj_Light_gun02_flash, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0, 0, 0], 'specular': [0, 0, 0], 'ambient': [0, 0, 0], 'direction': [0, 0, 1], 'range': 3, 'cutoff': 98.999977, 'type': 'L_POINT', 'theta': 90, 'atten': [0.8000000119, 0, 0.0399999991]}})
        obj_Ship_l_elite_1_engine_li_small_1 = SpatialSound(root=self, name='Ship_l_elite_1_engine_li_small_1', sound='engine_br_small', attenuation=-3, dmin=40, dmax=50, priority=None)
        preserve_entity(obj_Ship_l_elite_1_engine_li_small_1, {'template_name': 'engine_br_small', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'SPATIAL', 'audioprops': {'attenuation': -3, 'pan': 0, 'dmin': 40, 'dmax': 50, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_blackhole_ring = Alchemy(root=self, name='blackhole_ring', particles='Intro_volcanoplanet_sun', point_name='blackhole_ring', sparam=0)
        preserve_entity(obj_blackhole_ring, {'template_name': 'Intro_volcanoplanet_sun', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'psysprops': {'sparam': 0}})
        obj_blackhole_lighting = Alchemy(root=self, name='blackhole_lighting', particles='gf_neutronstar', point_name='blackhole_lighting', sparam=0)
        preserve_entity(obj_blackhole_lighting, {'template_name': 'gf_neutronstar', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'psysprops': {'sparam': 0}})
        obj_planet_1 = Asset_obj_planet_1(root=self, name='planet_1', light_group=7, init_point='planet_1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_planet_1, {'template_name': 'planet_mercury_5000', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Solar'}})
        obj_blackhole = Asset_obj_blackhole(root=self, name='blackhole', light_group=7, init_point='blackhole', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_blackhole, {'template_name': 'BlackHoleSun', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Solar'}})
        obj_gatling = Sound(root=self, name='gatling', sound='rtc_m07_gatling', attenuation=-15, dmin=490, dmax=500, priority='Story_Sound_1')
        preserve_entity(obj_gatling, {'template_name': 'rtc_m07_gatling', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 490, 'dmax': 500, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_shield1 = Sound(root=self, name='shield1', sound='sh_li01', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_shield1, {'template_name': 'sh_li01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_shield2 = Sound(root=self, name='shield2', sound='sh_li02', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_shield2, {'template_name': 'sh_li02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_shield3 = Sound(root=self, name='shield3', sound='sh_li03', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_shield3, {'template_name': 'sh_li03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_shield_offline = Sound(root=self, name='shield_offline', sound='cruise_disrupt', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_shield_offline, {'template_name': 'cruise_disrupt', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_transponder_reveal = Sound(root=self, name='transponder_reveal', sound='cloak_no_gunboat', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_transponder_reveal, {'template_name': 'cloak_no_gunboat', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_transponder_activates = Sound(root=self, name='transponder_activates', sound='cloak_no_battleship', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_transponder_activates, {'template_name': 'cloak_no_battleship', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_missile_rolling = Sound(root=self, name='missile_rolling', sound='tractor_interrupted', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_missile_rolling, {'template_name': 'tractor_interrupted', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_missile_loaded = Sound(root=self, name='missile_loaded', sound='tractor_loot_grabbed', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_missile_loaded, {'template_name': 'tractor_loot_grabbed', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_missile_launch = Sound(root=self, name='missile_launch', sound='fire_missile_homing', attenuation=-1, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_missile_launch, {'template_name': 'fire_missile_homing', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -1, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_missile_travel = SpatialSound(root=self, name='missile_travel', sound='engine_thruster', attenuation=-50, dmin=0.5, dmax=1, priority=None)
        preserve_entity(obj_missile_travel, {'template_name': 'engine_thruster', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'SPATIAL', 'audioprops': {'attenuation': -50, 'pan': 0, 'dmin': 0.5, 'dmax': 1, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_missile_travel2 = SpatialSound(root=self, name='missile_travel2', sound='engine_thruster', attenuation=-15, dmin=0.5, dmax=1, priority=None)
        preserve_entity(obj_missile_travel2, {'template_name': 'engine_thruster', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'SPATIAL', 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 0.5, 'dmax': 1, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_click1 = Sound(root=self, name='click1', sound='sfx_ui_react_accept02', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_click1, {'template_name': 'sfx_ui_react_accept02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_click2 = Sound(root=self, name='click2', sound='sfx_ui_react_data01', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_click2, {'template_name': 'sfx_ui_react_data01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_click3 = Sound(root=self, name='click3', sound='sfx_ui_react_data02', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_click3, {'template_name': 'sfx_ui_react_data02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_init_systems = Sound(root=self, name='init_systems', sound='sfx_ui_react_request01', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_init_systems, {'template_name': 'sfx_ui_react_request01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_system_error1 = Sound(root=self, name='system_error1', sound='sfx_ui_react_accept01', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_system_error1, {'template_name': 'sfx_ui_react_accept01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_system_error2 = Sound(root=self, name='system_error2', sound='sfx_ui_react_denied01', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_system_error2, {'template_name': 'sfx_ui_react_denied01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_system_success = Sound(root=self, name='system_success', sound='sfx_ui_react_processing01', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_system_success, {'template_name': 'sfx_ui_react_processing01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_fx_player_trapped = Alchemy(root=self, name='fx_player_trapped', particles='ms6_trapped', point_name='fx_player_trapped', sparam=0)
        preserve_entity(obj_fx_player_trapped, {'template_name': 'ms6_trapped', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_shield_offline = Alchemy(root=self, name='fx_shield_offline', particles='gf_li_bang01', point_name='fx_shield_offline', sparam=0)
        preserve_entity(obj_fx_shield_offline, {'template_name': 'gf_li_bang01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_crystal_light = Alchemy(root=self, name='fx_crystal_light', particles='ms7_crystal_fx', point_name='fx_crystal_light', sparam=0)
        preserve_entity(obj_fx_crystal_light, {'template_name': 'ms7_crystal_fx', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_crystal_touch = Alchemy(root=self, name='fx_crystal_touch', particles='ms7_crystal_touch', point_name='fx_crystal_touch', sparam=0)
        preserve_entity(obj_fx_crystal_touch, {'template_name': 'ms7_crystal_touch', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_crystal_touch_mega_effect = Alchemy(root=self, name='fx_crystal_touch_mega_effect', particles='no_cloakeffect05', point_name='fx_crystal_touch_mega_effect', sparam=0)
        preserve_entity(obj_fx_crystal_touch_mega_effect, {'template_name': 'no_cloakeffect05', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_crystal_touch_mega_effect2 = Alchemy(root=self, name='fx_crystal_touch_mega_effect2', particles='no_cloakeffect05', point_name='fx_crystal_touch_mega_effect2', sparam=0)
        preserve_entity(obj_fx_crystal_touch_mega_effect2, {'template_name': 'no_cloakeffect05', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_player_transponding = Alchemy(root=self, name='fx_player_transponding', particles='no_cloakeffect05', point_name='fx_player_transponding', sparam=0)
        preserve_entity(obj_fx_player_transponding, {'template_name': 'no_cloakeffect05', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_player_transponding2 = Alchemy(root=self, name='fx_player_transponding2', particles='gf_nomad_kernel', point_name='fx_player_transponding2', sparam=0)
        preserve_entity(obj_fx_player_transponding2, {'template_name': 'gf_nomad_kernel', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_player_transponding3 = Alchemy(root=self, name='fx_player_transponding3', particles='no_cloakeffect05', point_name='fx_player_transponding3', sparam=0)
        preserve_entity(obj_fx_player_transponding3, {'template_name': 'no_cloakeffect05', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_the_stars = Asset_obj_the_stars(root=self, name='the_stars', light_group=110, init_point='the_stars', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_the_stars, {'template_name': 'new_generic', 'lt_grp': 110, 'srt_grp': -100, 'usr_flg': 1, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_the_background = Asset_obj_the_background(root=self, name='the_background', light_group=110, init_point='the_background', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_the_background, {'template_name': 'om13_nebula', 'lt_grp': 110, 'srt_grp': -100, 'usr_flg': 1, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_fx_rockford_engine01 = Alchemy(root=self, name='fx_rockford_engine01', particles='gf_br_smallengine02_fire', point_name='fx_rockford_engine01', sparam=0)
        preserve_entity(obj_fx_rockford_engine01, {'template_name': 'gf_br_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_rockford_engine02 = Alchemy(root=self, name='fx_rockford_engine02', particles='gf_br_smallengine02_fire', point_name='fx_rockford_engine02', sparam=0)
        preserve_entity(obj_fx_rockford_engine02, {'template_name': 'gf_br_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun01 = Asset_obj_gun01(root=self, name='gun01', light_group=5, init_point='gun01', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_gun01, {'template_name': 'rtcprop_weapons_br_mass_driver', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment'}})
        obj_gun02 = Asset_obj_gun02(root=self, name='gun02', light_group=5, init_point='gun02', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_gun02, {'template_name': 'rtcprop_weapons_br_mass_driver', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment'}})
        obj_launcher01 = Asset_obj_launcher01(root=self, name='launcher01', light_group=5, init_point='launcher01', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_launcher01, {'template_name': 'rtcprop_weapons_br_slugger_launcher', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment'}})
        obj_cockpit_gun01 = Asset_obj_cockpit_gun01(root=self, name='cockpit_gun01', light_group=5, init_point='cockpit_gun01', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_cockpit_gun01, {'template_name': 'rtcprop_weapons_br_mass_driver', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment'}})
        obj_cockpit_gun02 = Asset_obj_cockpit_gun02(root=self, name='cockpit_gun02', light_group=5, init_point='cockpit_gun02', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_cockpit_gun02, {'template_name': 'rtcprop_weapons_br_mass_driver', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment'}})
        obj_missile01 = Asset_obj_missile01(root=self, name='missile01', light_group=5, init_point='missile01', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_missile01, {'template_name': 'rtcprop_weapons_br_slugger_missile', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_missile02 = Asset_obj_missile02(root=self, name='missile02', light_group=5, init_point='missile02', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_missile02, {'template_name': 'rtcprop_weapons_br_slugger_missile', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_fx_missile = Alchemy(root=self, name='fx_missile', particles='li_missile01_drive', point_name='fx_missile', sparam=0)
        preserve_entity(obj_fx_missile, {'template_name': 'li_missile01_drive', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_missile_alt = Alchemy(root=self, name='fx_missile_alt', particles='li_missile01_drive', point_name='fx_missile_alt', sparam=0)
        preserve_entity(obj_fx_missile_alt, {'template_name': 'li_missile01_drive', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun01_proj_01 = Alchemy(root=self, name='gun01_proj_01', particles='rtc_sanctumgun_proj', point_name='gun01_proj_01', sparam=0)
        preserve_entity(obj_gun01_proj_01, {'template_name': 'rtc_sanctumgun_proj', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun01_proj_02 = Alchemy(root=self, name='gun01_proj_02', particles='rtc_sanctumgun_proj', point_name='gun01_proj_02', sparam=0)
        preserve_entity(obj_gun01_proj_02, {'template_name': 'rtc_sanctumgun_proj', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun02_proj_01 = Alchemy(root=self, name='gun02_proj_01', particles='rtc_sanctumgun_proj', point_name='gun02_proj_01', sparam=0)
        preserve_entity(obj_gun02_proj_01, {'template_name': 'rtc_sanctumgun_proj', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun02_proj_02 = Alchemy(root=self, name='gun02_proj_02', particles='rtc_sanctumgun_proj', point_name='gun02_proj_02', sparam=0)
        preserve_entity(obj_gun02_proj_02, {'template_name': 'rtc_sanctumgun_proj', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_flash_01 = Alchemy(root=self, name='gun_flash_01', particles='rtc_sanctumgun_flash', point_name='gun_flash_01', sparam=0)
        preserve_entity(obj_gun_flash_01, {'template_name': 'rtc_sanctumgun_flash', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_flash_02 = Alchemy(root=self, name='gun_flash_02', particles='rtc_sanctumgun_flash', point_name='gun_flash_02', sparam=0)
        preserve_entity(obj_gun_flash_02, {'template_name': 'rtc_sanctumgun_flash', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_fireblast01 = Alchemy(root=self, name='gun_fireblast01', particles='gf_msn7_gunfire', point_name='gun_fireblast01', sparam=0)
        preserve_entity(obj_gun_fireblast01, {'template_name': 'gf_msn7_gunfire', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_fireblast02 = Alchemy(root=self, name='gun_fireblast02', particles='gf_msn7_gunfire', point_name='gun_fireblast02', sparam=0)
        preserve_entity(obj_gun_fireblast02, {'template_name': 'gf_msn7_gunfire', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_impact_01 = Alchemy(root=self, name='gun_impact_01', particles='gf_li_shield01', point_name='gun_impact_01', sparam=0)
        preserve_entity(obj_gun_impact_01, {'template_name': 'gf_li_shield01', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_impact_02 = Alchemy(root=self, name='gun_impact_02', particles='gf_li_shield01', point_name='gun_impact_02', sparam=0)
        preserve_entity(obj_gun_impact_02, {'template_name': 'gf_li_shield01', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_impact_03 = Alchemy(root=self, name='gun_impact_03', particles='gf_li_shield01', point_name='gun_impact_03', sparam=0)
        preserve_entity(obj_gun_impact_03, {'template_name': 'gf_li_shield01', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_impact_04 = Alchemy(root=self, name='gun_impact_04', particles='gf_li_shield01', point_name='gun_impact_04', sparam=0)
        preserve_entity(obj_gun_impact_04, {'template_name': 'gf_li_shield01', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_gun_impact_05 = Alchemy(root=self, name='gun_impact_05', particles='gf_li_shield01', point_name='gun_impact_05', sparam=0)
        preserve_entity(obj_gun_impact_05, {'template_name': 'gf_li_shield01', 'lt_grp': 0, 'srt_grp': 12, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_rockford = Character(root=self, actor=actors.Rockford, light_group=5, init_point='Char_rockford', rotate_from_quat=True, use_ambient=True, floor_height=0.5)
        preserve_entity(obj_Char_rockford, {'template_name': 'rockford', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0.5}, 'userprops': {'actor': 'Rockford', 'category': 'Character'}})
        obj_rockford_chair = Asset_obj_rockford_chair(root=self, name='rockford_chair', light_group=5, init_point='rockford_chair', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_rockford_chair, {'template_name': 'm7_pilot_chair', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_rockford_front = Asset_obj_rockford_front(root=self, name='rockford_front', light_group=5, init_point='rockford_front', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_rockford_front, {'template_name': 'ge_fighter6', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship'}})
        obj_PlayerShip = Asset_obj_PlayerShip(root=self, name='PlayerShip', light_group=4, init_point='PlayerShip', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_PlayerShip, {'template_name': 'PlayerShip', 'lt_grp': 4, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Spaceship'}})
        obj_the_cockpit = Asset_obj_the_cockpit(root=self, name='the_cockpit', light_group=0, init_point='the_cockpit', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_the_cockpit, {'template_name': 'm7_cockpit', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_case = Asset_obj_case(root=self, name='case', light_group=0, init_point='case', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_case, {'template_name': 'm7_case', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_panel = Asset_obj_panel(root=self, name='panel', light_group=0, init_point='panel', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_panel, {'template_name': 'm7_panel', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_crystal = Asset_obj_crystal(root=self, name='crystal', light_group=0, init_point='crystal', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crystal, {'template_name': 'Blixx_crystal', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_tome = Asset_obj_tome(root=self, name='tome', light_group=0, init_point='tome', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_tome, {'template_name': 'tome_075', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_chair = Asset_obj_chair(root=self, name='chair', light_group=0, init_point='chair', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_chair, {'template_name': 'm7_pilot_chair', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_rockford_cockpit = Asset_obj_rockford_cockpit(root=self, name='rockford_cockpit', light_group=5, init_point='rockford_cockpit', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_rockford_cockpit, {'template_name': 'ge_fighter6', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=12, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_pilot = LookAtCamera(root=self, name='cam_trent_pilot', fov=12, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_pilot, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_rockford_gunfire = LookAtCamera(root=self, name='cam_rockford_gunfire', fov=16, farplane=200000, look_duration=70)
        preserve_entity(obj_cam_rockford_gunfire, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 1, 'farplane': 200000}})
        obj_cam_trent_shield_damage = LookAtCamera(root=self, name='cam_trent_shield_damage', fov=12, farplane=200000, look_duration=70)
        preserve_entity(obj_cam_trent_shield_damage, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 200000}})
        obj_cam_shield_destroyed = StaticCamera(root=self, name='cam_shield_destroyed', fov=12, farplane=5000)
        preserve_entity(obj_cam_shield_destroyed, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_player_disappeared = StaticCamera(root=self, name='cam_player_disappeared', fov=12, farplane=5000)
        preserve_entity(obj_cam_player_disappeared, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_launcher_start = LookAtCamera(root=self, name='cam_launcher_start', fov=10, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_launcher_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 10, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_flying_missile = StaticCamera(root=self, name='cam_flying_missile', fov=10, farplane=200000)
        preserve_entity(obj_cam_flying_missile, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 10, 'hvaspect': 1.85, 'nearplane': 1, 'farplane': 200000}})
        obj_cam_flying_missile_near = StaticCamera(root=self, name='cam_flying_missile_near', fov=10, farplane=200000)
        preserve_entity(obj_cam_flying_missile_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 10, 'hvaspect': 1.85, 'nearplane': 1, 'farplane': 200000}})
        obj_cam_trent_lookback = LookAtCamera(root=self, name='cam_trent_lookback', fov=12, farplane=200000, look_duration=70)
        preserve_entity(obj_cam_trent_lookback, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 200000}})
        obj_cam_trent_walkback = LookAtCamera(root=self, name='cam_trent_walkback', fov=10, farplane=200000, look_duration=70)
        preserve_entity(obj_cam_trent_walkback, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 10, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 200000}})
        obj_cam_trent_touch = LookAtCamera(root=self, name='cam_trent_touch', fov=8, farplane=200000, look_duration=70)
        preserve_entity(obj_cam_trent_touch, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 8, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 200000}})
        obj_cam_trent_missilewatch = LookAtCamera(root=self, name='cam_trent_missilewatch', fov=12, farplane=200000, look_duration=70)
        preserve_entity(obj_cam_trent_missilewatch, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 200000}})
        t = 0
        # source event 0, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='planet_1', angle=125, axis='Y_AXIS', duration=100, smooth=False)
        # source event 1, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='planet_1', angle=450, axis='Z_AXIS', duration=100, smooth=False)
        # source event 2, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='blackhole_ring', duration=36000)
        # source event 3, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='blackhole_lighting', duration=36000)
        # source event 4, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='planet_1', angle=125, axis='Y_AXIS', duration=100, smooth=False)
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='rockford_cockpit', anim='Sc_launch extend', duration=2, time_scale=35, start_time=0, loop=False, trans_time=None)
        # source event 11, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_shield_destroyed', 'PlayerShip'], duration=70, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpPilot', target_type='HARDPOINT', flags='LOOK_AT')
        # source event 12, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_player_disappeared', 'automarker_cam_player_disappeared_marker'], duration=70, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpPilot', target_type='HARDPOINT', flags='LOOK_AT')
        # source event 18, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='gun01', parent_name='rockford_front', duration=1000, target_hardpoint='HpConnect', parent_hardpoint='HpWeapon04')
        # source event 19, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='gun02', parent_name='rockford_front', duration=1000, target_hardpoint='HpConnect', parent_hardpoint='HpWeapon03')
        # source event 20, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='launcher01', parent_name='rockford_front', duration=1000, target_hardpoint='HpConnect', parent_hardpoint='HpWeapon02')
        # source event 21, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine01', 'rockford_front'], duration=1555, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 22, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine02', 'rockford_front'], duration=1555, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine02', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 23, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_rockford_engine01', duration=36000)
        # source event 24, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_rockford_engine02', duration=36000)
        # source event 25, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine01'], duration=0.5, psysprops={'sparam': 0.4})
        # source event 26, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine02'], duration=0.5, psysprops={'sparam': 0.4})
        # source event 27, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['rockford_chair', 'rockford_front'], duration=1555, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpPilot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 28, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=0.001, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 30, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_player_trapped', duration=55)
        # source event 31, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_player_trapped', 'PlayerShip'], duration=260, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 34, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 41, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Ship_l_elite_1_engine_li_small_1', 'rockford_front'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 42, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='Ship_l_elite_1_engine_li_small_1', duration=7, start_time=0, loop=True)
        # source event 72, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun_flash_01', 'gun01'], duration=11111, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 73, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun_flash_02', 'gun02'], duration=11111, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 74, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun01_proj_01', 'gun01'], duration=11111, offset=[0, 0, -4], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 75, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun01_proj_02', 'gun01'], duration=11111, offset=[0, 0, -4], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 76, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun02_proj_01', 'gun02'], duration=11111, offset=[0, 0, -4], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 77, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun02_proj_02', 'gun02'], duration=11111, offset=[0, 0, -4], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        t += 0.01
        # source event 29, 0.01s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Char_rockford', 'rockford_front'], duration=1555, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpPilot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        t += 0.09
        # source event 33, 0.1s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        main_group.append_time(1)

        # Line 15: source 1s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        voice_sound = self.lookup_single_sound(15)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        main_group.append_time(3)

        # Line 20: source 4s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        voice_sound = self.lookup_single_sound(20)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        t += 1
        # source event 36, 5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='rockford_front', target_name='automarker_mrk_rockford_fly_forward', duration=4, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 37, 5s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine01'], duration=9, psysprops={'sparam': 1})
        # source event 38, 5s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine02'], duration=9, psysprops={'sparam': 1})
        t += 2
        # source event 43, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_pilot')
        # source event 44, 7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s020x_VanPelt_XC_CHRF_TYPE_000DN_06, duration=20, time_scale=1.6, start_time=0.2, loop=True, trans_time=None)
        main_group.append_time(3.5)

        # Line 30: source 7.5s; allocated facial window 15s.
        t = 0
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-15.0)

        # Line 35: source 7.5s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        voice_sound = self.lookup_single_sound(35)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        t += 0.2
        # source event 49, 7.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 54, 8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_SPACE_rockford_intro', duration=0, smooth=False, on=False)
        # source event 60, 8s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine01'], duration=2, psysprops={'sparam': 0.5})
        # source event 61, 8s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine02'], duration=2, psysprops={'sparam': 0.5})
        t += 0.2
        # source event 353, 8.2s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_background', duration=1, attenuation=0)
        t += 0.02
        # source event 352, 8.22s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_background', duration=555, start_time=0, loop=True)
        t += 0.18
        # source event 50, 8.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click2', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 55, 9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_SPACE_rockford_front', duration=0, smooth=False, on=True)
        t += 0.1
        # source event 51, 9.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click3', duration=5, start_time=0, loop=False)
        # source event 64, 9.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='rockford_front', target_name='automarker_mrk_rockford_standing_before_fire', duration=0.001, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.05
        # source event 65, 9.15s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['rockford_front', 'automarker_mrk_rockford_ready_to_fire_looking_point'], duration=1500, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        t += 0.05
        # source event 66, 9.2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mrk_rockford_ready_to_fire_looking_point', target_name='automarker_mrk_rockford_ready_to_fire_playerpoint', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 67, 9.2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='rockford_front', target_name='automarker_mrk_rockford_ready_to_fire', duration=6.3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.6
        # source event 52, 9.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 47, 10s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='DX_m07_omega13_0030_trent', duration=0.01, attenuation=-100)
        # source event 48, 10s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='DX_m07_omega13_0035_trent', duration=0.01, attenuation=0)
        # source event 56, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_rockford_gunfire')
        # source event 57, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_rockford_gunfire', target_name='automarker_cam_rockford_gunfire_pos2', duration=6.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 58, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_rockford_gunfire_focus', target_name='automarker_cam_rockford_gunfire_marker_pos2', duration=5.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 68, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='rockford_front', anim='Sc_launch extend', duration=221, time_scale=0.9, start_time=4, loop=False, trans_time=None)
        # source event 196, 10s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='cockpit_gun01', parent_name='rockford_cockpit', duration=1000, target_hardpoint='HpConnect', parent_hardpoint='HpWeapon04')
        # source event 197, 10s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='cockpit_gun02', parent_name='rockford_cockpit', duration=1000, target_hardpoint='HpConnect', parent_hardpoint='HpWeapon03')
        main_group.append_time(4.5)

        # Line 40: source 12s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        voice_sound = self.lookup_single_sound(40)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 62, 12s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine01'], duration=2, psysprops={'sparam': 0.2})
        # source event 63, 12s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_rockford_engine02'], duration=2, psysprops={'sparam': 0.2})
        # source event 70, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='gun01', anim='Sc_fire', duration=9, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 71, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='gun02', anim='Sc_fire', duration=9, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 198, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='cockpit_gun01', anim='Sc_fire', duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 199, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='cockpit_gun02', anim='Sc_fire', duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 200, 12s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun_fireblast01', 'cockpit_gun01'], duration=11111, offset=[0, 0, -2], up='NEG_Z_AXIS', front='NEG_Y_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 201, 12s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_fireblast01', duration=10)
        # source event 202, 12s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun_fireblast01', 'Char_trent'], duration=70, offset=[0, 0, 0], up='NEG_Z_AXIS', front='Y_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 203, 12s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun_fireblast02', 'cockpit_gun02'], duration=11111, offset=[0, 0, -2], up='NEG_Z_AXIS', front='NEG_Y_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 204, 12s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_fireblast02', duration=10)
        # source event 205, 12s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gun_fireblast02', 'Char_trent'], duration=70, offset=[0, 0, 0], up='NEG_Z_AXIS', front='Y_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        t += 1.5
        # source event 69, 13.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='gatling', duration=2.5, start_time=0, loop=False)
        t += 0.5
        # source event 78, 14s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_flash_01', duration=6)
        # source event 79, 14s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_flash_02', duration=6)
        # source event 80, 14s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 104, 14s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 128, 14s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Light_gun01_flash', 'gun01'], duration=10, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 129, 14s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Light_gun02_flash', 'gun02'], duration=10, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION')
        # source event 130, 14s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        # source event 163, 14s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        t += 0.1
        # source event 131, 14.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.8, 0.8, 0.8], ambient=[0.8, 0.8, 0.8])
        # source event 164, 14.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.8, 0.8, 0.8], ambient=[0.8, 0.8, 0.8], lt_range=3)
        t += 0.1
        # source event 132, 14.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 165, 14.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        t += 0.05
        # source event 81, 14.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 105, 14.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 133, 14.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 166, 14.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.1
        # source event 134, 14.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 167, 14.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0], lt_range=5)
        t += 0.1
        # source event 82, 14.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 106, 14.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 135, 14.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        # source event 168, 14.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        t += 0.1
        # source event 136, 14.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=4)
        # source event 169, 14.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        t += 0.1
        # source event 137, 14.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 170, 14.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.05
        # source event 83, 14.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 107, 14.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 138, 14.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 171, 14.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        t += 0.1
        # source event 139, 14.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.8, 0.8, 0.8], ambient=[0.8, 0.8, 0.8])
        # source event 172, 14.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.8, 0.8, 0.8], ambient=[0.8, 0.8, 0.8])
        t += 0.1
        # source event 84, 15s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 108, 15s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 140, 15s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 173, 15s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=4)
        # source event 206, 15s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM', duration=0, smooth=False, diffuse=[0.1, 0.1, 0.1], ambient=[0.05, 0.05, 0.05])
        t += 0.1
        # source event 141, 15.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0], lt_range=3)
        # source event 174, 15.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        t += 0.1
        # source event 142, 15.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[0, 0, 0])
        # source event 175, 15.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        t += 0.05
        # source event 85, 15.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 109, 15.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 143, 15.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        # source event 176, 15.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.1
        # source event 144, 15.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 177, 15.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        t += 0.1
        # source event 86, 15.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 110, 15.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 145, 15.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 178, 15.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.1
        # source event 146, 15.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        # source event 179, 15.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=4)
        t += 0.1
        # source event 147, 15.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.3, 0.3, 0.3], ambient=[0.3, 0.3, 0.3])
        # source event 180, 15.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.3, 0.3, 0.3], ambient=[0.3, 0.3, 0.3], lt_range=3)
        t += 0.05
        # source event 87, 15.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 111, 15.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 148, 15.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=4)
        # source event 181, 15.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        t += 0.1
        # source event 149, 15.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 182, 15.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.1
        # source event 88, 16s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 112, 16s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 150, 16s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 183, 16s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        # source event 208, 16s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        # source event 222, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_shield_damage')
        # source event 223, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_shield_damage', target_name='automarker_cam_trent_shield_damage_pos2', duration=2, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 224, 16s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_01', duration=60)
        # source event 239, 16s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield1', duration=60, start_time=0, loop=False)
        t += 0.1
        # source event 151, 16.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        # source event 184, 16.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.1
        # source event 152, 16.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 185, 16.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        t += 0.05
        # source event 89, 16.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 113, 16.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 153, 16.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0], lt_range=3)
        # source event 186, 16.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 209, 16.3s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.25, 0.3, 0.5], ambient=[0.25, 0.3, 0.5])
        t += 0.1
        # source event 154, 16.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1])
        # source event 187, 16.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        t += 0.1
        # source event 90, 16.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 114, 16.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 155, 16.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.8, 0.8, 0.8], ambient=[0.8, 0.8, 0.8])
        # source event 188, 16.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.8, 0.8, 0.8], ambient=[0.8, 0.8, 0.8], lt_range=3)
        # source event 225, 16.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_02', duration=60)
        # source event 240, 16.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield2', duration=60, start_time=0, loop=False)
        t += 0.1
        # source event 156, 16.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 189, 16.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 210, 16.6s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        t += 0.1
        # source event 157, 16.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 190, 16.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.05
        # source event 91, 16.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 115, 16.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 158, 16.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 191, 16.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 226, 16.8s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_03', duration=60)
        # source event 241, 16.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield3', duration=60, start_time=0, loop=False)
        t += 0.1
        # source event 159, 16.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        # source event 192, 16.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 211, 16.9s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.25, 0.3, 0.5], ambient=[0.25, 0.3, 0.5])
        t += 0.1
        # source event 92, 17s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 116, 17s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 160, 17s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[1, 1, 1], ambient=[1, 1, 1], lt_range=5)
        # source event 193, 17s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        t += 0.1
        # source event 161, 17.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5], lt_range=3)
        # source event 194, 17.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, diffuse=[0.5, 0.5, 0.5], ambient=[0.5, 0.5, 0.5])
        t += 0.1
        # source event 162, 17.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun01_flash', duration=0.05, smooth=False, on=False)
        # source event 195, 17.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_gun02_flash', duration=0.05, smooth=False, on=False)
        # source event 212, 17.2s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        t += 0.05
        # source event 93, 17.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 117, 17.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 227, 17.3s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_04', duration=60)
        # source event 242, 17.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield2', duration=60, start_time=0, loop=False)
        t += 0.2
        # source event 94, 17.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 118, 17.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 213, 17.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.25, 0.3, 0.5], ambient=[0.25, 0.3, 0.5])
        t += 0.2
        # source event 228, 17.7s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_05', duration=60)
        # source event 243, 17.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield1', duration=60, start_time=0, loop=False)
        t += 0.05
        # source event 95, 17.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 119, 17.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 214, 17.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        main_group.append_time(6)

        # Line 50: source 18s; allocated facial window 15s.
        t = 0
        # source event 96, 18s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 120, 18s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 229, 18s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_01', duration=60)
        # source event 244, 18s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield1', duration=60, start_time=0, loop=False)
        # source event 250, 18s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 251, 18s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_pilot')
        t += 0.1
        # source event 215, 18.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.25, 0.3, 0.5], ambient=[0.25, 0.3, 0.5])
        t += 0.15
        # source event 97, 18.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 121, 18.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.25
        # source event 98, 18.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 122, 18.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        # source event 216, 18.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        # source event 230, 18.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_02', duration=60)
        # source event 245, 18.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield2', duration=60, start_time=0, loop=False)
        t += 0.25
        # source event 99, 18.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 123, 18.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 217, 18.8s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.25, 0.3, 0.5], ambient=[0.25, 0.3, 0.5])
        # source event 231, 18.8s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_03', duration=60)
        # source event 246, 18.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield3', duration=60, start_time=0, loop=False)
        t += 0.2
        # source event 100, 19s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 124, 19s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        t += 0.1
        # source event 218, 19.1s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        t += 0.15
        # source event 101, 19.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 125, 19.25s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.05
        # source event 232, 19.3s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_04', duration=60)
        # source event 247, 19.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield2', duration=60, start_time=0, loop=False)
        t += 0.1
        # source event 219, 19.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.25, 0.3, 0.5], ambient=[0.25, 0.3, 0.5])
        t += 0.1
        # source event 102, 19.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_01', duration=0.5)
        # source event 126, 19.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_01', duration=0.5)
        t += 0.2
        # source event 220, 19.7s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.3, smooth=True, diffuse=[0.5, 0.6, 1], ambient=[0.5, 0.6, 1])
        # source event 233, 19.7s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_05', duration=60)
        # source event 248, 19.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield1', duration=60, start_time=0, loop=False)
        t += 0.05
        # source event 103, 19.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun01_proj_02', duration=0.5)
        # source event 127, 19.75s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun02_proj_02', duration=0.5)
        t += 0.25
        # source event 221, 20s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_shield_damage', duration=0.5, smooth=True, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        # source event 234, 20s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_01', duration=60)
        # source event 249, 20s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield1', duration=60, start_time=0, loop=False)
        # source event 259, 20s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_shield_offline', 'PlayerShip'], duration=260, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 265, 20s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_mrk_missile01_start_pos', 'launcher01'], duration=1, offset=[0, 0, 0.7], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 266, 20s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_mrk_missile01_ready_to_load', 'launcher01'], duration=1, offset=[0, 0, -0.5], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 267, 20s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_mrk_missile01_final_hp', 'launcher01'], duration=15, offset=[0, 0, -0.7], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 268, 20s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_mrk_missile01_firepoint', 'launcher01'], duration=1, offset=[0, 0, -220], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        t += 0.2
        # source event 254, 20.2s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_shield_destroyed')
        t += 0.2
        # source event 255, 20.4s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_SPACE_playership_shield_fx', duration=0, smooth=False, on=True, diffuse=[0.8, 0.9, 1], ambient=[0.8, 0.9, 1])
        # source event 258, 20.4s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_shield_offline', duration=60)
        # source event 260, 20.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='shield_offline', duration=5, start_time=0, loop=False)
        t += 0.01
        # source event 256, 20.41s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_SPACE_playership_shield_fx', duration=0.75, smooth=False, diffuse=[0, 0, 0], ambient=[0, 0, 0])
        t += 0.09
        # source event 235, 20.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_02', duration=60)
        t += 0.3
        # source event 236, 20.8s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_03', duration=60)
        t += 0.2
        # source event 207, 21s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM', duration=0, smooth=False, diffuse=[0.6, 0.6, 0.6], ambient=[0.3, 0.3, 0.3])
        t += 0.3
        # source event 237, 21.3s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_04', duration=60)
        t += 0.4
        # source event 238, 21.7s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gun_impact_05', duration=60)
        t += 0.3
        # source event 257, 22s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_SPACE_playership_shield_fx', duration=0, smooth=False, on=False)
        # source event 262, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_launcher_start', target_name='automarker_cam_launcher_start_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 261, 22.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_launcher_start')
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        self.groups.pop('motion_50', None)
        obj_Char_trent.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10)

        # Line 60: source 23s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        voice_sound = self.lookup_single_sound(60)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 263, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_launcher_start_focus', target_name='automarker_cam_launcher_start_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 269, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', target_name='automarker_mrk_missile01_start_pos', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 270, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='launcher01', anim='Sc_br_slugger_launcher', duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 271, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', target_name='automarker_mrk_missile01_final_hp', duration=1.99, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 272, 25.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_rolling', duration=15, start_time=0, loop=False)
        t += 1.3
        # source event 273, 26.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_loaded', duration=15, start_time=0, loop=False)
        t += 0.199
        # source event 274, 26.999s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['missile01', 'launcher01'], duration=2, offset=[0, 0, -0.7], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFire01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        t += 0.001
        # source event 275, 27s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='launcher01', anim='Sc_br_slugger_launcher', duration=1, time_scale=1, start_time=1, loop=False, trans_time=0.25)
        t += 1
        # source event 276, 28s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='crystal', angle=90, axis='X_AXIS', duration=0, smooth=False)
        # source event 278, 28s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_crystal_light', duration=36000)
        # source event 279, 28s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_crystal_light', 'crystal'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 280, 28s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='transponder_reveal', duration=15, start_time=0, loop=False)
        # source event 281, 28s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM', duration=0, smooth=False, on=False)
        # source event 282, 28s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM_backside', duration=0, smooth=False, on=True)
        # source event 283, 28s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_lookback')
        # source event 285, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_270LV_XA_03, duration=113, time_scale=0.75, start_time=0, loop=False, trans_time=None)
        t += 0.01
        # source event 277, 28.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='crystal', angle=35, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.49
        # source event 286, 28.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=90, axis='Y_AXIS', duration=3, smooth=False)
        # source event 287, 28.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='chair', angle=90, axis='Y_AXIS', duration=3, smooth=False)
        t += 3.5
        # source event 284, 32s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_walkback')
        # source event 288, 32s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='chair', angle=90, axis='Y_AXIS', duration=2, smooth=False)
        # source event 289, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_270LV_XA_10, duration=25, time_scale=0.6, start_time=1.8, loop=False, trans_time=1)
        # source event 291, 32s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='crystal', duration=7, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 292, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='panel', target_name='automarker_mrk_panel_open', duration=3, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 293, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='crystal', target_name='automarker_mrk_crystal_open', duration=3, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 294, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='tome', target_name='automarker_mrk_tome_open', duration=3, smooth=True, adjust_pos=True, adjust_orient=False)
        t += 0.5
        # source event 290, 32.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-5, axis='Y_AXIS', duration=1, smooth=False)
        t += 2.5
        # source event 296, 35s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_flying_missile', 'missile01'], duration=70, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 301, 35s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_missile', 'missile01'], duration=25, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpExhaust', target_type='HARDPOINT', flags='POSITION')
        t += 1
        # source event 295, 36s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_flying_missile')
        # source event 297, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', target_name='automarker_mrk_missile01_final_hp', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 298, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', target_name='automarker_mrk_missile01_firepoint', duration=18, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 299, 36s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='launcher01', anim='Sc_br_slugger_launcher', duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 300, 36s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_missile', duration=10)
        # source event 302, 36s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', angle=3600, axis='Z_AXIS', duration=25, smooth=False)
        # source event 303, 36s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['missile_travel', 'missile01'], duration=15, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 304, 36s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_travel', duration=15, start_time=0, loop=True)
        # source event 305, 36s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_launch', duration=5, start_time=0, loop=False)
        # source event 306, 36s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_travel', duration=3, attenuation=-5)
        t += 4
        # source event 311, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile02', target_name='automarker_mrk_missile02_start_pos', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 308, 41s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM_backside', duration=0, smooth=False, on=False)
        # source event 309, 41s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM', duration=0, smooth=False, on=True)
        # source event 319, 41s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_before_touch', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.25
        # source event 320, 41.25s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-35, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.75
        # source event 310, 42s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='crystal', target_name='automarker_mrk_crystal_open2', duration=0, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 318, 42s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_touch_focus', target_name='automarker_cam_trent_touch_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 307, 43s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_travel', duration=5, attenuation=-100)
        # source event 316, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_touch')
        # source event 317, 43s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_touch', target_name='automarker_cam_trent_touch_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 321, 43s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s027x_Trent_XA_STND_000DN_16, duration=8.5, time_scale=0.3, start_time=4, loop=False, trans_time=None)
        t += 1
        # source event 315, 44s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_missile_alt', 'missile02'], duration=25, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpExhaust', target_type='HARDPOINT', flags='POSITION')
        t += 1
        # source event 312, 45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile02', target_name='automarker_mrk_missile02_final_pos', duration=15, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 313, 45s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='missile02', angle=3600, axis='Z_AXIS', duration=25, smooth=False)
        # source event 314, 45s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_missile_alt', duration=25)
        t += 0.5
        # source event 322, 45.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='crystal', parent_name='Char_trent', duration=20, target_hardpoint='HpProp_Connect', parent_hardpoint='HpLeftConnect')
        # source event 323, 45.5s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_crystal_touch', 'crystal'], duration=60, offset=[0, 0.05, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFX', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 324, 45.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_crystal_touch', duration=30)
        # source event 325, 45.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_crystal_touch_mega_effect', duration=30)
        # source event 326, 45.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='transponder_activates', duration=15, start_time=0, loop=False)
        t += 4.5
        # source event 327, 50s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM_backside_nomad_light', duration=0, smooth=False, on=True)
        # source event 328, 50s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM_backside', duration=0, smooth=False, on=False)
        # source event 329, 50s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='Light_ROOM', duration=0, smooth=False, on=False)
        # source event 330, 50s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_crystal_touch_mega_effect2', duration=30)
        # source event 331, 50s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_missilewatch')
        # source event 332, 50s
        CameraAnimEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_missilewatch', duration=3, fov=4, smooth=True)
        # source event 333, 50s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_player_transponding', 'PlayerShip'], duration=260, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 334, 50s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_player_transponding2', 'PlayerShip'], duration=260, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 335, 50s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_player_transponding3', 'PlayerShip'], duration=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        t += 4
        # source event 340, 54s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='cam_flying_missile_near', angle=5, axis='Y_AXIS', duration=0, smooth=False)
        # source event 348, 54s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_missile', 'missile01'], duration=25, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpExhaust', target_type='HARDPOINT', flags='POSITION')
        t += 0.01
        # source event 341, 54.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='cam_flying_missile_near', angle=-3, axis='X_AXIS', duration=0, smooth=False)
        t += 0.49
        # source event 343, 54.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', target_name='automarker_mrk_missile01_fly2_start_pos', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 336, 55s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_player_transponding', duration=235)
        # source event 339, 55s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_flying_missile_near')
        # source event 342, 55s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_flying_missile_near', target_name='automarker_cam_flying_missile_near_pos2', duration=10, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 344, 55s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='missile01', target_name='automarker_mrk_missile01_fly2_final_pos', duration=10, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 345, 55s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['missile_travel2', 'missile01'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 346, 55s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_travel2', duration=55, start_time=0, loop=True)
        # source event 347, 55s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_missile', duration=25)
        t += 2
        # source event 337, 57s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_player_transponding2', duration=2)
        t += 1
        # source event 338, 58s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_player_transponding3', duration=5)
        t += 1
        # source event 349, 59s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_player_disappeared')
        # source event 350, 59s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='PlayerShip', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 351, 62s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='missile_travel', duration=5, attenuation=-100)
        t += 5
        # source event 354, 67s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_background', duration=1, attenuation=-100)
        main_group.append_time(45.0)
        preserve_spatial(self.get_entity('the_stars'), source_basis=[[10, 0, 0], [0, 10, 0], [0, 0, 10]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        restore_dialogue(self)
