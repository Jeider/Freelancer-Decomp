"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_mount'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_alaric, {'template_name': 'alaric', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Alaric', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=30)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=20, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric = LookAtCamera(root=self, name='cam_alaric', fov=20, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_alaric, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = LookAtCamera(root=self, name='cam_final', fov=26, farplane=5000, look_duration=111)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 26, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 5, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 6, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 7, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=6, time_scale=0.75, start_time=0.73, loop=True, trans_time=None)
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=8.5, time_scale=0.75, start_time=0, loop=True, trans_time=None)
        main_group.append_time(2)

        # Line 10: source 2s; allocated facial window 15s.
        t = 0
        # source event 9, 2s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=25, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11)

        # Line 20: source 6s; allocated facial window 12s.
        t = 0
        # source event 11, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=0.1)
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_20', None)
        obj_Char_alaric.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11)

        # Line 30: source 7s; allocated facial window 15s.
        t = 0
        t += 1
        # source event 15, 8s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-10, axis='Y_AXIS', duration=1, smooth=True)
        t += 0.5
        # source event 13, 8.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 8, 9s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='Char_trent', duration=25, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 14, 9s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', angle=35, axis='Y_AXIS', duration=1, smooth=True)
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11.5)

        # Line 40: source 10.5s; allocated facial window 12s.
        t = 0
        # source event 22, 10.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_40', None)
        obj_Char_alaric.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.5)

        # Line 50: source 13s; allocated facial window 15s.
        t = 0
        # source event 25, 13s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_50', None)
        obj_Char_trent.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-12)

        # Line 60: source 16s; allocated facial window 12s.
        t = 0
        # source event 28, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        # source event 31, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_GESTR_THMBSUP_000LV_XA_02, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 32, 18.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_GEST_HNDS_WAIT_000LV_XA_02, duration=6, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_60', None)
        obj_Char_alaric.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.7)

        # Line 70: source 21.3s; allocated facial window 15s.
        t = 0
        # source event 33, 21.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 36, 21.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.8)

        # Line 80: source 25.5s; allocated facial window 16s.
        t = 0
        # source event 37, 25.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        # source event 42, 25.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_HOLD_HEAD_RLEASE_000LV_XA_01, duration=6, time_scale=0.8, start_time=0.4, loop=False, trans_time=None)
        t += 2.0
        # source event 43, 27.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=6, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 4.0
        # source event 44, 31.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=6, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 1.7
        # source event 41, 33.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=2, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_80', None)
        obj_Char_alaric.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.5)

        # Line 90: source 34s; allocated facial window 15s.
        t = 0
        # source event 45, 34s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        # source event 48, 34s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=6, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        # source event 51, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_final', target_name='automarker_cam_final_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 49, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_WALK_TRNS_180LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 50, 36s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Mount', 'm06_mount')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.0)
        restore_dialogue(self)
