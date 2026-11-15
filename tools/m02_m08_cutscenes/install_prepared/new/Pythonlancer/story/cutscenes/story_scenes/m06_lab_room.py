"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_prop_case(Prop):
    COMPOUND_TEMPLATE_NAME = 'artifact_case'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_crystal(Prop):
    COMPOUND_TEMPLATE_NAME = 'prop_artifact_crystal'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_tome(Prop):
    COMPOUND_TEMPLATE_NAME = 'tome'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_lab_room'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Camera_X = LookAtCamera(root=self, name='Camera_X', fov=30, farplane=100000, look_duration=300)
        preserve_entity(obj_Camera_X, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 30, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Camera_Case = StaticCamera(root=self, name='Camera_Case', fov=30, farplane=100000)
        preserve_entity(obj_Camera_Case, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 30, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_prop_case = Asset_obj_prop_case(root=self, name='prop_case', light_group=9, init_point='prop_case', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_case, {'template_name': 'artifact_case', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_crystal = Asset_obj_prop_crystal(root=self, name='prop_crystal', light_group=9, init_point='prop_crystal', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_crystal, {'template_name': 'prop_artifact_crystal', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_tome = Asset_obj_prop_tome(root=self, name='prop_tome', light_group=9, init_point='prop_tome', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_tome, {'template_name': 'tome', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_fx_gas = Alchemy(root=self, name='fx_gas', particles='rtc_artifactcasegas', point_name='fx_gas', sparam=0)
        preserve_entity(obj_fx_gas, {'template_name': 'rtc_artifactcasegas', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_fx_light = Alchemy(root=self, name='fx_light', particles='rtc_artifactlight', point_name='fx_light', sparam=0)
        preserve_entity(obj_fx_light, {'template_name': 'rtc_artifactlight', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_Char_Trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_Trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'trent', 'category': 'Character'}})
        obj_Path_CameraInit = MotionPath(root=self, name='Path_CameraInit', point_name='Path_CameraInit', path_data='{3, 2, -3}, {1,0,0,0}, {-1.5, 2, -1.5}, {1,0,0,0}, {-2, 2, 1}, {1,0,0,0}')
        preserve_entity(obj_Path_CameraInit, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {3, 2, -3}, {1,0,0,0}, {-1.5, 2, -1.5}, {1,0,0,0}, {-2, 2, 1}, {1,0,0,0}'}})
        obj_Path_Mrk_CameraInit = MotionPath(root=self, name='Path_Mrk_CameraInit', point_name='Path_Mrk_CameraInit', path_data='{0, 1, 0}, {1,0,0,0}, {0, 1, -1}, {1,0,0,0}')
        preserve_entity(obj_Path_Mrk_CameraInit, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 1, 0}, {1,0,0,0}, {0, 1, -1}, {1,0,0,0}'}})
        obj_Camera_Tome = LookAtCamera(root=self, name='Camera_Tome', fov=35, farplane=100000, look_duration=300)
        preserve_entity(obj_Camera_Tome, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Camera_OpenCase = StaticCamera(root=self, name='Camera_OpenCase', fov=30, farplane=100000)
        preserve_entity(obj_Camera_OpenCase, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 30, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_CameraOpenCase = MotionPath(root=self, name='Path_CameraOpenCase', point_name='Path_CameraOpenCase', path_data='{0.4, 1.5, -1.2}, {1,0,0,0}, {-0.3, 1.5, -1.5}, {1,0,0,0}')
        preserve_entity(obj_Path_CameraOpenCase, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0.4, 1.5, -1.2}, {1,0,0,0}, {-0.3, 1.5, -1.5}, {1,0,0,0}'}})
        obj_Camera_GetCrystal = LookAtCamera(root=self, name='Camera_GetCrystal', fov=25, farplane=100000, look_duration=300)
        preserve_entity(obj_Camera_GetCrystal, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 25, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_CameraGetCrystal = MotionPath(root=self, name='Path_CameraGetCrystal', point_name='Path_CameraGetCrystal', path_data='{0, 1.3, 0}, {1,0,0,0}, {0.3, 1.66, -0.5}, {1,0,0,0}')
        preserve_entity(obj_Path_CameraGetCrystal, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 1.3, 0}, {1,0,0,0}, {0.3, 1.66, -0.5}, {1,0,0,0}'}})
        obj_Path_MrkGetCrystal = MotionPath(root=self, name='Path_MrkGetCrystal', point_name='Path_MrkGetCrystal', path_data='{-0.2, 1.4, -0.8}, {1,0,0,0}, {-0.3, 1.6, -1.3}, {1,0,0,0}')
        preserve_entity(obj_Path_MrkGetCrystal, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-0.2, 1.4, -0.8}, {1,0,0,0}, {-0.3, 1.6, -1.3}, {1,0,0,0}'}})
        obj_Camera_Last = StaticCamera(root=self, name='Camera_Last', fov=35, farplane=100000)
        preserve_entity(obj_Camera_Last, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_music_main = Sound(root=self, name='music_main', sound='music_anticipation_more_forboding', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_main, {'template_name': 'music_anticipation_more_forboding', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_pick_tome_sound = Sound(root=self, name='pick_tome_sound', sound='sfx_pick_up_bottle03', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_pick_tome_sound, {'template_name': 'sfx_pick_up_bottle03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_weld1_sound = Sound(root=self, name='weld1_sound', sound='sfx_weld1', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_weld1_sound, {'template_name': 'sfx_weld1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_weld2_sound = Sound(root=self, name='weld2_sound', sound='sfx_weld2', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_weld2_sound, {'template_name': 'sfx_weld2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_weld3_sound = Sound(root=self, name='weld3_sound', sound='sfx_weld3', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_weld3_sound, {'template_name': 'sfx_weld3', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_weld4_sound = Sound(root=self, name='weld4_sound', sound='sfx_weld4', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_weld4_sound, {'template_name': 'sfx_weld4', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_weld5_sound = Sound(root=self, name='weld5_sound', sound='sfx_weld5', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_weld5_sound, {'template_name': 'sfx_weld5', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_laser_sound = Sound(root=self, name='laser_sound', sound='rtc_laser_impact', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_laser_sound, {'template_name': 'rtc_laser_impact', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step1 = Sound(root=self, name='step1', sound='fs_ml_stone04', attenuation=-15, dmin=50, dmax=300, priority=None)
        preserve_entity(obj_step1, {'template_name': 'fs_ml_stone04', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_step2 = Sound(root=self, name='step2', sound='fs_mr_stone04', attenuation=-15, dmin=50, dmax=300, priority=None)
        preserve_entity(obj_step2, {'template_name': 'fs_mr_stone04', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_step3 = Sound(root=self, name='step3', sound='fs_ml_stone03', attenuation=-15, dmin=50, dmax=300, priority=None)
        preserve_entity(obj_step3, {'template_name': 'fs_ml_stone03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        t = 0
        # source event 0, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_crystal', parent_name='prop_case', duration=10, target_hardpoint='Hp_Rest_crystal', parent_hardpoint='Hp_Connect_crystal')
        # source event 1, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_X')
        # source event 4, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_OpenCase', 'prop_crystal'], duration=300, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 6, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_X', 'Path_CameraInit'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 7, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_X_focus', 'Path_Mrk_CameraInit'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 8, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_Mrk_TrentTome', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 35, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=500, start_time=0, loop=False)
        t += 6
        # source event 9, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s051x_Trent_XA_STND_000DN_07, duration=15, time_scale=0.6, start_time=1, loop=False, trans_time=None)
        t += 3
        # source event 11, 9s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_Tome')
        t += 0.5
        # source event 12, 9.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_HAPPY_CHUCKLE_TRENT_000LV_XA_, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.0
        # source event 10, 10.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_tome', parent_name='Char_trent', duration=10000, target_hardpoint='rhand_connect_tome', parent_hardpoint='hprightconnect')
        # source event 36, 10.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='pick_tome_sound', duration=5, start_time=0, loop=False)
        t += 2.5
        # source event 13, 13s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='prop_crystal', duration=5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 14, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_SURPRSE_IMPRESSED_TRENT_000LV_XA_, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 15, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_Mrk_TrentAway', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 16, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_OpenCase')
        # source event 17, 16s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_OpenCase', 'Path_CameraOpenCase'], duration=15, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 18, 16s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['prop_case'], animation='Sc_open case', duration=15, start_time=0, time_scale=1, weight=1, trans_scale=1)
        t += 0.5
        # source event 19, 16.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fx_light', duration=36000)
        # source event 37, 16.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='laser_sound', duration=5, start_time=0, loop=False)
        t += 2.0
        # source event 38, 18.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld2_sound', duration=5, start_time=0, loop=False)
        t += 1.7
        # source event 39, 20.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld3_sound', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 40, 20.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld3_sound', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 41, 20.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld3_sound', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 42, 21.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld3_sound', duration=5, start_time=0, loop=False)
        t += 1.1
        # source event 43, 22.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld5_sound', duration=5, start_time=0, loop=False)
        t += 3.8
        # source event 23, 26s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_Mrk_TrentCrystal', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 32, 26s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_Mrk_TrentCrystal_LookAt', duration=6, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 20, 27s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_GetCrystal')
        # source event 21, 27s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_GetCrystal', 'Path_CameraGetCrystal'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 22, 27s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Camera_GetCrystal_focus', 'Path_MrkGetCrystal'], duration=5, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        t += 0.001
        # source event 24, 27.001s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s012x_Quintaine_XA_STND_GRABL_ARTFCT_000DN_08, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.499
        # source event 26, 27.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_HOLD_ARTFCT_LHAND_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 33, 28s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_Mrk_TrentCrystal_LookAt', target_name='automarker_Mrk_TrentCrystal_LookAt_pos2', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.4
        # source event 44, 28.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='weld1_sound', duration=5, start_time=0, loop=False)
        t += 0.1
        # source event 25, 28.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_crystal', parent_name='Char_trent', duration=50000, target_hardpoint='HpLefthandConnect_prop_crystal', parent_hardpoint='hpleftconnect')
        main_group.append_time(29)

        # Line 10: source 29s; allocated facial window 15s.
        t = 0
        select_dialogue(self, 6, 'Msn6LabRoom', 'm06_lab_room')
        self.groups.pop('motion_10', None)
        obj_Char_Trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-13)

        # Line 20: source 31s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 6, 'Msn6LabRoom', 'm06_lab_room')
        voice_sound = self.lookup_single_sound(20)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        t += 1
        # source event 30, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_TURN_LEFT_BAR_180LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 34, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_Camera_GetCrystal_focus', target_name='automarker_Mrk_ExitPoint', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 31, 34.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        main_group.append_time(5.0)
        restore_dialogue(self)
