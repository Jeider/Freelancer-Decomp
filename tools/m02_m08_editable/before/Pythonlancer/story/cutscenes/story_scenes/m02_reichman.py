"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_subtitles_pack3(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_pack3'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_subtitles_m02_done01(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done01'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done02(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done02'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done03(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done03'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done04(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done04'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done05(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done05'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done06(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done06'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done07(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done07'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done08(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done08'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done09(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done09'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done10(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done10'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done11(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done11'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done12(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done12'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done13(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done13'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done14(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done14'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done15(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done15'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_done16(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_done16'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_main_ship(Ship):
    COMPOUND_TEMPLATE_NAME = 'rh_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_trooper1(actors.Actor):
    NAME = 'trooper1'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'ms2_trooper1'
    GAME_ACTOR = 'Trooper1'


class Actor_obj_Char_trooper2(actors.Actor):
    NAME = 'trooper2'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'ms2_trooper2'
    GAME_ACTOR = 'Trooper2'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm02_reichman'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_music_main = Sound(root=self, name='music_main', sound='music_discordant_psychosis', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_main, {'template_name': 'music_discordant_psychosis', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_second = Sound(root=self, name='music_second', sound='music_anticipation_more_forboding', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_second, {'template_name': 'music_anticipation_more_forboding', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_main_ship = Asset_obj_main_ship(root=self, name='main_ship', light_group=3, init_point='main_ship', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_main_ship, {'template_name': 'rh_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_rh_elite_loadout04'}})
        obj_Char_reichman = Character(root=self, actor=actors.Reichman, light_group=3, init_point='Char_reichman', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_reichman, {'template_name': 'reichman', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Reichman', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=3, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_wilham = Character(root=self, actor=actors.Wilham, light_group=3, init_point='Char_wilham', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_wilham, {'template_name': 'wilham', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Wilham', 'category': 'Character'}})
        obj_Char_trooper1 = Character(root=self, actor=Actor_obj_Char_trooper1, light_group=3, init_point='Char_trooper1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trooper1, {'template_name': 'ms2_trooper1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Trooper1', 'category': 'Character'}})
        obj_Char_trooper2 = Character(root=self, actor=Actor_obj_Char_trooper2, light_group=3, init_point='Char_trooper2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trooper2, {'template_name': 'ms2_trooper2', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Trooper2', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=40, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 40, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_reichman_near = LookAtCamera(root=self, name='cam_reichman_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_reichman_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_reichman_top = LookAtCamera(root=self, name='cam_reichman_top', fov=17, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_reichman_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 17, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_reichman_far = LookAtCamera(root=self, name='cam_reichman_far', fov=23, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_reichman_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 23, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_reichman_reward = LookAtCamera(root=self, name='cam_reichman_reward', fov=17, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_reichman_reward, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 17, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_top = LookAtCamera(root=self, name='cam_trent_top', fov=18, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_far = LookAtCamera(root=self, name='cam_trent_far', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_away = LookAtCamera(root=self, name='cam_trent_away', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_away, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_reichman_looktrent = LookAtCamera(root=self, name='cam_reichman_looktrent', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_reichman_looktrent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = LookAtCamera(root=self, name='cam_final', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=47, start_time=0, loop=True)
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 6, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 19, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 20, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 22, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 23, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_reichman', target_name='automarker_reichman_eye_ik', duration=15, transition_duration=0.1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 25, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trooper2', anim=Male.Sc_MLBODY_STND_000LV_E_20, duration=1555, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 26, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trooper1', anim=Male.Sc_MLBODY_STND_000LV_E_20, duration=1555, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 27, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.6, time_scale=1, start_time=0.3, loop=True, trans_time=None)
        # source event 29, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.8, time_scale=1, start_time=0.1, loop=True, trans_time=None)
        # source event 33, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 24, 3s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trooper2', target_name='Char_wilham', duration=25, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.6
        # source event 28, 3.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.2
        # source event 30, 3.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.2
        # source event 34, 4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=2, time_scale=0.2, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 31, 4.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_reichman_back_left', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 35, 5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 38, 5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 36, 6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_TURN_180LV_XA_04, duration=5, time_scale=0.75, start_time=0, loop=False, trans_time=0.5)
        t += 1
        # source event 40, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_reichman_top')
        # source event 41, 7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_reichman_top', target_name='automarker_cam_reichman_top_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 42, 7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_reichman_top_focus', target_name='automarker_cam_reichman_top_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 32, 7.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_reichman_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(10)

        # Line 10: source 10s; allocated facial window 4s.
        t = 0
        # source event 39, 10s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_reichman', target_name='automarker_reichman_head_ik', duration=5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 37, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=5, time_scale=0.6, start_time=0, loop=True, trans_time=2)
        t += 2
        # source event 47, 13s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_far')
        # source event 53, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=4, time_scale=1, start_time=0, loop=False, trans_time=2)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_10', None)
        obj_Char_reichman.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.8)

        # Line 20: source 13.2s; allocated facial window 2.1s.
        t = 0
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.2
        # source event 52, 15.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(0.7)

        # Line 30: source 16s; allocated facial window 4s.
        t = 0
        # source event 54, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_reichman_near')
        # source event 59, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_BOW_ASNSTYL_RSPCTFLY_000LV_xa_03, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 66, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=7, time_scale=1, start_time=0, loop=False, trans_time=2)
        t += 1
        # source event 60, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=2)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_30', None)
        obj_Char_reichman.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 40: source 20s; allocated facial window 8s.
        t = 0
        # source event 61, 20s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_top')
        # source event 69, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 70, 20s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 50: source 24s; allocated facial window 8.4s.
        t = 0
        # source event 67, 24s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_reichman', target_name='automarker_reichman_head_ik', duration=30, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 68, 24s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_reichman', target_name='automarker_reichman_eye_ik', duration=30, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 74, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_reichman_far_focus', target_name='automarker_cam_reichman_far_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 75, 24s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_reichman_far')
        t += 2
        # source event 73, 26s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_reichman_far', target_name='automarker_cam_reichman_far_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 71, 28s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 83, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        # source event 89, 28s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_reichman', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 90, 28s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_reichman', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 72, 29s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_wilham_trent_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 84, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_CONV_RHND_CASL_000LV_xa_01, duration=2, time_scale=1, start_time=0, loop=True, trans_time=1.5)
        # source event 86, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLHAND_HNEUT_GESTR_CASL_000LV_00, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        t += 1
        # source event 85, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        # source event 87, 30s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 88, 30s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 91, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 92, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_reichman_wilham_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 95, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_near_focus', target_name='automarker_cam_trent_near_marker_pos2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 96, 32s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_50', None)
        obj_Char_reichman.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.1
        # source event 93, 32.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_reichman', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 94, 32.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_reichman', duration=3.5, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(0.8)

        # Line 60: source 33.2s; allocated facial window 4.5s.
        t = 0
        t += 0.8
        # source event 102, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 103, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 70: source 36s; allocated facial window 15.25s.
        t = 0
        # source event 101, 36s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 104, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_reichman_reward', target_name='automarker_cam_reichman_reward_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 105, 36s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_reichman_reward_focus', target_name='automarker_cam_reichman_reward_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 106, 36s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_reichman_reward')
        # source event 115, 36s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 116, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_GESTL_STOP_000LV_XA_03, duration=4.5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 4.5
        # source event 117, 41.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 1, 42s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=5, attenuation=-100)
        t += 2
        # source event 118, 44s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_ATEASE_HOLD_000LV_XA_01, duration=5, time_scale=0.6, start_time=0, loop=True, trans_time=1)
        t += 3
        # source event 2, 47s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_second', duration=60, start_time=0, loop=True)
        # source event 3, 47s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_second', duration=5, attenuation=0)
        # source event 119, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_away', target_name='automarker_cam_trent_away_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 120, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_away_focus', target_name='automarker_cam_trent_away_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 123, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trooper1', target_name='offscreen', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 124, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trooper2', target_name='offscreen', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 125, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_talk', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 126, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', target_name='automarker_point_wilham_talk', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 127, 47s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', target_name='automarker_point_reichman_looktrent', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 128, 47s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_away')
        # source event 131, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_180LV_XA_02, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 132, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_TURN_090LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 129, 47.1s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='Char_trent', duration=5, transition_duration=5, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 130, 47.1s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='Char_trent', duration=5, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 3.9
        # source event 134, 51s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=5, time_scale=0.5, start_time=0.35, loop=False, trans_time=None)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_70', None)
        obj_Char_reichman.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.75
        # source event 133, 52s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=25, time_scale=0.6, start_time=0, loop=True, trans_time=2)
        # source event 148, 52s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_reichman_trentaway_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 149, 52s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.0
        # source event 142, 54s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent_away', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 143, 54s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_head_trent_away', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(3.75)

        # Line 80: source 55s; allocated facial window 4s.
        t = 0
        # source event 140, 55s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_head_ik', duration=35, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 141, 55s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_wilham', target_name='automarker_wilham_eye_ik', duration=35, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 144, 55s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_reichman_trentaway', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 145, 55s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_wilham_rotate_front_left', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 121, 57s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_away', target_name='automarker_cam_trent_away_pos3', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 122, 57s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_away_focus', target_name='automarker_cam_trent_away_marker_pos3', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 139, 57s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='offscreen', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 146, 57s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_reichman', target_name='automarker_reichman_head_ik', duration=35, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 147, 57s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_reichman', target_name='automarker_reichman_eye_ik', duration=35, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 150, 57s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 151, 57s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front_right', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_80', None)
        obj_Char_reichman.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 90: source 58s; allocated facial window 5.65s.
        t = 0
        t += 2
        # source event 154, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_trent_away', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 155, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_wilham_rotate_front', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 152, 61s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_reichman_trentaway_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 153, 61s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_90', None)
        obj_Char_wilham.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.35)

        # Line 100: source 64s; allocated facial window 4s.
        t = 0
        # source event 160, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_wilham', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 161, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front_right', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 162, 64s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_head_reichman_trentaway', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 163, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_wilham_rotate_front_left', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_100', None)
        obj_Char_reichman.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.4)

        # Line 110: source 65.6s; allocated facial window 5s.
        t = 0
        t += 1.9
        # source event 174, 67.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_reichman_looktrent')
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_110', None)
        obj_Char_wilham.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.6)

        # Line 120: source 68s; allocated facial window 6.5s.
        t = 0
        t += 2
        # source event 172, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_reichman_trentaway_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 173, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.5
        # source event 191, 72.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_120', None)
        obj_Char_reichman.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 130: source 73.5s; allocated facial window 5s.
        t = 0
        # source event 184, 73.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        # source event 190, 73.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_SALUT_000LV_XA_03, duration=15, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 180, 75s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_wilham', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 181, 75s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front_right', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 192, 75.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLBODY_STND_ATEASE_HOLD_000LV_XA_01, duration=15, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        t += 0.5
        # source event 189, 76s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        # source event 201, 76s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_final', target_name='automarker_cam_final_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 202, 76s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_final_focus', target_name='automarker_cam_final_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_130', None)
        obj_Char_wilham.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 140: source 76.5s; allocated facial window 4s.
        t = 0
        t += 0.5
        # source event 182, 77s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_eye_ik', target_name='automarker_head_reichman_trentaway_front', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 183, 77s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_reichman_head_ik', target_name='automarker_head_reichman_trentaway_front', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.0
        # source event 198, 79s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_eye_ik', target_name='automarker_outpoint', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 199, 79s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_wilham_head_ik', target_name='automarker_outpoint', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 200, 80s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_STND_WALK_TRNS_090LV_XA_02, duration=15, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 2, 'Msn2Done', 'm02_done')
        self.groups.pop('motion_140', None)
        obj_Char_reichman.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 1.5
        # source event 197, 82s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_reichman', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=2, time_scale=0.2, start_time=0, loop=False, trans_time=None)
        t += 1.0
        # source event 4, 83s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_second', duration=3, attenuation=-8)
        main_group.append_time(5.5)
        restore_dialogue(self)
