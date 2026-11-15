"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_Prop_server00(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_server'
    SRT_GRP = 0
    USR_FLG = 0


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


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_check_artifact'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Prop_server00 = Asset_obj_Prop_server00(root=self, name='Prop_server00', light_group=6, init_point='Prop_server00', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server00, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_server01 = Asset_obj_Prop_server01(root=self, name='Prop_server01', light_group=6, init_point='Prop_server01', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server01, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_server03 = Asset_obj_Prop_server03(root=self, name='Prop_server03', light_group=6, init_point='Prop_server03', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server03, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_server04 = Asset_obj_Prop_server04(root=self, name='Prop_server04', light_group=6, init_point='Prop_server04', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_server04, {'template_name': 'm7_server', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
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
        obj_LIGHT_trentchars_init = Light(root=self, name='LIGHT_trentchars_init', point_name='LIGHT_trentchars_init', extra_name='', light_group=12, diffuse=[0.6, 0.6, 0.8], ambient=[0.2, 0.4, 0.1], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_trentchars_init, {'template_name': '', 'lt_grp': 12, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.6, 0.6, 0.8], 'specular': [0, 0, 0], 'ambient': [0.2, 0.4, 0.1], 'direction': [-1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_trentchars_jabbaside = Light(root=self, name='LIGHT_trentchars_jabbaside', point_name='LIGHT_trentchars_jabbaside', extra_name='', light_group=12, diffuse=[0.8, 0.8, 0.9], ambient=[0.2, 0.3, 0.2], direction=[1, 0, 0], light_type='L_DIRECT', on=False, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_trentchars_jabbaside, {'template_name': '', 'lt_grp': 12, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'N', 'color': [255, 255, 255], 'diffuse': [0.8, 0.8, 0.9], 'specular': [0, 0, 0], 'ambient': [0.2, 0.3, 0.2], 'direction': [1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
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
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=12, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 12, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_jabba = Character(root=self, actor=actors.Jabba, light_group=3, init_point='Char_jabba', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jabba, {'template_name': 'jabba', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Jabba', 'category': 'Character'}})
        obj_Char_darcy = Character(root=self, actor=actors.Darcy, light_group=12, init_point='Char_darcy', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_darcy, {'template_name': 'darcy', 'lt_grp': 12, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Darcy', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_intro = LookAtCamera(root=self, name='cam_intro', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_intro, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_roomview = LookAtCamera(root=self, name='cam_roomview', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_roomview, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jabba_lookatdarcy = LookAtCamera(root=self, name='cam_jabba_lookatdarcy', fov=22, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_jabba_lookatdarcy, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jabba_check_artifact = LookAtCamera(root=self, name='cam_jabba_check_artifact', fov=22, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_jabba_check_artifact, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_offer = LookAtCamera(root=self, name='cam_darcy_offer', fov=18, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy_offer, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_final = StaticCamera(root=self, name='cam_darcy_final', fov=15, farplane=5000)
        preserve_entity(obj_cam_darcy_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jabba_affirmative = StaticCamera(root=self, name='cam_jabba_affirmative', fov=22, farplane=5000)
        preserve_entity(obj_cam_jabba_affirmative, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 9, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 11, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_monkeyking', anim=Male.Sc_MLBODY_STND_IDLE_BIG_000LV_xa_05, duration=0.1, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 13, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_worm', angle=-90, axis='Z_AXIS', duration=0, smooth=True)
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_worm', anim='Sc_Sc_s069x_worm_A', duration=10, time_scale=0.25, start_time=0, loop=False, trans_time=None)
        # source event 15, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-15, axis='Y_AXIS', duration=0, smooth=True)
        # source event 18, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 23, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Prop_alien01', angle=-35, axis='Y_AXIS', duration=0, smooth=True)
        t += 0.01
        # source event 17, 0.01s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        t += 0.49
        # source event 10, 0.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', angle=-15, axis='X_AXIS', duration=0, smooth=False)
        main_group.append_time(10)

        # Line 10: source 10s; allocated facial window 15s.
        t = 0
        # source event 19, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_intro')
        t += 3
        # source event 24, 13s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Prop_alien01', angle=-15, axis='Y_AXIS', duration=8, smooth=True)
        # source event 25, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Prop_alien01', target_name='automarker_point_alien01_top', duration=8, smooth=True, adjust_pos=True, adjust_orient=False)
        t += 2
        # source event 22, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_090LV_XA_02, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=0.25)
        t += 4
        # source event 26, 19s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=30, axis='Y_AXIS', duration=0, smooth=True)
        t += 1
        # source event 28, 20s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_init', duration=0, smooth=False, on=False)
        # source event 29, 20s
        LightAnimEvent(root=self, group=MAIN, time_delay=t, object_name='LIGHT_trentchars_jabbaside', duration=0, smooth=False, on=True)
        # source event 30, 20s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_roomview')
        # source event 31, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_roomview', target_name='automarker_cam_roomview_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 32, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_roomview_focus', target_name='automarker_cam_roomview_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 36, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=2.6, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 38, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=False)
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.5)

        # Line 20: source 20.5s; allocated facial window 14s.
        t = 0
        t += 1.5
        # source event 27, 22s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', angle=25, axis='Y_AXIS', duration=2, smooth=True)
        # source event 39, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=2.6, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.6
        # source event 37, 22.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.4
        # source event 41, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', target_name='automarker_point_darcy_init', duration=0, smooth=False, adjust_pos=True, adjust_orient=False)
        # source event 42, 24s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=10, axis='Y_AXIS', duration=0, smooth=True)
        # source event 43, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STROLL_000LV_XA_01, duration=3.4, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.6
        # source event 40, 24.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.4
        # source event 45, 27s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jabba_lookatdarcy')
        t += 0.4
        # source event 44, 27.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STROLL_STND_TRNS_000LV_XA_01, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 46, 27.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jabba', target_name='Char_darcy', duration=5, transition_duration=1, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_20', None)
        obj_Char_jabba.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.5)

        # Line 30: source 28s; allocated facial window 12s.
        t = 0
        t += 1
        # source event 49, 29s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_worm', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_30', None)
        obj_Char_jabba.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10)

        # Line 40: source 30s; allocated facial window 5s.
        t = 0
        # source event 7, 30s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_darcy_final', 'automarker_cam_darcy_final_marker'], duration=70, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 50, 30s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='Char_jabba', duration=5, transition_duration=1, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 51, 30s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_offer')
        t += 4
        # source event 54, 34s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 55, 34s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jabba_check_artifact')
        # source event 56, 34s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jabba', target_name='automarker_point_trent_hold_artifact_virtual', duration=6, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_40', None)
        obj_Char_darcy.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 50: source 35s; allocated facial window 15s.
        t = 0
        # source event 58, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_SPCBODY_s021x_Tobias_XA_STND_RUBH_000LV_05, duration=8, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 6
        # source event 57, 41s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jabba', target_name='automarker_point_darcy_head_near_jabba_virtual', duration=15, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_50', None)
        obj_Char_jabba.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.3)

        # Line 60: source 41.7s; allocated facial window 16.3s.
        t = 0
        t += 1.8
        # source event 59, 43.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=8, time_scale=0.58, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_60', None)
        obj_Char_jabba.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.0)

        # Line 70: source 50s; allocated facial window 25s.
        t = 0
        # source event 8, 50s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_jabba_affirmative', 'automarker_cam_jabba_affirmative_marker'], duration=70, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 60, 50s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 67, 50s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_final')
        # source event 68, 50s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_darcy_final', target_name='automarker_cam_darcy_final_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 69, 50s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_darcy_final_marker', target_name='automarker_cam_darcy_final_marker_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 73, 50s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5
        # source event 74, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 75, 56s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_1STEP_BKWD_PVOTR_090LV_XA_05, duration=10, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 76, 58s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='Char_jabba', duration=15, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_70', None)
        obj_Char_darcy.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-16)

        # Line 80: source 59s; allocated facial window 25s.
        t = 0
        t += 5
        # source event 82, 64s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jabba', target_name='automarker_point_darcy_head_near_jabba_virtual', duration=6, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_80', None)
        obj_Char_darcy.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19)

        # Line 90: source 65s; allocated facial window 12s.
        t = 0
        # source event 79, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', target_name='automarker_offscreen_back', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 80, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_offscreen_back', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 81, 65s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jabba_affirmative')
        # source event 85, 65s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 83, 67s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_jabba_affirmative', target_name='automarker_cam_jabba_affirmative_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 84, 67s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_jabba_affirmative_marker', target_name='automarker_cam_jabba_affirmative_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 86, 70s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jabba', anim=Male.Sc_MLBODY_STND_WALK_TRNS_180LV_XA_02, duration=10, time_scale=1, start_time=0, loop=False, trans_time=2)
        select_dialogue(self, 7, 'Msn7CheckArtifact', 'm07_check_artifact')
        self.groups.pop('motion_90', None)
        obj_Char_jabba.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.0)
        restore_dialogue(self)
