"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_chair(Prop):
    COMPOUND_TEMPLATE_NAME = 'm8_osiris_chair'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_tome(Prop):
    COMPOUND_TEMPLATE_NAME = 'tome'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_rifleman(actors.Actor):
    NAME = 'rifleman'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm8_asf_rifleman'
    GAME_ACTOR = 'Gunner2'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm08_osiris'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_chair = Asset_obj_chair(root=self, name='chair', light_group=0, init_point='chair', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_chair, {'template_name': 'm8_osiris_chair', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_prop_tome = Asset_obj_prop_tome(root=self, name='prop_tome', light_group=9, init_point='prop_tome', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_tome, {'template_name': 'tome', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_king = Character(root=self, actor=actors.King, light_group=0, init_point='Char_king', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_king, {'template_name': 'king', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'King', 'category': 'Character'}})
        obj_Char_major = Character(root=self, actor=actors.MajorScrew, light_group=0, init_point='Char_major', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_major, {'template_name': 'major_screw', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Major_Screw', 'category': 'Character'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=0, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_Char_captain = Character(root=self, actor=actors.MaleCaptain, light_group=0, init_point='Char_captain', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_captain, {'template_name': 'm8_asf_captain', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Gunner', 'category': 'Character'}})
        obj_Char_rifleman = Character(root=self, actor=Actor_obj_Char_rifleman, light_group=0, init_point='Char_rifleman', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_rifleman, {'template_name': 'm8_asf_rifleman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Gunner2', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_start_hatcher = LookAtCamera(root=self, name='cam_start_hatcher', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_king_first = LookAtCamera(root=self, name='cam_king_first', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_king_first, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_sits_down = LookAtCamera(root=self, name='cam_trent_sits_down', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_sits_down, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_king_far = LookAtCamera(root=self, name='cam_king_far', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_king_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_king_near = LookAtCamera(root=self, name='cam_king_near', fov=12, farplane=5000, look_duration=120)
        preserve_entity(obj_cam_king_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=12, farplane=5000, look_duration=120)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_major_near = LookAtCamera(root=self, name='cam_major_near', fov=12, farplane=5000, look_duration=120)
        preserve_entity(obj_cam_major_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_artifact = LookAtCamera(root=self, name='cam_trent_artifact', fov=15, farplane=5000, look_duration=120)
        preserve_entity(obj_cam_trent_artifact, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_decline = LookAtCamera(root=self, name='cam_trent_decline', fov=12, farplane=5000, look_duration=200)
        preserve_entity(obj_cam_trent_decline, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_reaction = LookAtCamera(root=self, name='cam_trent_reaction', fov=15, farplane=5000, look_duration=200)
        preserve_entity(obj_cam_trent_reaction, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_sad = LookAtCamera(root=self, name='cam_hatcher_sad', fov=15, farplane=5000, look_duration=200)
        preserve_entity(obj_cam_hatcher_sad, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 13, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 14, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 15, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 17, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_major', anim=Male.Sc_MLBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_02, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 18, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', anim=Male.Sc_MLBODY_STND_LEAN_ARMB_090LV_A_08, duration=0.1, time_scale=1, start_time=2.5, loop=False, trans_time=None)
        # source event 20, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rifleman', anim=Male.Sc_MLBODY_STND_HOLD_RIFLE_MILI_000LV_XA_05, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 23, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_captain', anim=Female.Sc_FMBODY_WALK_HOLD_GUN_RHAND_000LV_XB_01, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 24, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 25, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_WLKG_000LV_XA_01, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 26, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', angle=6, axis='Y_AXIS', duration=6, smooth=False)
        t += 0.01
        # source event 19, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', angle=-140, axis='Y_AXIS', duration=0, smooth=False)
        # source event 21, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rifleman', angle=30, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.19
        # source event 22, 0.2s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_rifleman', target_name='Char_captain', duration=15, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.8
        # source event 41, 2s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_king', target_name='automarker_king_head_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 42, 2s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_king', target_name='automarker_king_eye_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 32, 3s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 33, 3s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 4
        # source event 16, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_hatcher')
        # source event 27, 7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_WALK_STND_TRNS_000LV_XA_01, duration=15, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        # source event 28, 7s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', angle=-15, axis='Y_AXIS', duration=2, smooth=False)
        main_group.append_time(8.5)

        # Line 10: source 8.5s; allocated facial window 25s.
        t = 0
        t += 0.5
        # source event 34, 9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_king', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_king', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 29, 9.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_SALUT_000LV_XA_03, duration=10, time_scale=1, start_time=0.5, loop=False, trans_time=1)
        t += 2.0
        # source event 36, 11.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_major', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 11.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_major', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_10', None)
        obj_Char_hatcher.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19.5)

        # Line 20: source 14s; allocated facial window 6s.
        t = 0
        # source event 38, 14s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_first')
        # source event 39, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_king_first', target_name='automarker_cam_king_first_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 40, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_king_first_focus', target_name='automarker_cam_king_first_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 43, 14s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_major', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_A_11, duration=50, time_scale=0.2, start_time=1, loop=True, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_20', None)
        obj_Char_king.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 30: source 16s; allocated facial window 12s.
        t = 0
        # source event 48, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 49, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 50, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_captain', target_name='automarker_point_captain_aim', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 51, 16.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_captain', anim=Female.Sc_FMBODY_CHRB_LSTN_000LV_A_08, duration=200, time_scale=0.4, start_time=0, loop=True, trans_time=None)
        t += 0.1
        # source event 52, 16.2s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_captain', target_name='automarker_head_trent', duration=15, transition_duration=3, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.3
        # source event 54, 17.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_stand_to_sit', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.01
        # source event 55, 17.51s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=50, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.99
        # source event 56, 18.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SITCR_TRNS_090DN_XA_07, duration=15, time_scale=1, start_time=1, loop=False, trans_time=None)
        t += 2.0
        # source event 57, 20.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=20, axis='Y_AXIS', duration=1, smooth=False)
        t += 1.5
        # source event 53, 22s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sits_down')
        # source event 60, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', target_name='automarker_point_king_talk_front', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 61, 22.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=0.1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 62, 22.2s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', angle=-20, axis='Y_AXIS', duration=0, smooth=False)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_30', None)
        obj_Char_king.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.5)

        # Line 40: source 22.5s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 50: source 25s; allocated facial window 23s.
        t = 0
        # source event 63, 25s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_far')
        # source event 64, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_king_far', target_name='automarker_cam_king_far_pos2', duration=26, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 65, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        t += 10
        # source event 66, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_50', None)
        obj_Char_king.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9)

        # Line 60: source 39s; allocated facial window 17s.
        t = 0
        t += 1
        # source event 67, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_king', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=5, time_scale=0.4, start_time=0, loop=False, trans_time=2)
        t += 10
        # source event 76, 50s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_60', None)
        obj_Char_king.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.5)

        # Line 70: source 50.5s; allocated facial window 6s.
        t = 0
        # source event 78, 50.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sits_down')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 80: source 54.8s; allocated facial window 12s.
        t = 0
        # source event 81, 54.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        t += 1.2
        # source event 84, 56s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 85, 56.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_80', None)
        obj_Char_king.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.3)

        # Line 90: source 56.5s; allocated facial window 10s.
        t = 0
        # source event 86, 56.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        t += 1.5
        # source event 95, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_major', anim=Male.Sc_MLBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_02, duration=1, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 96, 58s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_major', target_name='automarker_major_head_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 97, 58s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_major', target_name='automarker_major_eye_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 100: source 64s; allocated facial window 12s.
        t = 0
        # source event 90, 64s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_far')
        # source event 93, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_major_front_far', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 94, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_major_front_near', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.7
        # source event 98, 65.7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        # source event 101, 65.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_head_ik', target_name='automarker_head_king_front_far', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 102, 65.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_eye_ik', target_name='automarker_head_king_front_near', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_100', None)
        obj_Char_king.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10)

        # Line 110: source 66s; allocated facial window 12s.
        t = 0
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_110', None)
        obj_Char_major.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10)

        # Line 120: source 68s; allocated facial window 6s.
        t = 0
        # source event 103, 68s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        # source event 106, 68s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 107, 68s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_120', None)
        obj_Char_trent.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 130: source 73s; allocated facial window 12s.
        t = 0
        # source event 108, 73s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_130', None)
        obj_Char_king.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11)

        # Line 140: source 74s; allocated facial window 14s.
        t = 0
        # source event 111, 74s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_artifact')
        t += 1
        # source event 116, 75s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_major_right', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 117, 75s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_major_right', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 118, 78s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_leaders_middle', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 119, 78s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_leaders_middle', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_140', None)
        obj_Char_trent.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 145: source 84s; allocated facial window 6s.
        t = 0
        t += 1
        # source event 120, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_major_right', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 121, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_major_right', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 126, 85.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_artifact_focus', target_name='automarker_cam_trent_artifact_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 127, 85.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_GESTR_RGHT_000LV_XA_03, duration=4, time_scale=0.15, start_time=0, loop=False, trans_time=0.5)
        # source event 128, 85.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_tome', parent_name='Char_trent', duration=20, target_hardpoint='rhand_connect_tome', parent_hardpoint='hprightconnect')
        # source event 130, 85.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_HOLDD_RGHT_000LV_00, duration=1, time_scale=5, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 122, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_leaders_middle_bottom', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 123, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_leaders_middle_bottom', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_145', None)
        obj_Char_trent.facial(group=MAIN, index=145, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(1)

        # Line 150: source 91s; allocated facial window 12s.
        t = 0
        # source event 131, 91s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        t += 2.3
        # source event 134, 93.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_150', None)
        obj_Char_king.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.6)

        # Line 160: source 93.4s; allocated facial window 12s.
        t = 0
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_160', None)
        obj_Char_major.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.6)

        # Line 170: source 94.8s; allocated facial window 12s.
        t = 0
        # source event 137, 94.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        t += 0.5
        # source event 140, 95.3s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_major_front_far', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 141, 95.3s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_major_front_near', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_170', None)
        obj_Char_king.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.1)

        # Line 180: source 98.7s; allocated facial window 16s.
        t = 0
        # source event 142, 98.7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        t += 1.0
        # source event 146, 99.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_head_ik', target_name='automarker_head_hatcher', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 147, 99.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_eye_ik', target_name='automarker_head_hatcher', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4.0
        # source event 148, 103.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_head_ik', target_name='automarker_head_king_front_far', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 149, 103.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_eye_ik', target_name='automarker_head_king_front_near', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_180', None)
        obj_Char_major.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.7)

        # Line 190: source 108s; allocated facial window 12s.
        t = 0
        # source event 150, 108s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_190', None)
        obj_Char_king.facial(group=MAIN, index=190, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.8)

        # Line 200: source 110.2s; allocated facial window 14.7s.
        t = 0
        # source event 153, 110.2s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        t += 4.8
        # source event 157, 115s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_head_ik', target_name='automarker_head_hatcher', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 158, 115s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_eye_ik', target_name='automarker_head_hatcher', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_200', None)
        obj_Char_major.facial(group=MAIN, index=200, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.8)

        # Line 210: source 118.1s; allocated facial window 15s.
        t = 0
        # source event 159, 118.1s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_far')
        t += 1.9
        # source event 129, 120s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_tome', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1.1
        # source event 163, 121.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_trent_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 164, 121.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_trent', duration=1.3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.9
        # source event 165, 122s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_king', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 166, 122s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_king', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 169, 122s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Male.GENERIC_ANIM, duration=0.1, start_time=0, time_scale=1, trans_time=0)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_210', None)
        obj_Char_king.facial(group=MAIN, index=210, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.1)

        # Line 220: source 123s; allocated facial window 32.6s.
        t = 0
        # source event 167, 123s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_hatcher')
        # source event 174, 123s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDS_EMPH_000LV_XB_03, duration=5, time_scale=0.8, start_time=0, loop=True, trans_time=1)
        t += 4
        # source event 175, 127s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_EMPH_HNDSDN_TRNS_000LV_XA_01, duration=100, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 176, 130s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=100, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_220', None)
        obj_Char_hatcher.facial(group=MAIN, index=220, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-21.8)

        # Line 230: source 133.8s; allocated facial window 15s.
        t = 0
        # source event 177, 133.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        t += 1.2
        # source event 182, 135s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_head_ik', target_name='automarker_head_king_front_far', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 183, 135s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_eye_ik', target_name='automarker_head_king_front_near', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 188, 135s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_major_front_far', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 189, 135s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_major_front_near', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_230', None)
        obj_Char_major.facial(group=MAIN, index=230, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.0)

        # Line 240: source 138.8s; allocated facial window 15.2s.
        t = 0
        # source event 184, 138.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_far')
        t += 1.2
        # source event 181, 140s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_major', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=4.444, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        t += 0.5
        # source event 190, 140.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_trent_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 191, 140.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 7.5
        # source event 192, 148s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_240', None)
        obj_Char_king.facial(group=MAIN, index=240, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.7)

        # Line 250: source 148.3s; allocated facial window 11.2s.
        t = 0
        # source event 193, 148.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_decline')
        t += 3.0
        # source event 194, 151.3s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_decline', target_name='automarker_cam_trent_decline_pos2', duration=13, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 195, 151.3s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_decline_focus', target_name='automarker_cam_trent_decline_marker_pos2', duration=13, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_250', None)
        obj_Char_trent.facial(group=MAIN, index=250, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.2)

        # Line 260: source 158.3s; allocated facial window 8s.
        t = 0
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_260', None)
        obj_Char_trent.facial(group=MAIN, index=260, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 270: source 164.6s; allocated facial window 17s.
        t = 0
        # source event 203, 164.6s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_270', None)
        obj_Char_major.facial(group=MAIN, index=270, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.3)

        # Line 280: source 171.3s; allocated facial window 14.5s.
        t = 0
        # source event 207, 171.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        # source event 211, 171.3s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_major_front_far', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 212, 171.3s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_major_front_near', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_280', None)
        obj_Char_king.facial(group=MAIN, index=280, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.3)

        # Line 290: source 175.5s; allocated facial window 12s.
        t = 0
        # source event 213, 175.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_290', None)
        obj_Char_major.facial(group=MAIN, index=290, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.0)

        # Line 300: source 177.5s; allocated facial window 12s.
        t = 0
        # source event 216, 177.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        t += 2.5
        # source event 220, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit_forward', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 221, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rifleman', target_name='automarker_point_rifleman_near_trent', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.005
        # source event 222, 180.005s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rifleman', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_300', None)
        obj_Char_king.facial(group=MAIN, index=300, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.2)

        # Line 310: source 180.3s; allocated facial window 6s.
        t = 0
        # source event 219, 180.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_reaction')
        # source event 223, 180.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s051x_Trent_XC_CHRF_RLLV_29, duration=6, time_scale=1, start_time=24.8, loop=False, trans_time=None)
        # source event 224, 180.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rifleman', anim=Male.Sc_SPCBODY_s051x_ku_guard01_XB_STND_000LV_05, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_310', None)
        obj_Char_trent.facial(group=MAIN, index=310, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.3)

        # Line 320: source 184s; allocated facial window 13s.
        t = 0
        # source event 227, 184s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_major_near')
        # source event 231, 184s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_head_ik', target_name='automarker_head_trent_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 232, 184s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_major_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4
        # source event 238, 188s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=100, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_320', None)
        obj_Char_major.facial(group=MAIN, index=320, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.5)

        # Line 330: source 188.5s; allocated facial window 15.7s.
        t = 0
        # source event 233, 188.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_sad')
        # source event 239, 188.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_upper_forward', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 240, 188.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_330', None)
        obj_Char_hatcher.facial(group=MAIN, index=330, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.7)

        # Line 340: source 197.5s; allocated facial window 15s.
        t = 0
        # source event 241, 197.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_near')
        # source event 242, 197.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_trent_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 243, 197.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_trent', duration=1.3, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_340', None)
        obj_Char_king.facial(group=MAIN, index=340, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.5)

        # Line 345: source 206s; allocated facial window 12s.
        t = 0
        t += 3
        # source event 249, 209s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rifleman', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 250, 209s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 251, 209.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_345', None)
        obj_Char_king.facial(group=MAIN, index=345, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.5)

        # Line 350: source 209.5s; allocated facial window 6s.
        t = 0
        # source event 252, 209.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_350', None)
        obj_Char_trent.facial(group=MAIN, index=350, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.0)

        # Line 360: source 211.5s; allocated facial window 12s.
        t = 0
        # source event 255, 211.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_king_far')
        # source event 256, 211.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_head_ik', target_name='automarker_head_hatcher_right', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 257, 211.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_king_eye_ik', target_name='automarker_head_hatcher_right_far', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_360', None)
        obj_Char_king.facial(group=MAIN, index=360, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.6)

        # Line 370: source 216.9s; allocated facial window 14s.
        t = 0
        t += 2.1
        # source event 263, 219s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_king', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 264, 219s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_king', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_370', None)
        obj_Char_king.facial(group=MAIN, index=370, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.4)

        # Line 380: source 223.5s; allocated facial window 5s.
        t = 0
        # source event 265, 223.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_hatcher')
        # source event 268, 223.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_SALUT_000LV_XA_03, duration=10, time_scale=1, start_time=1.5, loop=False, trans_time=None)
        select_dialogue(self, 8, 'Msn8Osiris', 'm08_osiris')
        self.groups.pop('motion_380', None)
        obj_Char_hatcher.facial(group=MAIN, index=380, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 10921.5
        # source event 77, 11150s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(-2.5)
        restore_dialogue(self)
