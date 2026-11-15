"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_BIGSHIP(Ship):
    COMPOUND_TEMPLATE_NAME = 'or_osiris'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_PlayerShip(Ship):
    COMPOUND_TEMPLATE_NAME = 'PlayerShip'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Player_connecter(Solar):
    COMPOUND_TEMPLATE_NAME = 'hidden_connect'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_li_elite01(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_li_elite02(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_li_elite03(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_li_elite04(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_or_elite01(Ship):
    COMPOUND_TEMPLATE_NAME = 'or_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_or_elite02(Ship):
    COMPOUND_TEMPLATE_NAME = 'or_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_ambi_skydome_clouds_snow(Prop):
    COMPOUND_TEMPLATE_NAME = 'edge_exclusion'
    SRT_GRP = -100
    USR_FLG = 2


class Asset_obj_lapa(Prop):
    COMPOUND_TEMPLATE_NAME = 'equip_magnet'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_omicron_major'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(60.0)
        obj_Light_SCENE = Light(root=self, name='Light_SCENE', point_name='Light_SCENE', extra_name='', light_group=0, diffuse=[0.8, 0.3, 0.7], ambient=[0.2, 0.4, 0.35], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=10000, cutoff=90, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Light_SCENE, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.8, 0.3, 0.7], 'specular': [0, 0, 0], 'ambient': [0.2, 0.4, 0.35], 'direction': [-1, 0, 0], 'range': 10000, 'cutoff': 90, 'type': 'L_DIRECT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Camera_1 = LookAtCamera(root=self, name='Camera_1', fov=35, farplane=120000, look_duration=60)
        preserve_entity(obj_Camera_1, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 120000}})
        obj_BIGSHIP = Asset_obj_BIGSHIP(root=self, name='BIGSHIP', light_group=0, init_point='BIGSHIP', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_BIGSHIP, {'template_name': 'or_osiris', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'or_osiris'}})
        obj_PlayerShip = Asset_obj_PlayerShip(root=self, name='PlayerShip', light_group=0, init_point='PlayerShip', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_PlayerShip, {'template_name': 'PlayerShip', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'running_lights': 'true'}})
        obj_Player_connecter = Asset_obj_Player_connecter(root=self, name='Player_connecter', light_group=0, init_point='Player_connecter', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_Player_connecter, {'template_name': 'hidden_connect', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Solar'}})
        obj_li_elite01 = Asset_obj_li_elite01(root=self, name='li_elite01', light_group=0, init_point='li_elite01', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_li_elite01, {'template_name': 'li_elite', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04', 'running_lights': 'true'}})
        obj_li_elite02 = Asset_obj_li_elite02(root=self, name='li_elite02', light_group=0, init_point='li_elite02', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_li_elite02, {'template_name': 'li_elite', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04', 'running_lights': 'true'}})
        obj_li_elite03 = Asset_obj_li_elite03(root=self, name='li_elite03', light_group=0, init_point='li_elite03', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_li_elite03, {'template_name': 'li_elite', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04', 'running_lights': 'true'}})
        obj_li_elite04 = Asset_obj_li_elite04(root=self, name='li_elite04', light_group=0, init_point='li_elite04', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_li_elite04, {'template_name': 'li_elite', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04', 'running_lights': 'true'}})
        obj_or_elite01 = Asset_obj_or_elite01(root=self, name='or_elite01', light_group=0, init_point='or_elite01', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_or_elite01, {'template_name': 'or_elite', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'ms6_cloak_co_elite2', 'running_lights': 'true'}})
        obj_or_elite02 = Asset_obj_or_elite02(root=self, name='or_elite02', light_group=0, init_point='or_elite02', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_or_elite02, {'template_name': 'or_elite', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'ms6_cloak_co_elite2', 'running_lights': 'true'}})
        obj_ambi_LtG11_Puffs_Amb = Light(root=self, name='ambi_LtG11_Puffs_Amb', point_name='ambi_LtG11_Puffs_Amb', extra_name='', light_group=11, diffuse=[0, 0, 0], ambient=[0.2352941, 0.5882353, 0.3921569], direction=[0, 0, 1], light_type='L_DIRECT', on=True, range=2000, cutoff=98.999977, theta=90, color=[255, 255, 255], attenuation=[1, 0, 0])
        preserve_entity(obj_ambi_LtG11_Puffs_Amb, {'lt_grp': 11, 'lightprops': {'on': 'Y', 'cutoff': 98.999977, 'direction': [0, 0, 1], 'range': 2000, 'ambient': [0.2352941, 0.5882353, 0.3921569], 'specular': [0, 0, 0], 'type': 'L_DIRECT', 'diffuse': [0, 0, 0], 'atten': [1, 0, 0], 'color': [255, 255, 255], 'theta': 90}, 'template_name': '', 'usr_flg': 0, 'srt_grp': 0})
        obj_ambi_skydome_clouds_snow = Asset_obj_ambi_skydome_clouds_snow(root=self, name='ambi_skydome_clouds_snow', light_group=23, init_point='ambi_skydome_clouds_snow', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_ambi_skydome_clouds_snow, {'lt_grp': 23, 'flags': 4, 'userprops': {'category': 'Prop', 'NoFog': 'Y'}, 'template_name': 'edge_exclusion', 'usr_flg': 2, 'srt_grp': -100})
        obj_Path_GOTO_PL = MotionPath(root=self, name='Path_GOTO_PL', point_name='Path_GOTO_PL', path_data='{0, 75, -400}, {1,0,0,0}, {0, 75, -65}, {1,0,0,0}')
        preserve_entity(obj_Path_GOTO_PL, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 75, -400}, {1,0,0,0}, {0, 75, -65}, {1,0,0,0}'}})
        obj_Path_Order01_Position = MotionPath(root=self, name='Path_Order01_Position', point_name='Path_Order01_Position', path_data='{-75, 10, -80}, {1,0,0,0}, {-65, 10, -10}, {1,0,0,0}, {-20, 10, 20}, {1,0,0,0}')
        preserve_entity(obj_Path_Order01_Position, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-75, 10, -80}, {1,0,0,0}, {-65, 10, -10}, {1,0,0,0}, {-20, 10, 20}, {1,0,0,0}'}})
        obj_Path_Order02_Position = MotionPath(root=self, name='Path_Order02_Position', point_name='Path_Order02_Position', path_data='{-40, 10, -100}, {1,0,0,0}, {-35, 10, -50}, {1,0,0,0}, {-15, 10, -25}, {1,0,0,0}')
        preserve_entity(obj_Path_Order02_Position, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-40, 10, -100}, {1,0,0,0}, {-35, 10, -50}, {1,0,0,0}, {-15, 10, -25}, {1,0,0,0}'}})
        obj_lapa = Asset_obj_lapa(root=self, name='lapa', light_group=0, init_point='lapa', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_lapa, {'template_name': 'equip_magnet', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_lapa_down = MotionPath(root=self, name='lapa_down', point_name='lapa_down', path_data='{0, 50, 0}, {1,0,0,0}, {0, 25, 0}, {1,0,0,0}')
        preserve_entity(obj_lapa_down, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 50, 0}, {1,0,0,0}, {0, 25, 0}, {1,0,0,0}'}})
        obj_lapa_up = MotionPath(root=self, name='lapa_up', point_name='lapa_up', path_data='{0, 25, 0}, {1,0,0,0}, {0, 75, 0}, {1,0,0,0}')
        preserve_entity(obj_lapa_up, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 25, 0}, {1,0,0,0}, {0, 75, 0}, {1,0,0,0}'}})
        obj_player_up = MotionPath(root=self, name='player_up', point_name='player_up', path_data='{0, 12, 0}, {1,0,0,0}, {0, 62, 0}, {1,0,0,0}')
        preserve_entity(obj_player_up, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 12, 0}, {1,0,0,0}, {0, 62, 0}, {1,0,0,0}'}})
        obj_PlayerShipEngines_2 = Alchemy(root=self, name='PlayerShipEngines_2', particles='PlayerShipEngines', point_name='PlayerShipEngines_2', sparam=0)
        preserve_entity(obj_PlayerShipEngines_2, {'template_name': 'PlayerShipEngines', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_engine1 = Alchemy(root=self, name='fx_li_engine1', particles='gf_li_smallengine02_fire', point_name='fx_li_engine1', sparam=0)
        preserve_entity(obj_fx_li_engine1, {'template_name': 'gf_li_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_engine2 = Alchemy(root=self, name='fx_li_engine2', particles='gf_li_smallengine02_fire', point_name='fx_li_engine2', sparam=0)
        preserve_entity(obj_fx_li_engine2, {'template_name': 'gf_li_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_engine3 = Alchemy(root=self, name='fx_li_engine3', particles='gf_li_smallengine02_fire', point_name='fx_li_engine3', sparam=0)
        preserve_entity(obj_fx_li_engine3, {'template_name': 'gf_li_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_engine4 = Alchemy(root=self, name='fx_li_engine4', particles='gf_li_smallengine02_fire', point_name='fx_li_engine4', sparam=0)
        preserve_entity(obj_fx_li_engine4, {'template_name': 'gf_li_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_trapped1 = Alchemy(root=self, name='fx_li_trapped1', particles='ms6_trapped', point_name='fx_li_trapped1', sparam=0)
        preserve_entity(obj_fx_li_trapped1, {'template_name': 'ms6_trapped', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_trapped2 = Alchemy(root=self, name='fx_li_trapped2', particles='ms6_trapped', point_name='fx_li_trapped2', sparam=0)
        preserve_entity(obj_fx_li_trapped2, {'template_name': 'ms6_trapped', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_trapped3 = Alchemy(root=self, name='fx_li_trapped3', particles='ms6_trapped', point_name='fx_li_trapped3', sparam=0)
        preserve_entity(obj_fx_li_trapped3, {'template_name': 'ms6_trapped', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_player_trapped = Alchemy(root=self, name='fx_player_trapped', particles='ms6_trapped', point_name='fx_player_trapped', sparam=0)
        preserve_entity(obj_fx_player_trapped, {'template_name': 'ms6_trapped', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_li_trapped4 = Alchemy(root=self, name='fx_li_trapped4', particles='ms6_trapped', point_name='fx_li_trapped4', sparam=0)
        preserve_entity(obj_fx_li_trapped4, {'template_name': 'ms6_trapped', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_or_engine1a = Alchemy(root=self, name='fx_or_engine1a', particles='gf_co_smallengine02_fire', point_name='fx_or_engine1a', sparam=0)
        preserve_entity(obj_fx_or_engine1a, {'template_name': 'gf_co_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_or_engine1b = Alchemy(root=self, name='fx_or_engine1b', particles='gf_co_smallengine02_fire', point_name='fx_or_engine1b', sparam=0)
        preserve_entity(obj_fx_or_engine1b, {'template_name': 'gf_co_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_or_engine1c = Alchemy(root=self, name='fx_or_engine1c', particles='gf_co_smallengine02_fire', point_name='fx_or_engine1c', sparam=0)
        preserve_entity(obj_fx_or_engine1c, {'template_name': 'gf_co_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_or_engine2a = Alchemy(root=self, name='fx_or_engine2a', particles='gf_co_smallengine02_fire', point_name='fx_or_engine2a', sparam=0)
        preserve_entity(obj_fx_or_engine2a, {'template_name': 'gf_co_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_or_engine2b = Alchemy(root=self, name='fx_or_engine2b', particles='gf_co_smallengine02_fire', point_name='fx_or_engine2b', sparam=0)
        preserve_entity(obj_fx_or_engine2b, {'template_name': 'gf_co_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_or_engine2c = Alchemy(root=self, name='fx_or_engine2c', particles='gf_co_smallengine02_fire', point_name='fx_or_engine2c', sparam=0)
        preserve_entity(obj_fx_or_engine2c, {'template_name': 'gf_co_smallengine02_fire', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_camera_start_path = MotionPath(root=self, name='camera_start_path', point_name='camera_start_path', path_data='{10, 10, 20}, {1,0,0,0}, {30, 15, -5}, {1,0,0,0}')
        preserve_entity(obj_camera_start_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {10, 10, 20}, {1,0,0,0}, {30, 15, -5}, {1,0,0,0}'}})
        obj_marker_start_path = MotionPath(root=self, name='marker_start_path', point_name='marker_start_path', path_data='{-100, 10, 100}, {1,0,0,0}, {-100, -10, 0}, {1,0,0,0}')
        preserve_entity(obj_marker_start_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-100, 10, 100}, {1,0,0,0}, {-100, -10, 0}, {1,0,0,0}'}})
        obj_camera_bigship_arrive_path = MotionPath(root=self, name='camera_bigship_arrive_path', point_name='camera_bigship_arrive_path', path_data='{30, 15, -5}, {1,0,0,0}, {20, 5, 60}, {1,0,0,0}')
        preserve_entity(obj_camera_bigship_arrive_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {30, 15, -5}, {1,0,0,0}, {20, 5, 60}, {1,0,0,0}'}})
        obj_marker_bigship_arrive_path = MotionPath(root=self, name='marker_bigship_arrive_path', point_name='marker_bigship_arrive_path', path_data='{-100, -10, 0}, {1,0,0,0}, {0, 75, -300}, {1,0,0,0}')
        preserve_entity(obj_marker_bigship_arrive_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-100, -10, 0}, {1,0,0,0}, {0, 75, -300}, {1,0,0,0}'}})
        obj_camera_baydoor_path = MotionPath(root=self, name='camera_baydoor_path', point_name='camera_baydoor_path', path_data='{60, 40, 10}, {1,0,0,0}, {35, 25, -20}, {1,0,0,0}, {-10, 10, -35}, {1,0,0,0}')
        preserve_entity(obj_camera_baydoor_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {60, 40, 10}, {1,0,0,0}, {35, 25, -20}, {1,0,0,0}, {-10, 10, -35}, {1,0,0,0}'}})
        obj_marker_baydoor_path = MotionPath(root=self, name='marker_baydoor_path', point_name='marker_baydoor_path', path_data='{0, 50, 0}, {1,0,0,0}, {0, 35, 0}, {1,0,0,0}')
        preserve_entity(obj_marker_baydoor_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 50, 0}, {1,0,0,0}, {0, 35, 0}, {1,0,0,0}'}})
        obj_marker_baydoor_down_path = MotionPath(root=self, name='marker_baydoor_down_path', point_name='marker_baydoor_down_path', path_data='{0, 35, 0}, {1,0,0,0}, {0, 15, 0}, {1,0,0,0}')
        preserve_entity(obj_marker_baydoor_down_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 35, 0}, {1,0,0,0}, {0, 15, 0}, {1,0,0,0}'}})
        obj_camera_getting_path = MotionPath(root=self, name='camera_getting_path', point_name='camera_getting_path', path_data='{-10, 10, -35}, {1,0,0,0}, {-20, 5, -55}, {1,0,0,0}')
        preserve_entity(obj_camera_getting_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-10, 10, -35}, {1,0,0,0}, {-20, 5, -55}, {1,0,0,0}'}})
        obj_marker_getting_path = MotionPath(root=self, name='marker_getting_path', point_name='marker_getting_path', path_data='{0, 15, 0}, {1,0,0,0}, {0, 50, 0}, {1,0,0,0}')
        preserve_entity(obj_marker_getting_path, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 15, 0}, {1,0,0,0}, {0, 50, 0}, {1,0,0,0}'}})
        obj_gf_rtc_shipcushion_1 = Alchemy(root=self, name='gf_rtc_shipcushion_1', particles='gf_rtc_shipcushion', point_name='gf_rtc_shipcushion_1', sparam=0)
        preserve_entity(obj_gf_rtc_shipcushion_1, {'template_name': 'gf_rtc_shipcushion', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_music_main = Sound(root=self, name='music_main', sound='music_danger', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_main, {'template_name': 'music_danger', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_rumble_player = Sound(root=self, name='rumble_player', sound='rumble_ci_h_fighter', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_rumble_player, {'template_name': 'rumble_ci_h_fighter', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_rumble_osiris = Sound(root=self, name='rumble_osiris', sound='rumble_battleship', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_rumble_osiris, {'template_name': 'rumble_battleship', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_open_baydoor = Sound(root=self, name='open_baydoor', sound='depot_open_sound', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_open_baydoor, {'template_name': 'depot_open_sound', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_close_baydoor = Sound(root=self, name='close_baydoor', sound='depot_close_sound', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_close_baydoor, {'template_name': 'depot_close_sound', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_extend_lapa = Sound(root=self, name='extend_lapa', sound='hanger_doors_opening', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_extend_lapa, {'template_name': 'hanger_doors_opening', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_move_lapa_back = Sound(root=self, name='move_lapa_back', sound='hanger_doors_closing', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_move_lapa_back, {'template_name': 'hanger_doors_closing', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_1')
        # source event 1, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='PlayerShip', parent_name='Player_connecter', duration=60, target_hardpoint='HpTop', parent_hardpoint='HpConnect')
        # source event 2, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Player_connecter', 'automarker_Player_Marker'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 3, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShipEngines_2'], duration=0.1, psysprops={'sparam': 0.5})
        # source event 4, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='PlayerShipEngines_2', duration=60)
        # source event 5, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShipEngines_2', 'PlayerShip'], duration=30, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 6, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_player_trapped', duration=60)
        # source event 7, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_player_trapped', 'PlayerShip'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 8, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_engine1', duration=60)
        # source event 9, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_engine1', 'li_elite01'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 10, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_trapped1', duration=60)
        # source event 11, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_trapped1', 'li_elite01'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 12, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_engine2', duration=60)
        # source event 13, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_engine2', 'li_elite02'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 14, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_trapped2', duration=60)
        # source event 15, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_trapped2', 'li_elite02'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 16, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_engine3', duration=60)
        # source event 17, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_engine3', 'li_elite03'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 18, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_trapped3', duration=60)
        # source event 19, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_trapped3', 'li_elite03'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 20, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_engine4', duration=60)
        # source event 21, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_engine4', 'li_elite04'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 22, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_li_trapped4', duration=60)
        # source event 23, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_li_trapped4', 'li_elite04'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 24, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_or_engine1a', duration=60)
        # source event 25, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1a', 'or_elite01'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 26, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1a'], duration=0.5, psysprops={'sparam': 0.8})
        # source event 27, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_or_engine1b', duration=60)
        # source event 28, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1b', 'or_elite01'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine02', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 29, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1b'], duration=0.5, psysprops={'sparam': 0.8})
        # source event 30, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_or_engine1c', duration=60)
        # source event 31, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1c', 'or_elite01'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine03', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 32, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1c'], duration=0.5, psysprops={'sparam': 0.8})
        # source event 33, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_or_engine2a', duration=60)
        # source event 34, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2a', 'or_elite02'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 35, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2a'], duration=0.5, psysprops={'sparam': 0.8})
        # source event 36, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_or_engine2b', duration=60)
        # source event 37, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2b', 'or_elite02'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine02', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 38, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2b'], duration=0.5, psysprops={'sparam': 0.8})
        # source event 39, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_or_engine2c', duration=60)
        # source event 40, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2c', 'or_elite02'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hpengine03', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 41, 0s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2c'], duration=0.5, psysprops={'sparam': 0.8})
        # source event 43, 0s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['li_elite01'], animation='Sc_force extend', duration=30, time_scale=1, weight=1, trans_scale=1)
        # source event 44, 0s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['li_elite02'], animation='Sc_force extend', duration=30, time_scale=1, weight=1, trans_scale=1)
        # source event 45, 0s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['li_elite03'], animation='Sc_force extend', duration=30, time_scale=1, weight=1, trans_scale=1)
        # source event 46, 0s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['li_elite04'], animation='Sc_force extend', duration=30, time_scale=1, weight=1, trans_scale=1)
        # source event 47, 0s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['or_elite01'], animation='Sc_launch extend', duration=30, time_scale=1000, weight=1, trans_scale=1)
        # source event 48, 0s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['or_elite02'], animation='Sc_launch extend', duration=30, time_scale=1000, weight=1, trans_scale=1)
        # source event 54, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_1', 'camera_start_path'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 55, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_1_focus', 'marker_start_path'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 71, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='gf_rtc_shipcushion_1', duration=300)
        # source event 72, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['gf_rtc_shipcushion_1', 'lapa'], duration=600, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpFx01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 79, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=60, start_time=0, loop=True)
        # source event 80, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='rumble_player', duration=60, start_time=0, loop=True)
        # source event 86, 0s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=5, attenuation=0)
        t += 5
        # source event 49, 5s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['or_elite01', 'Path_Order01_Position'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 50, 5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='or_elite01', angle=135, axis='Y_AXIS', duration=4.9, smooth=False)
        t += 1
        # source event 51, 6s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['or_elite02', 'Path_Order02_Position'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 52, 6s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='or_elite02', angle=50, axis='Y_AXIS', duration=4.85, smooth=False)
        t += 4
        # source event 73, 10s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1a'], duration=0.5, psysprops={'sparam': 0})
        # source event 74, 10s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1b'], duration=0.5, psysprops={'sparam': 0})
        # source event 75, 10s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine1c'], duration=0.5, psysprops={'sparam': 0})
        # source event 76, 10s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2a'], duration=0.5, psysprops={'sparam': 0})
        # source event 77, 10s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2b'], duration=0.5, psysprops={'sparam': 0})
        # source event 78, 10s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fx_or_engine2c'], duration=0.5, psysprops={'sparam': 0})
        t += 2
        # source event 53, 12s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['BIGSHIP', 'Path_GOTO_PL'], duration=15, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 56, 12s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_1', 'camera_bigship_arrive_path'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 57, 12s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_1_focus', 'marker_bigship_arrive_path'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 58, 12s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_1', 'camera_bigship_arrive_path'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 59, 12s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_1_focus', 'marker_bigship_arrive_path'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        t += 3
        # source event 81, 15s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='rumble_osiris', duration=45, start_time=0, loop=True)
        t += 7
        # source event 60, 22s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_1', 'camera_baydoor_path'], duration=20, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 61, 22s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_1_focus', 'marker_baydoor_path'], duration=12, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        t += 5
        # source event 64, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='lapa', target_name='automarker_Marker_Lapa', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 63, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='BIGSHIP', anim='Sc_open baydoor', duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 82, 28s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='open_baydoor', duration=15, start_time=0, loop=False)
        t += 6
        # source event 62, 34s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_1_focus', 'marker_baydoor_down_path'], duration=8, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        t += 2
        # source event 65, 36s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['lapa', 'lapa_down'], duration=8, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 83, 36s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='extend_lapa', duration=15, start_time=0, loop=False)
        t += 6
        # source event 66, 42s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_1', 'camera_getting_path'], duration=15, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        t += 2
        # source event 67, 44s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_1_focus', 'marker_getting_path'], duration=15, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 68, 44s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['lapa', 'lapa_up'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 69, 44s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Player_Marker', 'player_up'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 84, 44s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='move_lapa_back', duration=15, start_time=0, loop=False)
        t += 6
        # source event 87, 50s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=10, attenuation=-25)
        t += 2
        # source event 70, 52s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='BIGSHIP', anim='Sc_close baydoor', duration=15, time_scale=-1, start_time=0, loop=False, trans_time=None)
        # source event 85, 52s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='close_baydoor', duration=15, start_time=0, loop=False)
        restore_dialogue(self)
