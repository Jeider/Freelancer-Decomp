"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_prop_cityscape_bonus(Prop):
    COMPOUND_TEMPLATE_NAME = 'li_for_cityscape_bonus'
    SRT_GRP = 0
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
    DUMP_FILE = 'm04_final'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(72.0)
        obj_prop_cityscape_bonus = Asset_obj_prop_cityscape_bonus(root=self, name='prop_cityscape_bonus', light_group=3, init_point='prop_cityscape_bonus', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_prop_cityscape_bonus, {'template_name': 'li_for_cityscape_bonus', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_PlayerShip = Asset_obj_PlayerShip(root=self, name='PlayerShip', light_group=3, init_point='PlayerShip', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_PlayerShip, {'template_name': 'PlayerShip', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship'}})
        obj_alaric_ship = Asset_obj_alaric_ship(root=self, name='alaric_ship', light_group=3, init_point='alaric_ship', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_alaric_ship, {'template_name': 'li_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'lod_ms4_alaric'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=19.881128)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 19.881128}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True, use_ambient=True, floor_height=19.881128)
        preserve_entity(obj_Char_alaric, {'template_name': 'alaric', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 19.881128}, 'userprops': {'actor': 'Alaric', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wlkg_trent = StaticCamera(root=self, name='cam_wlkg_trent', fov=15, farplane=5000)
        preserve_entity(obj_cam_wlkg_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wlkg_alaric = StaticCamera(root=self, name='cam_wlkg_alaric', fov=15, farplane=5000)
        preserve_entity(obj_cam_wlkg_alaric, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wlkg_alaric_far = StaticCamera(root=self, name='cam_wlkg_alaric_far', fov=20, farplane=5000)
        preserve_entity(obj_cam_wlkg_alaric_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric_explain = LookAtCamera(root=self, name='cam_alaric_explain', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_alaric_explain, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_explain = LookAtCamera(root=self, name='cam_trent_explain', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_explain, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_explain_wide = LookAtCamera(root=self, name='cam_explain_wide', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_explain_wide, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 6, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_wlkg_trent', 'Char_trent'], duration=55, offset=[0.75, 0.6, 2], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION')
        # source event 7, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_wlkg_alaric', 'Char_alaric'], duration=55, offset=[-0.75, 0.6, 2], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION')
        # source event 8, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_wlkg_alaric_far', 'Char_alaric'], duration=55, offset=[-1.25, 0.6, 3], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION')
        # source event 9, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_trent_front', 'Char_trent'], duration=35, offset=[0, 0, 0.5], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 10, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_trent_front_near', 'Char_trent'], duration=35, offset=[1, 0, 1], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 11, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_trent_front_far', 'Char_trent'], duration=35, offset=[0, 0, 2], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 12, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_alaric_front', 'Char_alaric'], duration=35, offset=[0, 0, 0.5], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 13, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_alaric_front_near', 'Char_alaric'], duration=35, offset=[-1, 0, 1], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 14, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_alaric_front_far', 'Char_alaric'], duration=35, offset=[0, 0, 2], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 15, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 16, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 17, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=29, time_scale=0.75, start_time=0, loop=True, trans_time=None)
        # source event 20, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=30, time_scale=0.75, start_time=1, loop=True, trans_time=None)
        t += 7
        # source event 28, 7s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_wlkg_alaric_front_near', duration=5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 33, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wlkg_alaric_far')
        t += 3
        # source event 30, 10s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_wlkg_alaric_front_near', duration=15, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 23, 12s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_wlkg_trent_front_near', duration=7, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 29, 12s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_wlkg_trent_front_far', duration=13, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 4
        # source event 25, 16s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_wlkg_alaric_front', duration=2.5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 34, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wlkg_trent')
        t += 2.5
        # source event 26, 18.5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_wlkg_trent_front_far', duration=10.5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 24, 19s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_wlkg_trent_front_far', duration=10, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 4.5
        # source event 35, 23.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wlkg_alaric')
        t += 0.5
        # source event 46, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 31, 25s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_wlkg_alaric_front_far', duration=5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 32, 25s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_wlkg_alaric_front_far', duration=5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 4
        # source event 18, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 36, 30s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wlkg_trent')
        t += 0.5
        # source event 21, 30.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='automarker_point_alaric_explain', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 22, 30.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.4
        # source event 19, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 27, 32s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_head_alaric_explain', duration=10, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2.99
        # source event 52, 34.99s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='automarker_point_alaric_explain', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.01
        # source event 53, 35s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_head_ik', duration=28, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 54, 35s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_eye_ik', duration=28, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 55, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_trent_explain_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 56, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_trent_explain', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 57, 35s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric_explain')
        # source event 58, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=5, time_scale=0.6, start_time=1, loop=False, trans_time=None)
        t += 1
        # source event 71, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_alaric_explain_front', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 72, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric_explain', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 73, 36s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=33, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 74, 36s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=33, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 61, 38s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_explain')
        # source event 62, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 63, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 5
        # source event 66, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_explain_wide')
        # source event 67, 43s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_explain_wide', target_name='automarker_cam_explain_wide_pos2', duration=14, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 68, 43s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 76, 45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_trent_explain_outside', duration=3.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 75, 45.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_trent_explain_outside', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 77, 46s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_045LV_XA_04, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 78, 49s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 82, 49s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_SAD_CONCERN_TRENT_000LV_XA_, duration=12, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 83, 49.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_CONV_LHNDUP_TRNS_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        t += 1.0
        # source event 84, 50.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_CONV_LHND_CASL_000LV_xa_04, duration=4.5, time_scale=1, start_time=0, loop=True, trans_time=1.5)
        t += 2.5
        # source event 79, 53s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 85, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_CONV_LHNDDN_TRNS_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        t += 1
        # source event 89, 56s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_alaric_explain_front', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 90, 56s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric_explain', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 91, 56.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_315LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.0
        # source event 92, 57.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_explain')
        t += 4.3
        # source event 101, 61.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLHEAD_MOTION_BREATHE_HEAVY_000LV_XA_, duration=5, time_scale=0.2, start_time=0.25, loop=False, trans_time=0.1)
        t += 0.2
        # source event 95, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_alaric_explain_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 96, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_alaric_explain_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 99, 62s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric_explain')
        t += 1
        # source event 97, 63s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 102, 63.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 103, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric_explain_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 105, 65s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_explain')
        t += 1
        # source event 104, 66s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.8, start_time=0.3, loop=False, trans_time=1)
        t += 3
        # source event 98, 69s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 108, 69s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_180LV_XA_02, duration=10, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        self.add_group('voice_37', time=0.5)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        voice_sound = self.lookup_single_sound(10)
        SoundEvent(root=self, group='voice_37', sound_name=voice_sound.get_nickname())
        self.add_group('voice_38', time=4.5)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        voice_sound = self.lookup_single_sound(20)
        SoundEvent(root=self, group='voice_38', sound_name=voice_sound.get_nickname())
        self.add_group('voice_39', time=7)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_30', None)
        obj_Char_alaric.facial(group='voice_39', index=30, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_42', time=16)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group='voice_42', index=40, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_47', time=23.5)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_50', None)
        obj_Char_alaric.facial(group='voice_47', index=50, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_50', time=30)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group='voice_50', index=60, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_59', time=35)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_70', None)
        obj_Char_alaric.facial(group='voice_59', index=70, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_64', time=38)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_80', None)
        obj_Char_trent.facial(group='voice_64', index=80, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_69', time=43)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_90', None)
        obj_Char_alaric.facial(group='voice_69', index=90, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_80', time=46.5)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_100', None)
        obj_Char_trent.facial(group='voice_80', index=100, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_86', time=49.5)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_110', None)
        obj_Char_alaric.facial(group='voice_86', index=110, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_93', time=57.5)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_120', None)
        obj_Char_trent.facial(group='voice_93', index=120, append=False, auto_lip=True, extra_delay=0)
        self.add_group('voice_100', time=62)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        voice_sound = self.lookup_single_sound(130)
        SoundEvent(root=self, group='voice_100', sound_name=voice_sound.get_nickname())
        self.add_group('voice_106', time=65)
        select_dialogue(self, 4, 'Msn4Final', 'm04_final')
        self.groups.pop('motion_140', None)
        obj_Char_trent.facial(group='voice_106', index=140, append=False, auto_lip=True, extra_delay=0)
        restore_dialogue(self)
