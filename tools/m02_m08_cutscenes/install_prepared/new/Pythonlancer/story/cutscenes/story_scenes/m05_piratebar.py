"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_prop_cigarette_2(Prop):
    COMPOUND_TEMPLATE_NAME = 'cigarette_2'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_pda(Prop):
    COMPOUND_TEMPLATE_NAME = 'pda'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_piratebar'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_vfx_rtc_sydsmoke_3 = Alchemy(root=self, name='vfx_rtc_sydsmoke_3', particles='rtc_sydsmoke', point_name='vfx_rtc_sydsmoke_3', sparam=0)
        preserve_entity(obj_vfx_rtc_sydsmoke_3, {'template_name': 'rtc_sydsmoke', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_vfx_rtc_cigaretteglow_4 = Alchemy(root=self, name='vfx_rtc_cigaretteglow_4', particles='rtc_cigaretteglow', point_name='vfx_rtc_cigaretteglow_4', sparam=0)
        preserve_entity(obj_vfx_rtc_cigaretteglow_4, {'template_name': 'rtc_cigaretteglow', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_prop_cigarette_2 = Asset_obj_prop_cigarette_2(root=self, name='prop_cigarette_2', light_group=0, init_point='prop_cigarette_2', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_prop_cigarette_2, {'template_name': 'cigarette_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_prop_pda = Asset_obj_prop_pda(root=self, name='prop_pda', light_group=0, init_point='prop_pda', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_pda, {'template_name': 'pda', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Char_smith = Character(root=self, actor=actors.Smith, light_group=0, init_point='Char_smith', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_smith, {'template_name': 'm05_smith', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'm05_smith', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_stand = LookAtCamera(root=self, name='cam_trent_stand', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_stand, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_smith = LookAtCamera(root=self, name='cam_smith', fov=18, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_smith, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_smith_far = LookAtCamera(root=self, name='cam_smith_far', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_smith_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=18, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trough = LookAtCamera(root=self, name='cam_trough', fov=30, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trough, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 30, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_sidetalk = LookAtCamera(root=self, name='cam_trent_sidetalk', fov=18, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_sidetalk, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['vfx_rtc_sydsmoke_3', 'prop_cigarette_2'], duration=200, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HP_cigarette_Tip_smoke', target_type='HARDPOINT', flags='POSITION')
        # source event 1, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['vfx_rtc_cigaretteglow_4', 'prop_cigarette_2'], duration=200, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HP_cigarette_Tip_smoke', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 2, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='vfx_rtc_cigaretteglow_4', duration=105)
        # source event 3, 0s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='vfx_rtc_sydsmoke_3', duration=105)
        # source event 4, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 6, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_cigarette_2', parent_name='Char_smith', duration=105, target_hardpoint='hprightconnect_cigarette2', parent_hardpoint='hprightconnect')
        # source event 16, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 17, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 18, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.9, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 25, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_MILI_000LV_00, duration=0.5, time_scale=10, start_time=0, loop=False, trans_time=None)
        # source event 27, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 19, 1s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=2, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 28, 2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.3)
        t += 1.9
        # source event 22, 3.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 29, 4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CHIN_HOLDR_000LV_XA_03, duration=4, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 2.2
        # source event 23, 6.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=4, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 0.8
        # source event 20, 7s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=24, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 24, 7s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=45, axis='Y_AXIS', duration=2, smooth=True)
        t += 1
        # source event 30, 8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 26, 9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(10)

        # Line 10: source 10s; allocated facial window 8s.
        t = 0
        # source event 31, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_stand')
        # source event 32, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WAVE_RHND_000LV_XA_02, duration=1.5, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        t += 1.5
        # source event 33, 11.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TALK_SMALL_000DN_A_17, duration=6.5, time_scale=0.75, start_time=0, loop=False, trans_time=2)
        t += 0.5
        # source event 34, 12s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=25, axis='Y_AXIS', duration=2.5, smooth=True)
        # source event 43, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 4
        # source event 41, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_MILI_000LV_00, duration=0.5, time_scale=10, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 44, 16.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CHIN_HOLDR_000LV_XA_03, duration=1.5, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.5
        # source event 40, 17s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith_far')
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 45, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(0.5)

        # Line 20: source 18.5s; allocated facial window 5.5s.
        t = 0
        # source event 42, 18.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 37, 20s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_smith', target_name='automarker_smith_head_ik', duration=7, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 3.0
        # source event 38, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_smith_head_ik', target_name='automarker_head_smith_front_btm', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_20', None)
        obj_Char_smith.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 49, 24s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_stand')
        # source event 61, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_out_window_center', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 63, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        main_group.append_time(1.0)

        # Line 30: source 25s; allocated facial window 15s.
        t = 0
        # source event 39, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_smith_head_ik', target_name='automarker_head_smith_front', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 62, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_smith', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 64, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 54, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_MILI_000LV_00, duration=0.5, time_scale=10, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 65, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SITCL_TRNS_180DN_XA_06, duration=3.4, time_scale=0.85, start_time=0, loop=False, trans_time=0.25)
        t += 3
        # source event 56, 33s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.4
        # source event 50, 33.4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trough')
        # source event 51, 33.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trough', target_name='automarker_cam_trough_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 52, 33.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trough_focus', target_name='automarker_cam_trough_marker_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.0001
        # source event 66, 33.4001s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit_side', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.0001
        # source event 67, 33.4002s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TALK_000LV_A_16, duration=15.1, time_scale=0.75, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.5)

        # Line 40: source 33.5s; allocated facial window 15s.
        t = 0
        # source event 57, 33.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_TAP_RHND_000LV_A_02, duration=5.5, time_scale=0.7, start_time=0, loop=True, trans_time=0.25)
        t += 5.5
        # source event 58, 39s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.3)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.5)

        # Line 50: source 40s; allocated facial window 15s.
        t = 0
        t += 1
        # source event 59, 41s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CHIN_HOLDR_000LV_XA_03, duration=3, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 3
        # source event 60, 44s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 55, 45s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_50', None)
        obj_Char_trent.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.5)

        # Line 55: source 48.5s; allocated facial window 18s.
        t = 0
        # source event 53, 48.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 68, 48.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TWSTU_CLOC_LESS_000LV_A_14, duration=25, time_scale=0.75, start_time=9, loop=False, trans_time=None)
        t += 7.5
        # source event 79, 56s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith')
        # source event 80, 56s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_HOLD_CHIN_RLEASE_000LV_XA_03, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 82, 56s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_55', None)
        obj_Char_trent.facial(group=MAIN, index=55, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.5)

        # Line 60: source 59s; allocated facial window 5.75s.
        t = 0
        t += 2.5
        # source event 81, 61.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.3)
        t += 0.5
        # source event 87, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit_side', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.2
        # source event 88, 62.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.3
        # source event 86, 63.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sidetalk')
        t += 0.5
        # source event 90, 64s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=10, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 91, 64.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-90, axis='Y_AXIS', duration=2, smooth=True)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_60', None)
        obj_Char_smith.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.25)

        # Line 70: source 65s; allocated facial window 3s.
        t = 0
        t += 0.5
        # source event 89, 65.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=3, time_scale=0.92, start_time=0, loop=False, trans_time=0.25)
        t += 0.5
        # source event 94, 66s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 95, 68s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith_far')
        # source event 96, 68s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        main_group.append_time(0.5)

        # Line 80: source 68.5s; allocated facial window 4s.
        t = 0
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_80', None)
        obj_Char_smith.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 90: source 72s; allocated facial window 5s.
        t = 0
        # source event 99, 72s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sidetalk')
        # source event 100, 72s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=0.2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.8
        # source event 101, 72.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 1.5
        # source event 102, 74.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.8, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 100: source 76.5s; allocated facial window 8s.
        t = 0
        # source event 107, 76.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith')
        # source event 108, 76.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 109, 76.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith')
        t += 0.5
        # source event 106, 77s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=8, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 5.0
        # source event 113, 82s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 114, 82s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.2
        # source event 112, 83.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=8, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 0.8
        # source event 115, 84s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sidetalk')
        # source event 116, 84s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_LEAN_ARMB_000LV_A_10, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_100', None)
        obj_Char_smith.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 110: source 85s; allocated facial window 3s.
        t = 0
        t += 1
        # source event 122, 86s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_110', None)
        obj_Char_trent.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 119, 88s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith_far')
        # source event 120, 88s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_pda', parent_name='Char_smith', duration=17, target_hardpoint='Hp_LHand_PDA', parent_hardpoint='HpLeftConnect')
        # source event 123, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        main_group.append_time(1)

        # Line 120: source 89s; allocated facial window 15s.
        t = 0
        t += 1
        # source event 124, 90s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CONV_LHNDUP_TRNS_000LV_XA_02, duration=7, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 2.5
        # source event 125, 92.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CONV_LHND_CASL_000LV_xa_03, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 4.0
        # source event 126, 96.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CONV_LHNDDN_TRNS_000LV_XA_02, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 3.5
        # source event 127, 100s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CONV_LHNDUP_TRNS_000LV_XA_02, duration=7, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 2
        # source event 128, 102s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=0.5, start_time=1, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_120', None)
        obj_Char_smith.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 135, 104s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=4, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(1)

        # Line 130: source 105s; allocated facial window 3s.
        t = 0
        # source event 136, 105s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sidetalk')
        # source event 137, 105s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_270LV_XA_10, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 7, 105.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_cigarette_2', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.9
        # source event 121, 106s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_pda', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_130', None)
        obj_Char_trent.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 2
        # source event 141, 110s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_smith')
        # source event 142, 110s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_smith', anim=Male.Sc_MLBODY_CHRB_TWSTU_CLOC_LESS_000LV_A_14, duration=25, time_scale=0.75, start_time=8, loop=False, trans_time=None)
        t += 1e-05
        # source event 138, 110s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        main_group.append_time(4)

        # Line 140: source 112s; allocated facial window 3s.
        t = 0
        select_dialogue(self, 5, 'Msn5Piratebar', 'm05_piratebar')
        self.groups.pop('motion_140', None)
        obj_Char_smith.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 4
        # source event 145, 119s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        main_group.append_time(4.0)
        restore_dialogue(self)
