"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Actor_obj_Char_bartender_Fixture(actors.Actor):
    NAME = 'bartender_fixture'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'li_bartender_1'
    GAME_ACTOR = 'bartender'


class Asset_obj_prop_cigarette_2(Prop):
    COMPOUND_TEMPLATE_NAME = 'cigarette_2'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_prisoner2b(actors.Actor):
    NAME = 'prisoner2b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner02b'
    GAME_ACTOR = 'Prisoner2b'


class Actor_obj_Char_prisoner3b(actors.Actor):
    NAME = 'prisoner3b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner03b'
    GAME_ACTOR = 'Prisoner3b'


class Actor_obj_Char_prisoner4b(actors.Actor):
    NAME = 'prisoner4b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner04b'
    GAME_ACTOR = 'Prisoner4b'


class Actor_obj_Char_trent_base(actors.Actor):
    NAME = 'trent_base'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'trent'
    GAME_ACTOR = 'Player'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_offer'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_prop_cigarette_2 = Asset_obj_prop_cigarette_2(root=self, name='prop_cigarette_2', light_group=0, init_point='prop_cigarette_2', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_prop_cigarette_2, {'template_name': 'cigarette_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_DX_m07_offer_0110_trent = Sound(root=self, name='DX_m07_offer_0110_trent', sound='DX_m07_offer_0110_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0110_trent, {'template_name': 'DX_m07_offer_0110_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_delta = Character(root=self, actor=actors.DeltaOne, light_group=0, init_point='Char_delta1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_delta, {'template_name': 'm06_asf_prisoner01b', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner1b', 'category': 'Character'}})
        obj_Char_prisoner2b = Character(root=self, actor=Actor_obj_Char_prisoner2b, light_group=0, init_point='Char_prisoner2b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner2b, {'template_name': 'm06_asf_prisoner02b', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner2b', 'category': 'Character'}})
        obj_Char_prisoner3b = Character(root=self, actor=Actor_obj_Char_prisoner3b, light_group=0, init_point='Char_prisoner3b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner3b, {'template_name': 'm06_asf_prisoner03b', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner3b', 'category': 'Character'}})
        obj_Char_prisoner4b = Character(root=self, actor=Actor_obj_Char_prisoner4b, light_group=0, init_point='Char_prisoner4b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner4b, {'template_name': 'm06_asf_prisoner04b', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner4b', 'category': 'Character'}})
        obj_Char_trent_base = Character(root=self, actor=Actor_obj_Char_trent_base, light_group=0, init_point='Char_trent_base', rotate_from_quat=True, use_ambient=False, floor_height=-1000)
        preserve_entity(obj_Char_trent_base, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': -1000}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent_original', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'TrentOriginal', 'category': 'Character'}})
        obj_Char_barman = Character(root=self, actor=actors.CorsairBarman, light_group=0, init_point='Char_barman', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_barman, {'template_name': 'm07_bartender', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'm6_bartender', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_delta_sit_trent_sit_down = LookAtCamera(root=self, name='cam_delta_sit_trent_sit_down', fov=16, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_delta_sit_trent_sit_down, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_delta_sit = LookAtCamera(root=self, name='cam_delta_sit', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_delta_sit, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_sit = LookAtCamera(root=self, name='cam_trent_sit', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_sit, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_delta_explaining = LookAtCamera(root=self, name='cam_delta_explaining', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_delta_explaining, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_delta_warning = LookAtCamera(root=self, name='cam_delta_warning', fov=15, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_delta_warning, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_standup = LookAtCamera(root=self, name='cam_trent_standup', fov=15, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_trent_standup, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_barman = LookAtCamera(root=self, name='cam_barman', fov=15, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_barman, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_second_start = LookAtCamera(root=self, name='cam_second_start', fov=15, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_second_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_deal = LookAtCamera(root=self, name='cam_trent_deal', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_deal, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 11, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender_fixture', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 12, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_base', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=4, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 15, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 16, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 17, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 22, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 24, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 25, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 28, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_delta1', duration=25, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 29, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='Char_trent', duration=25, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.01
        # source event 13, 0.01s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_base', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=1, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1.99
        # source event 20, 2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', anim=Male.Sc_MLBODY_CHRB_TWSTU_CCL_LESS_000LV_A_14, duration=21, time_scale=1, start_time=7, loop=False, trans_time=1)
        # source event 23, 2s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=28, axis='Y_AXIS', duration=4, smooth=True)
        # source event 26, 2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 18, 4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', anim=Male.Sc_MLBODY_CHRF_TWSTS_LOOK_090LV_XA_02, duration=21, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 21, 4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 27, 5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner4b', target_name='Char_trent', duration=5, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(10)

        # Line 10: source 10s; allocated facial window 13.3s.
        t = 0
        # source event 19, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', anim=Male.Sc_MLBODY_CHRF_TWSTS_FROM_090LV_XA_02, duration=21, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 30, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit_down', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 32, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_delta_sit_trent_sit_down')
        # source event 35, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_TAP_RHND_000LV_A_02, duration=17, time_scale=0.3, start_time=0, loop=True, trans_time=1)
        t += 0.01
        # source event 31, 10.01s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SITCR_TRNS_180DN_XA_06, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.99
        # source event 33, 11s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_delta_sit_trent_sit_down', target_name='automarker_cam_delta_sit_trent_sit_down_pos2', duration=13, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 34, 11s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_delta_sit_trent_sit_down_focus', target_name='automarker_cam_delta_sit_trent_sit_down_marker_pos2', duration=13, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4
        # source event 36, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=15, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 7.9
        # source event 41, 22.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=4.444, time_scale=0.9, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_10', None)
        obj_Char_delta.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.2)

        # Line 20: source 23.5s; allocated facial window 6s.
        t = 0
        # source event 42, 23.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 30: source 28s; allocated facial window 11s.
        t = 0
        # source event 45, 28s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_delta_explaining')
        # source event 46, 28s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_delta_explaining', target_name='automarker_cam_delta_explaining_pos2', duration=20, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 63, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_TALK_HNSTBL_000LV_A_34, duration=20, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        # source event 69, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07, duration=62, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 70, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_IDLE_BIG_000LV_XA_06, duration=10, time_scale=0.6, start_time=2, loop=True, trans_time=None)
        # source event 79, 28s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_cigarette_2', parent_name='Char_prisoner4b', duration=50, target_hardpoint='hprightconnect_cigarette', parent_hardpoint='hprightconnect')
        # source event 80, 28s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='Char_trent', duration=72, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 81, 28s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='Char_trent', duration=72, transition_duration=4, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 10
        # source event 51, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=1, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        # source event 71, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_TAP_RHND_000LV_A_02, duration=5, time_scale=0.4, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_30', None)
        obj_Char_delta.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 40: source 39s; allocated facial window 12s.
        t = 0
        t += 4
        # source event 72, 43s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 55, 46s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=1, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_40', None)
        obj_Char_delta.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 50: source 47s; allocated facial window 12.5s.
        t = 0
        # source event 73, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_CHIN_HOLDR_000LV_XA_03, duration=5, time_scale=0.5, start_time=0, loop=True, trans_time=0.5)
        t += 1
        # source event 64, 48s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=15, time_scale=1, start_time=0, loop=True, trans_time=3)
        t += 4
        # source event 74, 52s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 47, 53s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_delta_explaining', target_name='automarker_cam_delta_explaining_pos3', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 65, 54s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=2, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_50', None)
        obj_Char_delta.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.5)

        # Line 60: source 55s; allocated facial window 18s.
        t = 0
        t += 1
        # source event 66, 56s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CONV_RHND_CASL_000LV_XA_04, duration=3.7, time_scale=0.75, start_time=0, loop=True, trans_time=0.25)
        # source event 75, 56s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_TAP_RHND_000LV_A_02, duration=5, time_scale=0.4, start_time=0, loop=True, trans_time=1)
        t += 3
        # source event 67, 59s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 76, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2.5
        # source event 68, 63.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=15, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 77, 65s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_CHIN_HOLDR_000LV_XA_03, duration=5, time_scale=0.5, start_time=0, loop=True, trans_time=0.5)
        t += 4
        # source event 78, 69s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_60', None)
        obj_Char_delta.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 70: source 71s; allocated facial window 6s.
        t = 0
        # source event 82, 71s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 90: source 74s; allocated facial window 14s.
        t = 0
        # source event 85, 74s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_delta_warning')
        # source event 87, 74s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 1
        # source event 88, 75s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=2, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        t += 2
        # source event 89, 77s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CONV_RHND_CASL_000LV_XA_04, duration=3.7, time_scale=0.75, start_time=0, loop=True, trans_time=0.25)
        t += 3
        # source event 90, 80s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 4
        # source event 86, 84s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_delta_warning', target_name='automarker_cam_delta_warning_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_90', None)
        obj_Char_delta.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 100: source 84.5s; allocated facial window 11s.
        t = 0
        t += 0.5
        # source event 91, 85s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=15, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 3.0
        # source event 117, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_IDLE_BART_000LV_XA_10, duration=12, time_scale=0.8, start_time=1, loop=True, trans_time=None)
        t += 1.0
        # source event 92, 89s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_090LV_XA_10, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 103, 90s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_standup', target_name='automarker_cam_trent_standup_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 104, 90s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_standup_focus', target_name='automarker_cam_trent_standup_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.0
        # source event 95, 92s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-97, axis='Y_AXIS', duration=5, smooth=True)
        t += 1.0
        # source event 102, 93s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_standup')
        t += 1.15
        # source event 93, 94.15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=5.2, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 6, 'Msn6Freeport', 'm06_freeport')
        self.groups.pop('motion_100', None)
        obj_Char_delta.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 2.5
        # source event 116, 98s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_head_barman_near', duration=100, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.35
        # source event 94, 99.35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        main_group.append_time(4.5)

        # Line 10: source 100s; allocated facial window 4.7s.
        t = 0
        # source event 105, 100s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_090LV_XA_10, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 112, 100s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_second_start')
        # source event 113, 100s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_second_start', target_name='automarker_cam_second_start_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 114, 100s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_second_start_focus', target_name='automarker_cam_second_start_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 115, 100s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_barman', target_name='Char_trent', duration=55, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 118, 100s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=100, time_scale=0.8, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_10', None)
        obj_Char_barman.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.2)

        # Line 20: source 101.5s; allocated facial window 6s.
        t = 0
        t += 0.5
        # source event 106, 102s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_270LV_XA_10, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 121, 102s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 30: source 105.5s; allocated facial window 6s.
        t = 0
        # source event 124, 105.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_barman')
        t += 0.5
        # source event 107, 106s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 108, 106s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 109, 106s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 2.0
        # source event 110, 108s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', target_name='automarker_point_delta_walkout', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_30', None)
        obj_Char_barman.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 40: source 110.5s; allocated facial window 9.5s.
        t = 0
        # source event 111, 110.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=55, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 127, 110.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_deal')
        t += 1.5
        # source event 131, 112s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.0)

        # Line 50: source 117s; allocated facial window 6s.
        t = 0
        # source event 132, 117s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_second_start')
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_50', None)
        obj_Char_barman.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.7)

        # Line 60: source 118.3s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.8)

        # Line 70: source 119.5s; allocated facial window 6s.
        t = 0
        # source event 137, 119.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_barman')
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_70', None)
        obj_Char_barman.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 80: source 122s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_80', None)
        obj_Char_barman.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 90: source 127s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_90', None)
        obj_Char_barman.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 100: source 133s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_100', None)
        obj_Char_barman.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.0)
        restore_dialogue(self)
