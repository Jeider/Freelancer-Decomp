"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm03_offer_accept'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_hassler = Character(root=self, actor=actors.Hassler, light_group=0, init_point='Char_hassler', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hassler, {'template_name': 'hassler', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'hassler'}})
        obj_Char_wilham = Character(root=self, actor=actors.Wilham, light_group=0, init_point='Char_wilham', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_wilham, {'template_name': 'wilham', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'wilham'}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_far = LookAtCamera(root=self, name='cam_trent_far', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hassler_near = LookAtCamera(root=self, name='cam_hassler_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hassler_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hassler_far = LookAtCamera(root=self, name='cam_hassler_far', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hassler_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wilham_near = LookAtCamera(root=self, name='cam_wilham_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_wilham_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = LookAtCamera(root=self, name='cam_final', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        # source event 8, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_head_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 9, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_eye_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 10, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hassler', target_name='automarker_hassler_head_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 11, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hassler', target_name='automarker_hassler_eye_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 12, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=73, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 13, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=73, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_LSTN_SMALL_000LV_A_34, duration=35, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 15, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_LSTN_SMALL_000LV_B_09, duration=16, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 16, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        main_group.append_time(1)

        # Line 100: source 1s; allocated facial window 14.5s.
        t = 0
        t += 3
        # source event 17, 4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=10, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        # source event 18, 4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hassler_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 19, 4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hassler', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4
        # source event 20, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_half', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 5
        # source event 22, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hassler_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 23, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hassler', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 32, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent_half', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 33, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 34, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_hassler_half', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_hassler', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_100', None)
        obj_Char_trent.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 110: source 16s; allocated facial window 13s.
        t = 0
        # source event 36, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hassler_far', target_name='automarker_cam_hassler_far_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 38, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hassler_far_focus', target_name='automarker_cam_hassler_far_marker_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 40, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hassler_far')
        t += 1
        # source event 43, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CONV_HNDSUP_TRNS_000LV_XA_00, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 1.5
        # source event 44, 18.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CONV_HNDS_CASL_000LV_xc_01, duration=4.5, time_scale=0.5, start_time=0, loop=True, trans_time=1.5)
        t += 4.5
        # source event 45, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 3
        # source event 46, 26s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        # Duplicate source sound event 51, same timestamp.
        SoundEvent(root=self, group=MAIN, sound_name=self.lookup_single_sound(110).get_nickname())
        self.groups.pop('motion_110', None)
        obj_Char_hassler.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 115: source 29s; allocated facial window 13.8s.
        t = 0
        t += 1
        # source event 60, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent_half', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 61, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 39, 31s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hassler_far', target_name='automarker_cam_hassler_far_pos3', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 10
        # source event 47, 41s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_wilham_half', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 48, 41s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_wilham', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 62, 41.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHEAD_MAD_SNARL_000LV_XA_, duration=5.5, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 0.5
        # source event 63, 42s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_hassler', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 64, 42s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_hassler', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_115', None)
        obj_Char_hassler.facial(group=MAIN, index=115, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.2
        # source event 59, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wilham_near')
        t += 2.0
        # source event 49, 45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 50, 45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 65, 45.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hassler_near')
        main_group.append_time(3.7)

        # Line 120: source 46.5s; allocated facial window 20s.
        t = 0
        # source event 66, 46.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 68, 46.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hassler_near', target_name='automarker_cam_hassler_near_pos2', duration=20, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 8.5
        # source event 67, 55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=10, time_scale=0.3, start_time=0, loop=False, trans_time=1)
        t += 9.0
        # source event 74, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 75, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_120', None)
        obj_Char_hassler.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 130: source 66.5s; allocated facial window 9s.
        t = 0
        # source event 78, 66.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        t += 1.5
        # source event 82, 68s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=10, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2.0
        # source event 76, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_half', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 77, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3.0
        # source event 87, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_final', target_name='automarker_cam_final_pos2', duration=20, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 88, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_final_focus', target_name='automarker_cam_final_marker_pos2', duration=20, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 89, 73s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_130', None)
        obj_Char_trent.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 140: source 73.5s; allocated facial window 3s.
        t = 0
        # source event 93, 73.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_GESTR_THMBSUP_000LV_XA_02, duration=25, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        # source event 94, 73.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHAND_HNEUT_GESTR_THUMB_000LV_00, duration=25, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_140', None)
        obj_Char_wilham.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 150: source 76s; allocated facial window 9.5s.
        t = 0
        # source event 83, 76s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_hassler_half', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 84, 76s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_hassler', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 85, 76s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_hassler', duration=90, transition_duration=1, target_type='PART', target_part='Body_Neck', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 86, 76s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_hassler', duration=90, transition_duration=1, target_type='PART', target_part='Body_Neck', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.25
        # source event 95, 76.25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_IDLE_MED_000LV_xa_05, duration=10, time_scale=0.5, start_time=0, loop=True, trans_time=0.5)
        t += 0.25
        # source event 92, 76.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=10, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 6.5
        # source event 99, 83s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', angle=-10, axis='Y_AXIS', duration=3, smooth=True)
        t += 2
        # source event 100, 85s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_TURN_045LV_XA_04, duration=25, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_150', None)
        obj_Char_hassler.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 155: source 86s; allocated facial window 7s.
        t = 0
        t += 1
        # source event 112, 87s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_315LV_XA_02, duration=25, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 113, 90s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=20, axis='Y_AXIS', duration=2, smooth=True)
        t += 2
        # source event 106, 92s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_head_ik', target_name='automarker_way_out', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 107, 92s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hassler_eye_ik', target_name='automarker_way_out', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 108, 92s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=25, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        # source event 114, 92s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_315LV_XA_02, duration=25, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 3, 'Msn3Offer', 'm03_offer')
        self.groups.pop('motion_155', None)
        obj_Char_hassler.facial(group=MAIN, index=155, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 104, 93s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_way_out', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 105, 93s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_way_out', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 110, 93s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=25, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 0.42
        # source event 109, 93.42s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=25, time_scale=0.75, start_time=0, loop=True, trans_time=0.01)
        t += 1.0
        # source event 111, 94.42s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=25, time_scale=0.75, start_time=0, loop=True, trans_time=0.01)
        main_group.append_time(5.0)
        restore_dialogue(self)
