"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_subtitles_pack2(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_pack2'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer33(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer33'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer34(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer34'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer35(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer35'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer36(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer36'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer37(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer37'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer38(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer38'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer39(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer39'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer40(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer40'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer41(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer41'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer42(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer42'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_offer43(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_offer43'
    SRT_GRP = -1
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm02_bship_bar_accept'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'Trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'Player'}})
        obj_Char_wilham = Character(root=self, actor=actors.Wilham, light_group=0, init_point='Char_wilham', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_wilham, {'template_name': 'wilham', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'wilham'}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wilham_near = LookAtCamera(root=self, name='cam_wilham_near', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_wilham_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_standing = LookAtCamera(root=self, name='cam_trent_standing', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_standing, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wilham_stand = LookAtCamera(root=self, name='cam_wilham_stand', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_wilham_stand, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = LookAtCamera(root=self, name='cam_final', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 6, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        # source event 11, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        main_group.append_time(0.5)

        # Line 200: source 0.5s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 2, 'Msn2Offer', 'm02_offer')
        self.groups.pop('motion_200', None)
        obj_Char_trent.facial(group=MAIN, index=200, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.0)

        # Line 210: source 3.5s; allocated facial window 7s.
        t = 0
        # source event 13, 3.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wilham_near')
        # source event 19, 3.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.0
        # source event 20, 5.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 3.0
        # source event 21, 8.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_CHRB_STNDCR_TRNS_090LV_XA_05, duration=2.5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 22, 10s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=22, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 2, 'Msn2Offer', 'm02_offer')
        self.groups.pop('motion_210', None)
        obj_Char_wilham.facial(group=MAIN, index=210, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.5
        # source event 24, 11s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_standing')
        # source event 27, 11s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_standing', target_name='automarker_cam_trent_standing_pos2', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 28, 11s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_standing_focus', target_name='automarker_cam_trent_standing_point2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 31, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_STNDCL_TRNS_270LV_XA_06, duration=5, time_scale=1, start_time=1, loop=False, trans_time=None)
        main_group.append_time(1.0)

        # Line 220: source 11.5s; allocated facial window 6s.
        t = 0
        t += 0.5
        # source event 23, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_stand_progress', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 33, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', target_name='automarker_point_wilham_stand', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 34, 13s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_head_ik', duration=30, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 35, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent_stand_lower', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Offer', 'm02_offer')
        self.groups.pop('motion_220', None)
        obj_Char_trent.facial(group=MAIN, index=220, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 230: source 14s; allocated facial window 13s.
        t = 0
        # source event 36, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent_stand', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 14s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wilham_stand')
        # source event 42, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_wilham_stand', target_name='automarker_cam_wilham_stand_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 47, 14s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_GESTL_STOP_000LV_XA_03, duration=5, time_scale=1, start_time=0.5, loop=False, trans_time=None)
        t += 3
        # source event 48, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        t += 1
        # source event 49, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_CONV_RHND_CASL_000LV_xa_01, duration=2, time_scale=1, start_time=0, loop=True, trans_time=1.5)
        # source event 52, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHAND_HNEUT_GESTR_CASL_000LV_00, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        t += 2
        # source event 50, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        t += 2.5
        # source event 51, 22.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_GESTR_THMBSUP_000LV_XA_02, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 53, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_CASL_000LV_00, duration=4, time_scale=1.5, start_time=3, loop=False, trans_time=0.5)
        t += 1
        # source event 54, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_stand', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 55, 24.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_SMALL_000LV_xa_05, duration=0.5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 56, 25s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=30, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 57, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_wilham_stand', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 58, 26s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        # source event 69, 26s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_NOD_YES_EMPH_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 73, 26s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_IDLE_SMALL_000LV_xa_05, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 2, 'Msn2Offer', 'm02_offer')
        # Duplicate source sound event 43, same timestamp.
        SoundEvent(root=self, group=MAIN, sound_name=self.lookup_single_sound(230).get_nickname())
        self.groups.pop('motion_230', None)
        obj_Char_wilham.facial(group=MAIN, index=230, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 240: source 26.5s; allocated facial window 6s.
        t = 0
        t += 0.5
        # source event 63, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_final', target_name='automarker_cam_final_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 64, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_final_focus', target_name='automarker_cam_final_point2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 70, 27s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SHRG_SHLDRS_SMALL_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 2, 'Msn2Offer', 'm02_offer')
        self.groups.pop('motion_240', None)
        obj_Char_trent.facial(group=MAIN, index=240, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 250: source 30s; allocated facial window 6s.
        t = 0
        # source event 74, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_GESTL_STOP_000LV_XA_03, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 65, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_final', target_name='automarker_cam_final_pos3', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 66, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_final_focus', target_name='automarker_cam_final_point3', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 75, 34s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 77, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_wilham_outdoor', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 78, 34s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_wilham', duration=5, transition_duration=1, target_type='HARDPOINT', target_part='hp_neck', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 76, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=50, time_scale=1, start_time=0, loop=True, trans_time=0.25)
        # source event 79, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=10, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 2, 'Msn2Offer', 'm02_offer')
        self.groups.pop('motion_250', None)
        obj_Char_wilham.facial(group=MAIN, index=250, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 2
        # source event 80, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=10, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(4.5)
        restore_dialogue(self)
