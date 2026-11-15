"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_offer'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_DX_m06_offer_0150_trent = Sound(root=self, name='DX_m06_offer_0150_trent', sound='DX_m06_offer_0150_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_offer_0150_trent, {'template_name': 'DX_m06_offer_0150_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_offer_0160_hatcher = Sound(root=self, name='DX_m06_offer_0160_hatcher', sound='DX_m06_offer_0160_hatcher', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_offer_0160_hatcher, {'template_name': 'DX_m06_offer_0160_hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_alaric, {'template_name': 'alaric', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Alaric', 'category': 'Character'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=0, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=30, farplane=5000, look_duration=30)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 30, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_arrive = LookAtCamera(root=self, name='cam_trent_arrive', fov=25, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_trent_arrive, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_greetings = LookAtCamera(root=self, name='cam_greetings', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_greetings, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher = LookAtCamera(root=self, name='cam_hatcher', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=22, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_friends = LookAtCamera(root=self, name='cam_friends', fov=22, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_friends, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric = LookAtCamera(root=self, name='cam_alaric', fov=22, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_alaric, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=0.01, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 13, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_IDLE_000LV_XB_04, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 17, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.8, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 23, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=3.8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 24, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=3.8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 28, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='Char_trent', duration=10, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 14, 2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_SITCR_TRNS_180DN_XA_06, duration=1.8, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.8
        # source event 18, 3.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        # source event 25, 3.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_arrive')
        t += 0.001
        # source event 15, 3.801s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='automarker_point_alaric_sit', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.01
        # source event 16, 3.811s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.189
        # source event 31, 4s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=200, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 32, 4s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=200, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(5)

        # Line 10: source 5s; allocated facial window 8s.
        t = 0
        t += 1
        # source event 33, 6s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_table_center', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 34, 6s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric_btm', duration=1.3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 20, 6.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=10, axis='Y_AXIS', duration=2, smooth=True)
        t += 0.5
        # source event 35, 7s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 36, 7s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 37, 7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 38, 7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 19, 7.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SITCR_TRNS_180DN_XA_06, duration=1, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.5)

        # Line 20: source 8.5s; allocated facial window 12s.
        t = 0
        # source event 39, 8.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_CONV_LHNDUP_TRNS_000LV_XA_02, duration=7, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        # source event 45, 8.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_greetings')
        t += 0.001
        # source event 21, 8.501s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.01
        # source event 22, 8.511s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.489
        # source event 40, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_CONV_LHND_CASL_000LV_xa_03, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2.0
        # source event 41, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_CONV_LHNDDN_TRNS_000LV_XA_02, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=2)
        t += 0.5
        # source event 43, 13.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_greetings', target_name='automarker_cam_greetings_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 44, 13.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_greetings_focus', target_name='automarker_cam_greetings_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 29, 15s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=200, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 30, 15s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=200, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 54, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_hatcher', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 55, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_hatcher', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_20', None)
        obj_Char_alaric.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.0)

        # Line 30: source 15.5s; allocated facial window 17.5s.
        t = 0
        t += 1.0
        # source event 42, 16.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=25, time_scale=1, start_time=0, loop=True, trans_time=2)
        t += 1.0
        # source event 48, 17.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 49, 17.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 56, 17.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 2.5
        # source event 50, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=1.75, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 51, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric_near', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.8
        # source event 79, 21.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_MOTION_MOUTH_CLENCH_000LV_, duration=1, time_scale=1, start_time=0, loop=False, trans_time=0.4)
        t += 0.2
        # source event 52, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 53, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 72, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_greetings', target_name='automarker_cam_greetings_pos3', duration=30, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 80, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=0.5, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_30', None)
        obj_Char_hatcher.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.0)

        # Line 40: source 24s; allocated facial window 12.2s.
        t = 0
        # source event 73, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=4, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 60, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 61, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric_near', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 74, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=8, time_scale=0.6, start_time=0, loop=True, trans_time=1)
        t += 5
        # source event 62, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 63, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 75, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CONV_LHNDUP_TRNS_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_40', None)
        obj_Char_hatcher.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.2)

        # Line 50: source 36s; allocated facial window 15s.
        t = 0
        t += 0.7
        # source event 76, 36.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CONV_LHND_CASL_000LV_xa_03, duration=3, time_scale=0.5, start_time=0, loop=True, trans_time=1)
        t += 1.3
        # source event 64, 38s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 65, 38s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric_near', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.8
        # source event 77, 39.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CONV_LHNDDN_TRNS_000LV_XA_01, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 0.2
        # source event 66, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 67, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 88, 41s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=0.5, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 3
        # source event 68, 44s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 69, 44s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric_near', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 78, 45s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 91, 45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 92, 45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 70, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 71, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_50', None)
        obj_Char_hatcher.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 60: source 50.5s; allocated facial window 18.3s.
        t = 0
        # source event 93, 50.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 94, 50.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 6.0
        # source event 95, 56.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=3, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 98, 57.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_GESTR_FIST_000LV_00, duration=4, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 3.0
        # source event 96, 60.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=7, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 99, 61.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Female.Sc_FMHAND_NEUT_RGHT_000LV_A_00, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2.5
        # source event 97, 64s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.3)

        # Line 70: source 66.5s; allocated facial window 13.5s.
        t = 0
        # source event 106, 66.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 107, 66.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TILT_HEAD_QUZZCLLY_000LV_XA_04, duration=4, time_scale=0.6, start_time=1, loop=False, trans_time=None)
        t += 2.0
        # source event 108, 68.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 2.0
        # source event 109, 70.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=2, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 2.0
        # source event 110, 72.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 4.0
        # source event 111, 76.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=4, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_70', None)
        obj_Char_hatcher.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 80: source 77.5s; allocated facial window 10.8s.
        t = 0
        t += 2.0
        # source event 112, 79.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TILT_HEAD_QUZZCLLY_000LV_XA_04, duration=2, time_scale=0.6, start_time=1, loop=False, trans_time=1)
        t += 2.0
        # source event 113, 81.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=5, time_scale=1, start_time=0, loop=True, trans_time=3)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_80', None)
        obj_Char_hatcher.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.8)

        # Line 90: source 85.5s; allocated facial window 15s.
        t = 0
        # source event 123, 85.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 124, 85.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=8, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11.0)

        # Line 100: source 89.5s; allocated facial window 12.7s.
        t = 0
        # source event 127, 89.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 128, 89.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 129, 89.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric_near', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4.0
        # source event 134, 93.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 130, 94s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 131, 94s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 5.0
        # source event 132, 99s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 133, 99s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric_near', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 141, 100s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_100', None)
        obj_Char_hatcher.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.7)

        # Line 110: source 101.5s; allocated facial window 5.7s.
        t = 0
        # source event 140, 101.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        # source event 144, 101.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_SHRG_SHLDRS_BIG_000LV_XA_03, duration=1.25, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 1.25
        # source event 145, 102.75s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=6, time_scale=0.6, start_time=0, loop=True, trans_time=2.2)
        t += 0.25
        # source event 142, 103s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_hatcher_near', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.0
        # source event 152, 105s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_alaric_near_far', duration=0.01, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 153, 105s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric_near', duration=0.01, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.8
        # source event 143, 105.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_110', None)
        obj_Char_alaric.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 150, 107.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=2, time_scale=1, start_time=0, loop=False, trans_time=2)
        main_group.append_time(0.3)

        # Line 120: source 107.5s; allocated facial window 14.1s.
        t = 0
        # source event 151, 107.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 1.0
        # source event 154, 108.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 155, 108.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 6.5
        # source event 163, 115s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 164, 115s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.0
        # source event 169, 117s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=2, time_scale=0.5, start_time=1.2, loop=False, trans_time=None)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_120', None)
        obj_Char_trent.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.1)

        # Line 130: source 117.5s; allocated facial window 14.5s.
        t = 0
        # source event 161, 117.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 162, 117.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_greetings', target_name='automarker_cam_greetings_pos3', duration=18, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.2
        # source event 170, 119.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 4.8
        # source event 165, 124.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 166, 124.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 171, 125s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=15, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 2.5
        # source event 167, 127.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 168, 127.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_130', None)
        obj_Char_hatcher.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 140: source 131.5s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 6, 'Msn6Offer', 'm06_offer')
        self.groups.pop('motion_140', None)
        obj_Char_hatcher.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)
        restore_dialogue(self)
