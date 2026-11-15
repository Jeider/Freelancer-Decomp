"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_prop_pda(Prop):
    COMPOUND_TEMPLATE_NAME = 'pda'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_pilot(Prop):
    COMPOUND_TEMPLATE_NAME = 'the_ship_pilot_trent'
    SRT_GRP = 1
    USR_FLG = 0


class Asset_obj_PlayerShip(Ship):
    COMPOUND_TEMPLATE_NAME = 'PlayerShip'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_alaric_ship(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_lab_land'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(40.0)
        obj_prop_pda = Asset_obj_prop_pda(root=self, name='prop_pda', light_group=0, init_point='prop_pda', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_pda, {'template_name': 'pda', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_pilot = Asset_obj_prop_pilot(root=self, name='prop_pilot', light_group=3, init_point='prop_pilot', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_pilot, {'template_name': 'the_ship_pilot_trent', 'lt_grp': 3, 'srt_grp': 1, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_PlayerShip = Asset_obj_PlayerShip(root=self, name='PlayerShip', light_group=3, init_point='PlayerShip', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_PlayerShip, {'template_name': 'PlayerShip', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship'}})
        obj_alaric_ship = Asset_obj_alaric_ship(root=self, name='alaric_ship', light_group=3, init_point='alaric_ship', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_alaric_ship, {'template_name': 'li_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'lod_ms6_alaric_cloak'}})
        obj_doors_sound = Sound(root=self, name='doors_sound', sound='hanger_doors_opening', attenuation=0, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_doors_sound, {'template_name': 'hanger_doors_opening', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_cart_sound1 = Sound(root=self, name='cart_sound1', sound='equipment_cart_start', attenuation=-10, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_cart_sound1, {'template_name': 'equipment_cart_start', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_cart_sound2 = Sound(root=self, name='cart_sound2', sound='equipment_cart_loop', attenuation=-10, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_cart_sound2, {'template_name': 'equipment_cart_loop', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_cart_sound3 = Sound(root=self, name='cart_sound3', sound='equipment_cart_stop', attenuation=-10, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_cart_sound3, {'template_name': 'equipment_cart_stop', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_turbine_sound = Sound(root=self, name='turbine_sound', sound='engine_rh_freighter_loop', attenuation=-50, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_turbine_sound, {'template_name': 'engine_rh_freighter_loop', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -50, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_landed_sound = Sound(root=self, name='landed_sound', sound='engine_rh_freighter_kill', attenuation=2, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_landed_sound, {'template_name': 'engine_rh_freighter_kill', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 2, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_cam_land = StaticCamera(root=self, name='cam_land', fov=35, farplane=100000)
        preserve_entity(obj_cam_land, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_Landing = MotionPath(root=self, name='Path_Landing', point_name='Path_Landing', path_data='{45,5,0}, {0.5,0,0.5,0}, {20,5,0}, {0.5,0,0.5,0}, {0,0,0}, {0.25,0,0.75,0}')
        preserve_entity(obj_Path_Landing, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {45,5,0}, {0.5,0,0.5,0}, {20,5,0}, {0.5,0,0.5,0}, {0,0,0}, {0.25,0,0.75,0} '}})
        obj_Xambi_ltg00_point_trader_key_yellow = Light(root=self, name='Xambi_ltg00_point_trader_key_yellow', point_name='Xambi_ltg00_point_trader_key_yellow', extra_name='', light_group=5, diffuse=[1, 1, 1], ambient=[0.18, 0.2, 0.18], direction=[0, 0, 1], light_type='L_POINT', on=True, range=2000, cutoff=98.999977, theta=90, color=[255, 255, 255], attenuation=[1, 0, 4e-06])
        preserve_entity(obj_Xambi_ltg00_point_trader_key_yellow, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [1, 1, 1], 'specular': [0, 0, 0], 'ambient': [0.18, 0.2, 0.18], 'direction': [0, 0, 1], 'range': 2000, 'cutoff': 98.999977, 'type': 'L_POINT', 'theta': 90, 'atten': [1, 0, 4e-06]}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=5, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'trent', 'category': 'Character'}})
        obj_Char_alaric = Character(root=self, actor=actors.Alaric, light_group=5, init_point='Char_alaric', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_alaric, {'template_name': 'alaric', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'alaric', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=25, farplane=100000, look_duration=30)
        preserve_entity(obj_cam_start, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 25, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=25, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric = LookAtCamera(root=self, name='cam_alaric', fov=22, farplane=5000, look_duration=51)
        preserve_entity(obj_cam_alaric, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = LookAtCamera(root=self, name='cam_final', fov=25, farplane=5000, look_duration=111)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_pda', parent_name='Char_alaric', duration=66.389, target_hardpoint='Hp_LHand_PDA', parent_hardpoint='HpLeftConnect')
        # source event 1, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_land', 'PlayerShip'], duration=30, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRoot', target_type='HARDPOINT', flags='LOOK_AT')
        # source event 6, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_land')
        # source event 7, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_land', target_name='automarker_cam_land_pos2', duration=14, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 8, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['PlayerShip', 'Path_Landing'], duration=15, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION+ORIENTATION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [0.791667, 0.977564, 0.2, 0.214286], [1, 1, 0, 0]]}, pcurve_period=-1)
        # source event 42, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='turbine_sound', duration=20, start_time=0, loop=True)
        # source event 43, 0s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='turbine_sound', duration=4, attenuation=0)
        t += 0.25
        # source event 41, 0.25s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='doors_sound', duration=15, start_time=0, loop=False)
        t += 9.75
        # source event 44, 10s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='turbine_sound', duration=3, attenuation=-5)
        t += 3
        # source event 45, 13s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='turbine_sound', duration=7, attenuation=-100)
        t += 1
        # source event 46, 14s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='landed_sound', duration=5, start_time=0, loop=False)
        t += 1.999
        # source event 9, 15.999s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='automarker_point_alaric', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 10, 15.999s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.001
        # source event 11, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_DEALR_PDA_000LV_XA_09, duration=5, time_scale=1, start_time=2, loop=False, trans_time=None)
        # source event 14, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 15, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 16, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 19, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=5, time_scale=0.75, start_time=0.15, loop=True, trans_time=None)
        t += 5
        # source event 12, 21s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_TURN_090LV_XA_02, duration=6, time_scale=0.8, start_time=0, loop=False, trans_time=1.5)
        # source event 20, 21s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=None)
        t += 5
        # source event 13, 26s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=1, time_scale=1, start_time=0, loop=False, trans_time=2)
        t += 1
        # source event 21, 27s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 0.5
        # source event 24, 27.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 25, 30s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        # source event 26, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_alaric', target_name='automarker_cam_alaric_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 27, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_alaric_focus', target_name='automarker_cam_alaric_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 32, 31s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 30, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        t += 2.7
        # source event 33, 34.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_1STEP_SIDWYSL_000LV_XA_02, duration=3, time_scale=1.2, start_time=0, loop=False, trans_time=None)
        t += 0.3
        # source event 31, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_DEALR_PDA_000LV_XA_09, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        # source event 34, 35s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=12, axis='Y_AXIS', duration=1.5, smooth=True)
        t += 0.5
        # source event 37, 35.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        # source event 38, 35.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_final_focus', target_name='automarker_cam_final_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 35, 36.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_RUN_TRNS_000LV_XA_02, duration=16, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 2.5
        # source event 36, 39s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=16, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        self.add_group('voice_17', time=22)
        select_dialogue(self, 6, 'Msn6LabLand', 'm06_lab_land')
        self.groups.pop('motion_10', None)
        obj_Char_alaric.facial(group='voice_17', index=10, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_22', time=27)
        select_dialogue(self, 6, 'Msn6LabLand', 'm06_lab_land')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group='voice_22', index=20, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_28', time=30)
        select_dialogue(self, 6, 'Msn6LabLand', 'm06_lab_land')
        self.groups.pop('motion_30', None)
        obj_Char_alaric.facial(group='voice_28', index=30, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_39', time=35.5)
        select_dialogue(self, 6, 'Msn6LabLand', 'm06_lab_land')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group='voice_39', index=40, append=False, auto_lip=True, extra_delay=0)
        restore_dialogue(self)
