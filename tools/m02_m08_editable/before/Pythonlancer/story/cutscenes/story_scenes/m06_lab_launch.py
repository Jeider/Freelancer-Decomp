"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_prop_crystal(Prop):
    COMPOUND_TEMPLATE_NAME = 'prop_artifact_crystal'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_tome(Prop):
    COMPOUND_TEMPLATE_NAME = 'tome'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_the_cart2(Prop):
    COMPOUND_TEMPLATE_NAME = 'rh_cart'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_the_cart3(Prop):
    COMPOUND_TEMPLATE_NAME = 'rh_cart'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_the_cart4(Prop):
    COMPOUND_TEMPLATE_NAME = 'rh_cart'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crateB1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm06_crate1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crateB2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm06_crate1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crateC1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm06_crate1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crateC2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm06_crate1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crateA1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm06_crate1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_crateA2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm06_crate1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_alaric_ship(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_PlayerShip(Ship):
    COMPOUND_TEMPLATE_NAME = 'PlayerShip'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_lab_launch'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(14.0)
        obj_prop_crystal = Asset_obj_prop_crystal(root=self, name='prop_crystal', light_group=9, init_point='prop_crystal', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_crystal, {'template_name': 'prop_artifact_crystal', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_tome = Asset_obj_prop_tome(root=self, name='prop_tome', light_group=9, init_point='prop_tome', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_tome, {'template_name': 'tome', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_the_cart2 = Asset_obj_the_cart2(root=self, name='the_cart2', light_group=3, init_point='the_cart2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_the_cart2, {'template_name': 'rh_cart', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment Cart', 'Priority': 'Equip_2'}})
        obj_the_cart3 = Asset_obj_the_cart3(root=self, name='the_cart3', light_group=3, init_point='the_cart3', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_the_cart3, {'template_name': 'rh_cart', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment Cart', 'Priority': 'Equip_2'}})
        obj_the_cart4 = Asset_obj_the_cart4(root=self, name='the_cart4', light_group=3, init_point='the_cart4', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_the_cart4, {'template_name': 'rh_cart', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Equipment Cart', 'Priority': 'Equip_2'}})
        obj_crateB1 = Asset_obj_crateB1(root=self, name='crateB1', light_group=3, init_point='crateB1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crateB1, {'template_name': 'm06_crate1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_crateB2 = Asset_obj_crateB2(root=self, name='crateB2', light_group=3, init_point='crateB2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crateB2, {'template_name': 'm06_crate1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_crateC1 = Asset_obj_crateC1(root=self, name='crateC1', light_group=3, init_point='crateC1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crateC1, {'template_name': 'm06_crate1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_crateC2 = Asset_obj_crateC2(root=self, name='crateC2', light_group=3, init_point='crateC2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crateC2, {'template_name': 'm06_crate1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_crateA1 = Asset_obj_crateA1(root=self, name='crateA1', light_group=3, init_point='crateA1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crateA1, {'template_name': 'm06_crate1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_crateA2 = Asset_obj_crateA2(root=self, name='crateA2', light_group=3, init_point='crateA2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_crateA2, {'template_name': 'm06_crate1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Camera_X = StaticCamera(root=self, name='Camera_X', fov=35, farplane=100000)
        preserve_entity(obj_Camera_X, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_alaric_ship = Asset_obj_alaric_ship(root=self, name='alaric_ship', light_group=3, init_point='alaric_ship', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_alaric_ship, {'template_name': 'li_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'lod_ms6_alaric_cloak'}})
        obj_PlayerShip = Asset_obj_PlayerShip(root=self, name='PlayerShip', light_group=3, init_point='PlayerShip', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_PlayerShip, {'template_name': 'PlayerShip', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship'}})
        obj_Char_Trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_Trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'trent', 'category': 'Character'}, 'ambient': [128, 128, 128]})
        obj_Path_CameraLaunch = MotionPath(root=self, name='Path_CameraLaunch', point_name='Path_CameraLaunch', path_data='{-20,4,0}, {1,0,0,0}, {-45,12,4}, {1,0,0,0}')
        preserve_entity(obj_Path_CameraLaunch, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-20,4,0}, {1,0,0,0}, {-45,12,4}, {1,0,0,0}'}})
        obj_Path_PlayerShipStart = MotionPath(root=self, name='Path_PlayerShipStart', point_name='Path_PlayerShipStart', path_data='{0,0,0}, {0.25,0,0.75,0}, {0,0.001,0}, {0.25,0,0.75,0}')
        preserve_entity(obj_Path_PlayerShipStart, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0,0,0}, {0.25,0,0.75,0}, {0,0.001,0}, {0.25,0,0.75,0}'}})
        obj_Path_PlayerShip = MotionPath(root=self, name='Path_PlayerShip', point_name='Path_PlayerShip', path_data='{0,0,0}, {1,0,0,0}, {1,4,0}, {1,0,0,0}')
        preserve_entity(obj_Path_PlayerShip, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0,0,0}, {1,0,0,0}, {1,4,0}, {1,0,0,0}'}})
        obj_Path_PlayerShipFlyOut = MotionPath(root=self, name='Path_PlayerShipFlyOut', point_name='Path_PlayerShipFlyOut', path_data='{1,4,0}, {0.25,0,-0.5,0}, {50,4,0}, {0.5,0,-0.5,0}')
        preserve_entity(obj_Path_PlayerShipFlyOut, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {1,4,0}, {0.25,0,-0.5,0}, {50,4,0}, {0.5,0,-0.5,0}'}})
        obj_Path_AlaricShip = MotionPath(root=self, name='Path_AlaricShip', point_name='Path_AlaricShip', path_data='{-15,3,-5}, {0.25,0,-0.5,0}, {-14,9,0}, {0.5,0,0.5,0}')
        preserve_entity(obj_Path_AlaricShip, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-15,3,-5}, {0.25,0,-0.5,0}, {-14,9,0}, {0.5,0,0.5,0}'}})
        obj_Path_AlaricShipOrient = MotionPath(root=self, name='Path_AlaricShipOrient', point_name='Path_AlaricShipOrient', path_data='{-15,3,-5}, {0.25,0,-0.5,0}, {-1,9,0}, {0.5,0,0.5,0}')
        preserve_entity(obj_Path_AlaricShipOrient, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN,  {-15,3,-5}, {0.25,0,-0.5,0}, {-1,9,0}, {0.5,0,0.5,0}'}})
        obj_Path_AlaricShipFlyAway = MotionPath(root=self, name='Path_AlaricShipFlyAway', point_name='Path_AlaricShipFlyAway', path_data='{-14,9,0}, {0.5,0,0.5,0}, {-50,9,0}, {0.25,0,-0.5,0}')
        preserve_entity(obj_Path_AlaricShipFlyAway, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-14,9,0}, {0.5,0,0.5,0}, {-50,9,0}, {0.25,0,-0.5,0}'}})
        obj_Camera_Running = LookAtCamera(root=self, name='Camera_Running', fov=35, farplane=100000, look_duration=300)
        preserve_entity(obj_Camera_Running, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_CameraRunning = MotionPath(root=self, name='Path_CameraRunning', point_name='Path_CameraRunning', path_data='{-1, 3, 35}, {1,0,0,0}, {0, 4, 20}, {1,0,0,0}')
        preserve_entity(obj_Path_CameraRunning, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-1, 3, 35}, {1,0,0,0}, {0, 4, 20}, {1,0,0,0}'}})
        obj_Path_MrkCameraRunning = MotionPath(root=self, name='Path_MrkCameraRunning', point_name='Path_MrkCameraRunning', path_data='{0, 0, 30}, {1,0,0,0}, {0, 5, 10}, {1,0,0,0}')
        preserve_entity(obj_Path_MrkCameraRunning, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 0, 30}, {1,0,0,0}, {0, 5, 10}, {1,0,0,0}'}})
        obj_Camera_Launch = LookAtCamera(root=self, name='Camera_Launch', fov=35, farplane=100000, look_duration=300)
        preserve_entity(obj_Camera_Launch, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_MrkCameraLaunch = MotionPath(root=self, name='Path_MrkCameraLaunch', point_name='Path_MrkCameraLaunch', path_data='{0, 2, 0}, {1,0,0,0}, {0, 5, 0}, {1,0,0,0}')
        preserve_entity(obj_Path_MrkCameraLaunch, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 2, 0}, {1,0,0,0}, {0, 5, 0}, {1,0,0,0}'}})
        obj_PlayerShipEngines_2 = Alchemy(root=self, name='PlayerShipEngines_2', particles='PlayerShipEngines', point_name='PlayerShipEngines_2', sparam=0)
        preserve_entity(obj_PlayerShipEngines_2, {'template_name': 'PlayerShipEngines', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_music_main = Sound(root=self, name='music_main', sound='music_upcoming_action_heavy', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_main, {'template_name': 'music_upcoming_action_heavy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_start_sound = Sound(root=self, name='start_sound', sound='engine_playership_launch_turbine', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_start_sound, {'template_name': 'engine_playership_launch_turbine', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_launch_sound = Sound(root=self, name='launch_sound', sound='engine_playership_launch', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_launch_sound, {'template_name': 'engine_playership_launch', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        t = 0
        # source event 0, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_crystal', parent_name='Char_trent', duration=50000, target_hardpoint='HpLefthandConnect_prop_crystal', parent_hardpoint='hpleftconnect')
        # source event 1, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_tome', parent_name='Char_trent', duration=10000, target_hardpoint='rhand_connect_tome', parent_hardpoint='hprightconnect')
        # source event 2, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_X', 'Mrk_CameraInit'], duration=300, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 3, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShip', 'Path_PlayerShipStart'], duration=0.001, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION+ORIENTATION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 4, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 20, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_Running')
        # source event 22, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_Running', 'Path_CameraRunning'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 23, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_Running_focus', 'Path_MrkCameraRunning'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 31, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=500, start_time=0, loop=False)
        t += 0.6
        # source event 5, 0.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 6, 1.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 7, 1.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 8, 2.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 9, 3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 10, 3.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 11, 4.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 12, 4.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.2
        # source event 13, 5s
        SourceSpatialEvent(root=self, group=MAIN, time_delay=t, targets=['Char_trent', 'automarker_Mrk_OffScreen'], duration=0.001, target_part='', target_type='ROOT', spatialprops={'pos': [25000, 0, 0], 'q_orient': [1, 0, 0, 0]})
        # source event 17, 5s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['alaric_ship', 'Path_AlaricShipOrient'], duration=8, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='ORIENTATION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 18, 5s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['alaric_ship', 'Path_AlaricShip'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 24, 5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_Launch')
        # source event 26, 5s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_Launch', 'Path_CameraLaunch'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 27, 5s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_Launch_focus', 'Path_MrkCameraLaunch'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 28, 5s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShipEngines_2'], duration=0.1, psysprops={'sparam': 0.5})
        # source event 29, 5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='PlayerShipEngines_2', duration=20)
        # source event 30, 5s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShipEngines_2', 'PlayerShip'], duration=30, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpEngine01', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 32, 5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='start_sound', duration=500, start_time=0, loop=False)
        t += 5
        # source event 14, 10s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='PlayerShip', angle=135, axis='Y_AXIS', duration=7, smooth=False)
        # source event 15, 10s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShip', 'Path_PlayerShip'], duration=3, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 19, 10s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['alaric_ship', 'Path_AlaricShipFlyAway'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        t += 1
        # source event 33, 11s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='launch_sound', duration=500, start_time=0, loop=False)
        t += 2
        # source event 16, 13s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShip', 'Path_PlayerShipFlyOut'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        restore_dialogue(self)
