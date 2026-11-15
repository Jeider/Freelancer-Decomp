"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm03_offer'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_hassler = Character(root=self, actor=actors.Hassler, light_group=0, init_point='Char_hassler', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hassler, {'template_name': 'hassler', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'hassler'}})
        obj_Char_wilham = Character(root=self, actor=actors.Wilham, light_group=0, init_point='Char_wilham', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_wilham, {'template_name': 'wilham', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'wilham'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_hands = LookAtCamera(root=self, name='cam_trent_hands', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_hands, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wilham_near = LookAtCamera(root=self, name='cam_wilham_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_wilham_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wilham_far = LookAtCamera(root=self, name='cam_wilham_far', fov=16, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_wilham_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_far = LookAtCamera(root=self, name='cam_trent_far', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_top = LookAtCamera(root=self, name='cam_top', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 9, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_head_ik', duration=19.5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 11, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_eye_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 12, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hassler', target_name='automarker_hassler_head_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 13, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hassler', target_name='automarker_hassler_eye_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 26, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 27, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 28, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_02, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 29, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=5, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 30, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        main_group.append_time(2)

        # Line 10: source 2s; allocated facial window 4.5s.
        t = 0
        # source event 14, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 15, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 76, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 77, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 16, 2.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 17, 2.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 20: source 4s; allocated facial window 12s.
        t = 0
        t += 1
        # source event 18, 5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_hassler_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 19, 5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_hassler_half', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 36, 5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_GESTR_RGHT_000LV_XA_02, duration=10, time_scale=0.4, start_time=0, loop=False, trans_time=1.5)
        # source event 38, 5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 39, 5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 20, 5.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 5.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_wilham_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.5
        # source event 22, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 23, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=7, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        # source event 40, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hassler', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 41, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hassler', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 24, 8.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 25, 8.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 42, 10s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=25, axis='Y_AXIS', duration=2, smooth=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_20', None)
        obj_Char_wilham.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5)

        # Line 30: source 11s; allocated facial window 4.5s.
        t = 0
        # source event 43, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SHAK_RHAND_000LV_XA_03, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 55, 11s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_hands')
        t += 0.3
        # source event 44, 11.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_SHAK_RGHT_000LV_A_03, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        t += 1.7
        # source event 54, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_hands_focus', target_name='automarker_cam_trent_hands_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 58, 13.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 59, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 60, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 61, 14s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-25, axis='Y_AXIS', duration=3, smooth=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 40: source 14.5s; allocated facial window 4.5s.
        t = 0
        t += 2.0
        # source event 64, 16.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 0.75
        # source event 65, 17.25s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wilham_far')
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 50: source 17.5s; allocated facial window 10s.
        t = 0
        t += 0.5
        # source event 45, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_LSTN_SMALL_000LV_A_34, duration=40, time_scale=0.5, start_time=0, loop=True, trans_time=1)
        t += 1.5
        # source event 68, 19.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_SHAKHEAD_NO_SLGHTLY_000LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 46, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        t += 1.2
        # source event 69, 21.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=1, time_scale=0.75, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_50', None)
        obj_Char_wilham.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.5)

        # Line 60: source 22s; allocated facial window 8.2s.
        t = 0
        # source event 70, 22s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        # source event 74, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=2.5, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 2.5
        # source event 75, 24.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=2.5, time_scale=0.5, start_time=0, loop=True, trans_time=0.25)
        t += 0.5
        # source event 47, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.2)

        # Line 70: source 30s; allocated facial window 8.5s.
        t = 0
        # source event 10, 30s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_head_ik', duration=40, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 48, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        # source event 86, 30s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', angle=10, axis='Y_AXIS', duration=1, smooth=True)
        # source event 89, 30s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wilham_far')
        t += 1
        # source event 99, 31s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_IDLE_MED_000LV_xa_05, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=2)
        t += 1
        # source event 87, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_wilham_far', target_name='automarker_cam_wilham_far_pos2', duration=23, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 88, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_wilham_far_focus', target_name='automarker_cam_wilham_far_marker_pos2', duration=23, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 100, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_CONV_HNDSUP_TRNS_000LV_XA_00, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 3
        # source event 49, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 78, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_hassler_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 79, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_hassler', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_70', None)
        obj_Char_wilham.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 75: source 37s; allocated facial window 16s.
        t = 0
        # source event 80, 37s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_wilham_half', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 81, 37s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_wilham', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 50, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        # source event 82, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent_half', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 83, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 84, 42s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 85, 42s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 101, 44s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_CONV_HNDS_CASL_000LV_xc_01, duration=8, time_scale=0.5, start_time=0, loop=True, trans_time=1.5)
        t += 1
        # source event 51, 45s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_75', None)
        obj_Char_wilham.facial(group=MAIN, index=75, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.8)

        # Line 77: source 49.2s; allocated facial window 11.8s.
        t = 0
        t += 0.8
        # source event 52, 50s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        t += 2.0
        # source event 102, 52s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 3.0
        # source event 53, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        # source event 122, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_GESTL_FIST_000LV_00, duration=1, time_scale=2, start_time=0, loop=False, trans_time=None)
        # source event 123, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_GESTR_FIST_000LV_00, duration=1, time_scale=2, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_77', None)
        obj_Char_wilham.facial(group=MAIN, index=77, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.0)

        # Line 80: source 58s; allocated facial window 3s.
        t = 0
        # source event 103, 58s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_top')
        # source event 115, 58s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_top', target_name='automarker_cam_top_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 116, 58s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_top_focus', target_name='automarker_cam_top_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 117, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_LSTN_SMALL_000LV_A_34, duration=3, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 121, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_LSTN_000DN_A_18, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 124, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_80', None)
        obj_Char_trent.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 111, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        # source event 118, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_GESTR_THMBSUP_000LV_XA_02, duration=5, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        # source event 119, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_CASL_000LV_00, duration=4, time_scale=1.5, start_time=3, loop=False, trans_time=0.5)
        main_group.append_time(0.5)

        # Line 90: source 61.5s; allocated facial window 12s.
        t = 0
        t += 0.5
        # source event 104, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hassler_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 105, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hassler', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 108, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent_half_right', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 125, 62s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 3.0
        # source event 106, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_half', duration=2.2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 107, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_wilham', duration=1.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 120, 65s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_TALK_SMALL_000DN_A_17, duration=15, time_scale=0.3, start_time=0, loop=True, trans_time=1)
        # source event 126, 65s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_LSTN_SMALL_000LV_B_09, duration=5, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_90', None)
        obj_Char_wilham.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.5)
        restore_dialogue(self)
