"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Actor_obj_Char_outcast(actors.Actor):
    NAME = 'outcast'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm03_deck_informer'
    GAME_ACTOR = 'outcast'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm03_reward'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_hassler = Character(root=self, actor=actors.Hassler, light_group=0, init_point='Char_hassler', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_hassler, {'template_name': 'hassler', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'hassler', 'category': 'Character'}})
        obj_Char_outcast = Character(root=self, actor=Actor_obj_Char_outcast, light_group=0, init_point='Char_outcast', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_outcast, {'template_name': 'm03_deck_informer', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=35, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 35, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hassler = LookAtCamera(root=self, name='cam_hassler', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hassler, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 7, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CONV_HNDSUP_TRNS_000LV_XA_00, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        # source event 13, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_outcast', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=3, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 18, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_LOOK_AROU_CASL_000LV_XA_08, duration=10, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 8, 1.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CONV_HNDS_CASL_000LV_xc_01, duration=2, time_scale=0.5, start_time=0, loop=True, trans_time=1.5)
        t += 1.5
        # source event 14, 3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_outcast', anim=Male.Sc_MLBODY_STND_SHAKHEAD_NO_SLGHTLY_000LV_XA_02, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 9, 3.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 2.5
        # source event 10, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_NOD_YES_SLGHTLY_000LV_XA_02, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        # source event 15, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_outcast', anim=Male.Sc_MLBODY_STND_SHRG_SHLDRS_SMALL_000LV_XA_01, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 5, 9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 6, 9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 11, 9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_WALK_TRNS_180LV_XA_02, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 16, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_outcast', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        # source event 19, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 20, 12s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hassler', target_name='automarker_head_trent', duration=31, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 21, 12s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_head_hassler', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.3
        # source event 12, 12.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=0.2)
        t += 0.2
        # source event 17, 12.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_outcast', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=33, time_scale=0.8, start_time=0, loop=True, trans_time=0.02)
        t += 1.5
        # source event 22, 14s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hassler')
        main_group.append_time(15)

        # Line 10: source 15s; allocated facial window 14s.
        t = 0
        t += 3
        # source event 27, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=10, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 3, 'Msn3Reward', 'm03_reward')
        self.groups.pop('motion_10', None)
        obj_Char_hassler.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 20: source 29s; allocated facial window 11s.
        t = 0
        # source event 28, 29s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 3
        # source event 34, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=2.5, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 5.25
        # source event 33, 37.25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 3, 'Msn3Reward', 'm03_reward')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 30: source 38s; allocated facial window 4s.
        t = 0
        # source event 35, 38s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hassler')
        t += 1
        # source event 39, 39s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=10, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 3, 'Msn3Reward', 'm03_reward')
        self.groups.pop('motion_30', None)
        obj_Char_hassler.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 38, 42s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=4, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 40, 43s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_STND_WALK_TRNS_090LV_XA_02, duration=10, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 2.5
        # source event 41, 45.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hassler', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=33, time_scale=0.8, start_time=0, loop=True, trans_time=0.02)
        main_group.append_time(4.0)
        restore_dialogue(self)
