"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_Prop_server01(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_server'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_server03(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_server'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_server04(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_server'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_server05(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_server'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera01(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera03(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera05(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_alien05(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_olaf'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera06(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera_tall'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_alien06(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_jarjar'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera07(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera_tall'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_alien07(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_samus'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera08(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_alien08(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_mole'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera09(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera_tall'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_alien09(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_elon'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_barocamera10(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_barocamera_tall'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_monkeyking(actors.Actor):
    NAME = 'monkeyking'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm07_monkeyking'
    GAME_ACTOR = 'monkeyking'


class Asset_obj_Prop_alien01(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_facehugger'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_worm(actors.Actor):
    NAME = 'worm'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'worm'
    GAME_ACTOR = 'worm'


class Actor_obj_Char_assistant(actors.Actor):
    NAME = 'assistant'
    TYPE = 'female'
    CUTSCENE_APPEARANCE = 'm07_female_br_officer'
    GAME_ACTOR = 'Assistant'


class Actor_obj_Char_gunner(actors.Actor):
    NAME = 'gunner'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm07_male_br_officer_gunner'
    GAME_ACTOR = 'Gunner'


class Actor_obj_Char_doorkeeper(actors.Actor):
    NAME = 'doorkeeper'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm07_male_br_officer_marksman'
    GAME_ACTOR = 'Doorkeeper'


class Actor_obj_Char_leader(actors.Actor):
    NAME = 'leader'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm07_male_br_officer'
    GAME_ACTOR = 'Policeleader'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_reward'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_step1 = Sound(root=self, name='step1', sound='fs_fl_stone01', attenuation=-100, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step1, {'template_name': 'fs_fl_stone01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -100, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step2 = Sound(root=self, name='step2', sound='fs_fl_stone02', attenuation=-100, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step2, {'template_name': 'fs_fl_stone02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -100, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step3 = Sound(root=self, name='step3', sound='fs_fl_stone03', attenuation=-100, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step3, {'template_name': 'fs_fl_stone03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -100, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step4 = Sound(root=self, name='step4', sound='fs_fl_stone04', attenuation=-100, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step4, {'template_name': 'fs_fl_stone04', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -100, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step1_cmdr = Sound(root=self, name='step1_cmdr', sound='fs_fl_stone02', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step1_cmdr, {'template_name': 'fs_fl_stone02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step2_cmdr = Sound(root=self, name='step2_cmdr', sound='fs_fl_stone03', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step2_cmdr, {'template_name': 'fs_fl_stone03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step3_cmdr = Sound(root=self, name='step3_cmdr', sound='fs_fl_stone04', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step3_cmdr, {'template_name': 'fs_fl_stone04', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_LIGHT_barocameras_left = Light(root=self, name='LIGHT_barocameras_left', point_name='LIGHT_barocameras_left', extra_name='', light_group=55, diffuse=[0.6, 0.6, 0.8], ambient=[0.2, 0.4, 0.1], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocameras_left, {'template_name': '', 'lt_grp': 55, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.6, 0.6, 0.8], 'specular': [0, 0, 0], 'ambient': [0.2, 0.4, 0.1], 'direction': [-1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocameras_trentlook = Light(root=self, name='LIGHT_barocameras_trentlook', point_name='LIGHT_barocameras_trentlook', extra_name='', light_group=56, diffuse=[0.6, 0.6, 0.8], ambient=[0.2, 0.4, 0.1], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocameras_trentlook, {'template_name': '', 'lt_grp': 56, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.6, 0.6, 0.8], 'specular': [0, 0, 0], 'ambient': [0.2, 0.4, 0.1], 'direction': [-1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_trentchars_jabbaside = Light(root=self, name='LIGHT_trentchars_jabbaside', point_name='LIGHT_trentchars_jabbaside', extra_name='', light_group=56, diffuse=[0.5, 0.5, 0.5], ambient=[0.2, 0.2, 0.2], direction=[1, 0, 0], light_type='L_DIRECT', on=False, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_trentchars_jabbaside, {'template_name': '', 'lt_grp': 56, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'N', 'color': [255, 255, 255], 'diffuse': [0.5, 0.5, 0.5], 'specular': [0, 0, 0], 'ambient': [0.2, 0.2, 0.2], 'direction': [1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_darcy_and_girlfriend = Light(root=self, name='LIGHT_darcy_and_girlfriend', point_name='LIGHT_darcy_and_girlfriend', extra_name='', light_group=60, diffuse=[1, 1, 1], ambient=[0.3, 0.4, 0.55], direction=[1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_darcy_and_girlfriend, {'template_name': '', 'lt_grp': 60, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [1, 1, 1], 'specular': [0, 0, 0], 'ambient': [0.3, 0.4, 0.55], 'direction': [1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_Prop_server01 = Asset_obj_Prop_server01(root=self, name='Prop_server01', light_group=6, init_point='Prop_server01', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server01, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_server03 = Asset_obj_Prop_server03(root=self, name='Prop_server03', light_group=6, init_point='Prop_server03', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server03, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_server04 = Asset_obj_Prop_server04(root=self, name='Prop_server04', light_group=6, init_point='Prop_server04', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server04, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_server05 = Asset_obj_Prop_server05(root=self, name='Prop_server05', light_group=6, init_point='Prop_server05', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server05, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera01 = Asset_obj_Prop_barocamera01(root=self, name='Prop_barocamera01', light_group=6, init_point='Prop_barocamera01', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera01, {'template_name': 'm7_barocamera', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera03 = Asset_obj_Prop_barocamera03(root=self, name='Prop_barocamera03', light_group=6, init_point='Prop_barocamera03', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera03, {'template_name': 'm7_barocamera', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera05 = Asset_obj_Prop_barocamera05(root=self, name='Prop_barocamera05', light_group=7, init_point='Prop_barocamera05', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera05, {'template_name': 'm7_barocamera', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_alien05 = Asset_obj_Prop_alien05(root=self, name='Prop_alien05', light_group=52, init_point='Prop_alien05', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_alien05, {'template_name': 'm7_olaf', 'lt_grp': 52, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera06 = Asset_obj_Prop_barocamera06(root=self, name='Prop_barocamera06', light_group=7, init_point='Prop_barocamera06', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera06, {'template_name': 'm7_barocamera_tall', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_alien06 = Asset_obj_Prop_alien06(root=self, name='Prop_alien06', light_group=51, init_point='Prop_alien06', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_alien06, {'template_name': 'm7_jarjar', 'lt_grp': 51, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera07 = Asset_obj_Prop_barocamera07(root=self, name='Prop_barocamera07', light_group=7, init_point='Prop_barocamera07', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera07, {'template_name': 'm7_barocamera_tall', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_alien07 = Asset_obj_Prop_alien07(root=self, name='Prop_alien07', light_group=50, init_point='Prop_alien07', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_alien07, {'template_name': 'm7_samus', 'lt_grp': 50, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera08 = Asset_obj_Prop_barocamera08(root=self, name='Prop_barocamera08', light_group=7, init_point='Prop_barocamera08', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera08, {'template_name': 'm7_barocamera', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_alien08 = Asset_obj_Prop_alien08(root=self, name='Prop_alien08', light_group=55, init_point='Prop_alien08', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_alien08, {'template_name': 'm7_mole', 'lt_grp': 55, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera09 = Asset_obj_Prop_barocamera09(root=self, name='Prop_barocamera09', light_group=7, init_point='Prop_barocamera09', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera09, {'template_name': 'm7_barocamera_tall', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_alien09 = Asset_obj_Prop_alien09(root=self, name='Prop_alien09', light_group=53, init_point='Prop_alien09', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_alien09, {'template_name': 'm7_elon', 'lt_grp': 53, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_barocamera10 = Asset_obj_Prop_barocamera10(root=self, name='Prop_barocamera10', light_group=7, init_point='Prop_barocamera10', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barocamera10, {'template_name': 'm7_barocamera_tall', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Char_monkeyking = Character(root=self, actor=Actor_obj_Char_monkeyking, light_group=54, init_point='Char_monkeyking', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_monkeyking, {'template_name': 'm07_monkeyking', 'lt_grp': 54, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character'}})
        obj_Prop_alien01 = Asset_obj_Prop_alien01(root=self, name='Prop_alien01', light_group=15, init_point='Prop_alien01', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_alien01, {'template_name': 'm7_facehugger', 'lt_grp': 15, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Char_worm = Character(root=self, actor=Actor_obj_Char_worm, light_group=5, init_point='Char_worm', rotate_from_quat=True, use_ambient=True, floor_height=1.2)
        preserve_entity(obj_Char_worm, {'template_name': 'worm', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 1.2}, 'userprops': {'category': 'Character'}})
        obj_LIGHT_barocamera_inside01 = Light(root=self, name='LIGHT_barocamera_inside01', point_name='LIGHT_barocamera_inside01', extra_name='', light_group=5, diffuse=[0.9, 1, 0], ambient=[1, 0.5, 0.25], direction=[0, -0.8, -0.2], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside01, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.9, 1, 0], 'specular': [0, 0, 0], 'ambient': [1, 0.5, 0.25], 'direction': [0, -0.8, -0.2], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_inside02 = Light(root=self, name='LIGHT_barocamera_inside02', point_name='LIGHT_barocamera_inside02', extra_name='', light_group=15, diffuse=[0.4, 0.5, 0], ambient=[0.5, 0.25, 0], direction=[0, 0, 1], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside02, {'template_name': '', 'lt_grp': 15, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.4, 0.5, 0], 'specular': [0, 0, 0], 'ambient': [0.5, 0.25, 0], 'direction': [0, 0, 1], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_objects = Light(root=self, name='LIGHT_barocamera_objects', point_name='LIGHT_barocamera_objects', extra_name='', light_group=6, diffuse=[0.2, 0.2, 0.5], ambient=[0.3, 0.3, 0.2], direction=[0.2, 0, -0.5], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_objects, {'template_name': '', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.2, 0.2, 0.5], 'specular': [0, 0, 0], 'ambient': [0.3, 0.3, 0.2], 'direction': [0.2, 0, -0.5], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_objects02 = Light(root=self, name='LIGHT_barocamera_objects02', point_name='LIGHT_barocamera_objects02', extra_name='', light_group=7, diffuse=[0.5, 0.5, 0.9], ambient=[0.9, 0.3, 0], direction=[0.2, 0, -0.5], light_type='L_DIRECT', on=True, range=5000, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_objects02, {'template_name': '', 'lt_grp': 7, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.5, 0.5, 0.9], 'specular': [0, 1, 0], 'ambient': [0.9, 0.3, 0], 'direction': [0.2, 0, -0.5], 'range': 5000, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_inside_samus = Light(root=self, name='LIGHT_barocamera_inside_samus', point_name='LIGHT_barocamera_inside_samus', extra_name='', light_group=50, diffuse=[0.9, 1, 0], ambient=[0.8, 0.5, 0.5], direction=[-0.5, -0.5, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside_samus, {'template_name': '', 'lt_grp': 50, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.9, 1, 0], 'specular': [0, 0, 0], 'ambient': [0.8, 0.5, 0.5], 'direction': [-0.5, -0.5, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_inside_jarjar = Light(root=self, name='LIGHT_barocamera_inside_jarjar', point_name='LIGHT_barocamera_inside_jarjar', extra_name='', light_group=51, diffuse=[0.9, 1, 0], ambient=[0.8, 0.2, 0.1], direction=[1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside_jarjar, {'template_name': '', 'lt_grp': 51, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.9, 1, 0], 'specular': [0, 0, 0], 'ambient': [0.8, 0.2, 0.1], 'direction': [1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_inside_olaf = Light(root=self, name='LIGHT_barocamera_inside_olaf', point_name='LIGHT_barocamera_inside_olaf', extra_name='', light_group=52, diffuse=[0.9, 1, 0], ambient=[0.5, 0.5, 0.25], direction=[0, -0.5, -0.5], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside_olaf, {'template_name': '', 'lt_grp': 52, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.9, 1, 0], 'specular': [0, 0, 0], 'ambient': [0.5, 0.5, 0.25], 'direction': [0, -0.5, -0.5], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_inside_elon = Light(root=self, name='LIGHT_barocamera_inside_elon', point_name='LIGHT_barocamera_inside_elon', extra_name='', light_group=53, diffuse=[0.6, 0.6, 0], ambient=[0.7, 0.5, 0.2], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside_elon, {'template_name': '', 'lt_grp': 53, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.6, 0.6, 0], 'specular': [0, 0, 0], 'ambient': [0.7, 0.5, 0.2], 'direction': [-1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_barocamera_inside_monkeyking = Light(root=self, name='LIGHT_barocamera_inside_monkeyking', point_name='LIGHT_barocamera_inside_monkeyking', extra_name='', light_group=54, diffuse=[0.9, 1, 0], ambient=[0.2, 0.3, 0.6], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_barocamera_inside_monkeyking, {'template_name': '', 'lt_grp': 54, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.9, 1, 0], 'specular': [0, 0, 0], 'ambient': [0.2, 0.3, 0.6], 'direction': [-1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=56, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 56, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_jabba = Character(root=self, actor=actors.Jabba, light_group=55, init_point='Char_jabba', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_jabba, {'template_name': 'jabba', 'lt_grp': 55, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Jabba', 'category': 'Character'}})
        obj_Char_darcy = Character(root=self, actor=actors.Darcy, light_group=60, init_point='Char_darcy', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_darcy, {'template_name': 'darcy', 'lt_grp': 60, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Darcy', 'category': 'Character'}})
        obj_Char_assistant = Character(root=self, actor=Actor_obj_Char_assistant, light_group=60, init_point='Char_assistant', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_assistant, {'template_name': 'm07_female_br_officer', 'lt_grp': 60, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Assistant', 'category': 'Character'}})
        obj_Char_gunner = Character(root=self, actor=Actor_obj_Char_gunner, light_group=55, init_point='Char_gunner', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_gunner, {'template_name': 'm07_male_br_officer_gunner', 'lt_grp': 55, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Gunner', 'category': 'Character'}})
        obj_Char_doorkeeper = Character(root=self, actor=Actor_obj_Char_doorkeeper, light_group=55, init_point='Char_doorkeeper', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_doorkeeper, {'template_name': 'm07_male_br_officer_marksman', 'lt_grp': 55, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Doorkeeper', 'category': 'Character'}})
        obj_Char_leader = Character(root=self, actor=Actor_obj_Char_leader, light_group=3, init_point='Char_leader', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_leader, {'template_name': 'm07_male_br_officer', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Policeleader', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_meeting = LookAtCamera(root=self, name='cam_darcy_meeting', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy_meeting, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy = LookAtCamera(root=self, name='cam_darcy', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_top = LookAtCamera(root=self, name='cam_darcy_top', fov=18, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_official = LookAtCamera(root=self, name='cam_darcy_official', fov=13, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy_official, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 13, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=18, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 7, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 9, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_darcy_and_girlfriend', angle=25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_monkeyking', anim=Male.Sc_MLBODY_STND_IDLE_BIG_000LV_xa_05, duration=0.1, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 11, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_worm', angle=-90, axis='Z_AXIS', duration=0, smooth=True)
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_worm', anim='Sc_Sc_s069x_worm_A', duration=12.5, time_scale=0.125, start_time=0, loop=False, trans_time=None)
        # source event 13, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_gunner', anim=Male.Sc_MLBODY_WALK_HOLD_GUN_RHAND_000LV_XB_01, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 15, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_doorkeeper', anim=Male.Sc_MLBODY_STND_HOLD_RIFLE_MILI_000LV_XA_05, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 16, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_leader', anim=Male.Sc_MLBODY_STND_LOOK_AROU_CASL_000LV_XA_08, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 17, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=15, axis='Y_AXIS', duration=0, smooth=True)
        # source event 19, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        # source event 21, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_jabba', duration=9.01, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 24, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 25, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_ATEASE_HOLD_000LV_XA_01, duration=100, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 40, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assistant', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 107, 0s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=3, attenuation=-15)
        # source event 108, 0s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=3, attenuation=-15)
        # source event 109, 0s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=3, attenuation=-15)
        t += 0.01
        # source event 23, 0.01s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        t += 0.19
        # source event 83, 0.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 8, 0.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', angle=-15, axis='X_AXIS', duration=0, smooth=False)
        t += 0.2
        # source event 84, 0.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 85, 1.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 86, 2.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 87, 2.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 88, 3.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 89, 4.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 90, 4.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step4', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 91, 5.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 92, 5.9s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 93, 6.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 94, 7.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 95, 8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        # source event 110, 8s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=3, attenuation=-30)
        # source event 111, 8s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=3, attenuation=-30)
        # source event 112, 8s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=3, attenuation=-30)
        t += 0.7
        # source event 96, 8.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 97, 9.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step4', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 18, 10s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-15, axis='Y_AXIS', duration=2, smooth=True)
        # source event 20, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_090LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 22, 10s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_darcy', duration=25, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.1
        # source event 98, 10.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 99, 10.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.4
        # source event 41, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assistant', anim=Female.Sc_FMBODY_STND_CONV_HNDS_CASL_000LV_xa_03, duration=100, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 100, 11s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 103, 11.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 101, 11.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 104, 11.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2_cmdr', duration=5, start_time=0, loop=False)
        t += 0.4
        # source event 102, 12.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.1
        # source event 105, 12.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 26, 12.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_barocameras_trentlook', duration=0, smooth=False, on=False)
        # source event 27, 12.5s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', duration=0, smooth=False, on=True)
        # source event 29, 12.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_meeting')
        # source event 30, 12.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_darcy_meeting', target_name='automarker_cam_darcy_meeting_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 31, 12.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=5.2, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 106, 12.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.01
        # source event 33, 12.51s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-12, axis='Y_AXIS', duration=3, smooth=True)
        t += 0.49
        # source event 36, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_ATEASE_RLEASE_000LV_XA_02, duration=2, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 38, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Male.GENERIC_ANIM, duration=25, start_time=0, time_scale=0.8, trans_time=0.25)
        t += 1
        # source event 42, 14s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assistant', anim=Female.Sc_FMBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=100, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 37, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_POINT_RHND_000LV_A_03, duration=100, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 43, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assistant', anim=Female.Sc_FMBODY_STND_SALUT_000LV_XA_03, duration=100, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 34, 17s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=7, axis='Y_AXIS', duration=4, smooth=True)
        t += 0.7
        # source event 32, 17.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=6.5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.3
        # source event 28, 18s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', duration=2, smooth=False, diffuse=[1, 1, 1], ambient=[0.3, 0.4, 0.55])
        # source event 39, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_TURN_180LV_XA_04, duration=100, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 44, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assistant', anim=Female.Sc_FMBODY_STND_WALK_TRNS_180LV_XA_02, duration=100, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(20)

        # Line 10: source 20s; allocated facial window 30s.
        t = 0
        # source event 45, 20s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='Char_trent', duration=25, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 46, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assistant', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 47, 20s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_official')
        # source event 48, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_darcy_official', target_name='automarker_cam_darcy_official_pos2', duration=10, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 49, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_darcy_official_focus', target_name='automarker_cam_darcy_official_marker_pos2', duration=10, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 53, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=100, time_scale=0.9, start_time=0, loop=False, trans_time=1)
        t += 5
        # source event 54, 27s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=100, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Reward', 'm07_reward')
        self.groups.pop('motion_10', None)
        obj_Char_darcy.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-20)

        # Line 20: source 30s; allocated facial window 30s.
        t = 0
        # source event 50, 30s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_top')
        # source event 51, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_darcy_top', target_name='automarker_cam_darcy_top_pos2', duration=17, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 52, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_darcy_top_focus', target_name='automarker_cam_darcy_top_marker_pos2', duration=17, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 55, 31s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=100, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 5
        # source event 56, 36s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=100, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        t += 4
        # source event 57, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_02, duration=100, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Reward', 'm07_reward')
        self.groups.pop('motion_20', None)
        obj_Char_darcy.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19.5)

        # Line 30: source 40.5s; allocated facial window 25s.
        t = 0
        t += 5.5
        # source event 69, 46s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 7, 'Msn7Reward', 'm07_reward')
        self.groups.pop('motion_30', None)
        obj_Char_darcy.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-18.7)

        # Line 40: source 46.8s; allocated facial window 6s.
        t = 0
        # source event 66, 46.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 7, 'Msn7Reward', 'm07_reward')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.3)

        # Line 50: source 50.5s; allocated facial window 25s.
        t = 0
        # source event 70, 50.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='Char_trent', duration=5, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 71, 50.5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='Char_trent', duration=5, transition_duration=1, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 72, 50.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy')
        # source event 77, 50.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_02, duration=100, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 4.0
        # source event 76, 54.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHEAD_MOTION_WINK_000LV_XA_, duration=25, time_scale=0.5, start_time=0.8, loop=False, trans_time=0.2)
        t += 1.0
        # source event 78, 55.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_WALK_TRNS_090LV_XA_02, duration=100, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 79, 56.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_darcy', duration=25, transition_duration=4, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7Reward', 'm07_reward')
        self.groups.pop('motion_50', None)
        obj_Char_darcy.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-18.0)

        # Line 60: source 57.5s; allocated facial window 6s.
        t = 0
        # source event 80, 57.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 7, 'Msn7Reward', 'm07_reward')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)
        restore_dialogue(self)
