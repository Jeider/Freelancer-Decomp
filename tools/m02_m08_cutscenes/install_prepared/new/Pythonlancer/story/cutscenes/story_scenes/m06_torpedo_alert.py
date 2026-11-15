"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Actor_obj_Char_li_trooper01(actors.Actor):
    NAME = 'li_trooper01'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_dread_military_1'
    GAME_ACTOR = 'li_troop01'


class Actor_obj_Char_li_trooper02(actors.Actor):
    NAME = 'li_trooper02'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_dread_military_2'
    GAME_ACTOR = 'li_troop02'


class Actor_obj_Char_assist(actors.Actor):
    NAME = 'assist'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_dread_military_2'
    GAME_ACTOR = 'li_troop03'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_torpedo_alert'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_alarm = Sound(root=self, name='alarm', sound='rtc_klaxon_loop_3', attenuation=-10, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_alarm, {'template_name': 'rtc_klaxon_loop_3', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=0, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_Char_li_trooper01 = Character(root=self, actor=Actor_obj_Char_li_trooper01, light_group=0, init_point='Char_li_trooper01', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_li_trooper01, {'template_name': 'm06_dread_military_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'li_troop01', 'category': 'Character'}})
        obj_Char_li_trooper02 = Character(root=self, actor=Actor_obj_Char_li_trooper02, light_group=0, init_point='Char_li_trooper02', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_li_trooper02, {'template_name': 'm06_dread_military_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'li_troop02', 'category': 'Character'}})
        obj_Char_assist = Character(root=self, actor=Actor_obj_Char_assist, light_group=0, init_point='Char_assist', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_assist, {'template_name': 'm06_dread_military_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'li_troop03', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=30)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher = LookAtCamera(root=self, name='cam_hatcher', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=20, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = LookAtCamera(root=self, name='cam_final', fov=22, farplane=5000, look_duration=111)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 5, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        t += 1
        # source event 53, 1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='alarm', duration=40, start_time=0, loop=True)
        t += 1
        # source event 6, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 7, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 54, 4s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='alarm', duration=2, attenuation=-20)
        t += 2
        # source event 11, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_trooper01', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=25, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 12, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_trooper02', anim=Male.Sc_MLBODY_RNNG_000LV_XA_01, duration=25, time_scale=0.6, start_time=0.4, loop=True, trans_time=None)
        # source event 13, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=7, time_scale=1, start_time=0.73, loop=True, trans_time=None)
        t += 4
        # source event 28, 10s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=29.5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 16, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Male.GENERIC_ANIM, duration=10, start_time=0, time_scale=0.8, trans_time=0.25)
        # source event 17, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDS_EMPH_000LV_XA_04, duration=3, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 21, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assist', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 55, 12s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='alarm', duration=2, attenuation=-40)
        t += 1
        # source event 8, 13s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 9, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 10, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_marker_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 14, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=0.1)
        t += 2
        # source event 15, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 18, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_EMPH_HNDSDN_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        # source event 22, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assist', anim=Male.Sc_MLBODY_STND_SALUT_000LV_XA_03, duration=5, time_scale=1.25, start_time=0, loop=False, trans_time=0.8)
        t += 1
        # source event 19, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_POINTR_OVRTHRE_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 23, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assist', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 26, 17s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assist', angle=15, axis='Y_AXIS', duration=2, smooth=True)
        t += 1
        # source event 20, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TURN_270LV_XA_03, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 24, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assist', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=1, time_scale=1, start_time=0, loop=True, trans_time=None)
        main_group.append_time(20)

        # Line 10: source 20s; allocated facial window 6.5s.
        t = 0
        # source event 25, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_assist', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=15, time_scale=2, start_time=1, loop=True, trans_time=None)
        # source event 27, 20s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=35, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 56, 20s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='alarm', duration=10, attenuation=-100)
        t += 1
        # source event 38, 21s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=3, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 3
        # source event 39, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDSUP_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 32, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=0.5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        # source event 40, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDS_CASL_000LV_xa_03, duration=4, time_scale=1, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 6, 'Msn6TorpedoAlert', 'm06_torpedo_alert')
        self.groups.pop('motion_10', None)
        obj_Char_hatcher.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 20: source 25.5s; allocated facial window 5.8s.
        t = 0
        t += 3.5
        # source event 41, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1.9
        # source event 37, 30.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6TorpedoAlert', 'm06_torpedo_alert')
        self.groups.pop('motion_20', None)
        obj_Char_hatcher.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.3)

        # Line 40: source 31s; allocated facial window 15s.
        t = 0
        # source event 42, 31s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 43, 31s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_ATEASE_RLEASE_000LV_XA_01, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6TorpedoAlert', 'm06_torpedo_alert')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-12)

        # Line 50: source 34s; allocated facial window 7s.
        t = 0
        # source event 46, 34s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        # source event 50, 34s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDSUP_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 51, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDS_CASL_000LV_xa_03, duration=3.5, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 3.5
        # source event 52, 38.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=0.5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6TorpedoAlert', 'm06_torpedo_alert')
        self.groups.pop('motion_50', None)
        obj_Char_hatcher.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)
        restore_dialogue(self)
