"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Actor_obj_Char_trooper1(actors.Actor):
    NAME = 'trooper1'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'ms4_trooper1'
    GAME_ACTOR = 'Trooper1'


class Actor_obj_Char_trooper2(actors.Actor):
    NAME = 'trooper2'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'ms4_trooper2'
    GAME_ACTOR = 'Trooper2'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm04_offer'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_DX_m04_offer_0070_trent = Sound(root=self, name='DX_m04_offer_0070_trent', sound='DX_m04_offer_0070_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0070_trent, {'template_name': 'DX_m04_offer_0070_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0080_jacobo = Sound(root=self, name='DX_m04_offer_0080_jacobo', sound='DX_m04_offer_0080_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0080_jacobo, {'template_name': 'DX_m04_offer_0080_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0090_trent = Sound(root=self, name='DX_m04_offer_0090_trent', sound='DX_m04_offer_0090_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0090_trent, {'template_name': 'DX_m04_offer_0090_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_trooper1 = Character(root=self, actor=Actor_obj_Char_trooper1, light_group=0, init_point='Char_trooper1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trooper1, {'template_name': 'ms4_trooper1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Trooper1', 'category': 'Character'}})
        obj_Char_trooper2 = Character(root=self, actor=Actor_obj_Char_trooper2, light_group=0, init_point='Char_trooper2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trooper2, {'template_name': 'ms4_trooper2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Trooper2', 'category': 'Character'}})
        obj_Char_jacobo = Character(root=self, actor=actors.Jacobo, light_group=0, init_point='Char_jacobo', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jacobo, {'template_name': 'jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'jacobo'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_search = LookAtCamera(root=self, name='cam_search', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_search, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jacobo_appear = LookAtCamera(root=self, name='cam_jacobo_appear', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_jacobo_appear, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jacobo_sitting = LookAtCamera(root=self, name='cam_jacobo_sitting', fov=16, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_jacobo_sitting, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_sitting = LookAtCamera(root=self, name='cam_trent_sitting', fov=16, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_sitting, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 7, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 8, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=1.3, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 1.3
        # source event 11, 1.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.7
        # source event 16, 3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trooper1', anim=Male.Sc_MLBODY_WLKG_000LV_XB_01, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 17, 3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trooper2', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=15, time_scale=1, start_time=1, loop=True, trans_time=None)
        t += 0.6
        # source event 12, 3.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_1STEP_SIDWYSL_000LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.4
        # source event 13, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_1STEP_BKWD_PVOTR_090LV_XA_06, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 4
        # source event 9, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos3', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 14, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=1.1, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 1.1
        # source event 15, 13.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=1.89, time_scale=1, start_time=0, loop=True, trans_time=0.001)
        t += 1.9
        # source event 18, 15s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_search')
        # source event 19, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_search', target_name='automarker_cam_search_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 20, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_search_focus', target_name='automarker_cam_search_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_search', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 22, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.9, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 3.9
        # source event 23, 18.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=2.3, time_scale=1, start_time=0, loop=False, trans_time=0.1)
        t += 2.3
        # source event 24, 21.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_LOOK_AROU_CASL_000LV_XA_08, duration=6.3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5.8
        # source event 29, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_search', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 25, 27.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_090LV_XA_02, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 32, 29s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_appear')
        # source event 36, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=2.3, time_scale=1, start_time=0.45, loop=False, trans_time=None)
        t += 0.25
        # source event 31, 29.25s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jacobo', target_name='automarker_jacobo_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.75
        # source event 26, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_MOTION_MOUTH_CLENCH_TRENT_000LV_, duration=1.937, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 33, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_jacobo_appear', target_name='automarker_cam_jacobo_appear_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 27, 30.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=15, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        # source event 34, 30.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-15, axis='Y_AXIS', duration=1, smooth=True)
        main_group.append_time(32)

        # Line 10: source 32s; allocated facial window 3s.
        t = 0
        # source event 28, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=0.333, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 35, 33s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_180LV_XA_04, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_10', None)
        obj_Char_jacobo.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 30, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_sitting', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 39, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_STND_SITCL_TRNS_180DN_XA_06, duration=8, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(2)

        # Line 20: source 37s; allocated facial window 8.5s.
        t = 0
        # source event 40, 37s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit_around_jacobo', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 43, 37s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_sitting')
        t += 0.0011
        # source event 41, 37.0011s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.9989
        # source event 42, 39s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_sit', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_20', None)
        obj_Char_jacobo.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 30: source 45s; allocated facial window 8s.
        t = 0
        # source event 47, 45s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sitting')
        t += 5
        # source event 52, 50s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_sit', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 53, 50s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_trent_sit', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 60, 50s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=3, time_scale=2, start_time=1, loop=False, trans_time=1)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 40: source 52s; allocated facial window 10s.
        t = 0
        # source event 56, 52s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_sitting')
        # source event 61, 52s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_LOOK_RLLV_A_06, duration=3, time_scale=0.8, start_time=1, loop=False, trans_time=1)
        t += 3
        # source event 62, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_CONV_HNDS_CASL_000LV_xa_04, duration=4, time_scale=0.8, start_time=1, loop=True, trans_time=1)
        t += 1
        # source event 54, 56s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jacobo', target_name='automarker_jacobo_head_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 55, 56s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jacobo', target_name='automarker_jacobo_eye_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 3
        # source event 63, 59s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=5, time_scale=0.8, start_time=1, loop=False, trans_time=1)
        t += 1
        # source event 64, 60s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=15, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 65, 60s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=15, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 66, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo_sit', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 67, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo_sit', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_40', None)
        obj_Char_jacobo.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 50: source 61s; allocated facial window 11s.
        t = 0
        # source event 68, 61s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sitting')
        t += 4
        # source event 74, 65s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=4, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_50', None)
        obj_Char_trent.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 60: source 72s; allocated facial window 10s.
        t = 0
        # source event 75, 72s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_sitting')
        # source event 86, 72s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_TALK_HNSTBL_000LV_B_30, duration=26, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_60', None)
        obj_Char_jacobo.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 62: source 82s; allocated facial window 10s.
        t = 0
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_62', None)
        obj_Char_jacobo.facial(group=MAIN, index=62, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 65: source 92s; allocated facial window 9s.
        t = 0
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_65', None)
        obj_Char_jacobo.facial(group=MAIN, index=65, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 67: source 97s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        voice_sound = self.lookup_single_sound(67)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        t += 1
        # source event 87, 98s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(4.0)
        restore_dialogue(self)
