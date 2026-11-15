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


class Asset_obj_subtitles_pack3(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_pack3'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner01(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner01'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner02(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner02'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner03(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner03'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner04(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner04'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner05(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner05'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner06(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner06'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner07(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner07'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner08(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner08'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner09(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner09'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner10(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner10'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner11(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner11'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner12(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner12'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner13(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner13'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner14(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner14'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner15(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner15'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner16(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner16'
    SRT_GRP = -1
    USR_FLG = 0


class Asset_obj_subtitles_m02_miner17(Prop):
    COMPOUND_TEMPLATE_NAME = 'subtitles_m02_miner17'
    SRT_GRP = -1
    USR_FLG = 0


class Actor_obj_Char_bartender_fixture(actors.Actor):
    NAME = 'bartender_fixture'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'botzler'
    GAME_ACTOR = 'bartender'


class Asset_obj_prop_notebook(Prop):
    COMPOUND_TEMPLATE_NAME = 'notebook'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm02_jacobo_offer'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_sfx_ui_react_accept01 = Sound(root=self, name='sfx_ui_react_accept01', sound='sfx_ui_react_accept01', attenuation=-30, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_ui_react_accept01, {'template_name': 'sfx_ui_react_accept01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -30, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sfx_ui_react_accept02 = Sound(root=self, name='sfx_ui_react_accept02', sound='sfx_ui_react_accept02', attenuation=-30, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_ui_react_accept02, {'template_name': 'sfx_ui_react_accept02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -30, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sfx_ui_react_data01 = Sound(root=self, name='sfx_ui_react_data01', sound='sfx_ui_react_data01', attenuation=-20, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_ui_react_data01, {'template_name': 'sfx_ui_react_data01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sfx_ui_react_denied01 = Sound(root=self, name='sfx_ui_react_denied01', sound='sfx_ui_react_denied01', attenuation=-30, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_ui_react_denied01, {'template_name': 'sfx_ui_react_denied01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -30, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sfx_keyboard_flurry01 = Sound(root=self, name='sfx_keyboard_flurry01', sound='sfx_keyboard_flurry01', attenuation=-30, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_keyboard_flurry01, {'template_name': 'sfx_keyboard_flurry01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -30, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sfx_keyboard_flurry02 = Sound(root=self, name='sfx_keyboard_flurry02', sound='sfx_keyboard_flurry02', attenuation=-22, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_keyboard_flurry02, {'template_name': 'sfx_keyboard_flurry02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -22, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sfx_keyboard_flurry03 = Sound(root=self, name='sfx_keyboard_flurry03', sound='sfx_keyboard_flurry03', attenuation=-15, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_sfx_keyboard_flurry03, {'template_name': 'sfx_keyboard_flurry03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'Trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'Player'}})
        obj_Char_jacobo = Character(root=self, actor=actors.Jacobo, light_group=0, init_point='Char_jacobo', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jacobo, {'template_name': 'jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'jacobo'}})
        obj_Char_bartender = Character(root=self, actor=actors.BartenderFixture, light_group=0, init_point='Char_bartender', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_bartender, {'template_name': 'botzler', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character'}})
        obj_Char_bartender_fixture = Character(root=self, actor=Actor_obj_Char_bartender_fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_bartender_fixture, {'template_name': 'botzler', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'bartender'}})
        obj_prop_notebook = Asset_obj_prop_notebook(root=self, name='prop_notebook', light_group=0, init_point='prop_notebook', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_notebook, {'template_name': 'notebook', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_cam_begin = LookAtCamera(root=self, name='cam_begin', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_begin, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jacobo_eyes = LookAtCamera(root=self, name='cam_jacobo_eyes', fov=12, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_jacobo_eyes, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_bartender_pointer = LookAtCamera(root=self, name='cam_bartender_pointer', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_bartender_pointer, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jacobo_fingerprint = LookAtCamera(root=self, name='cam_jacobo_fingerprint', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_jacobo_fingerprint, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_arrival = LookAtCamera(root=self, name='cam_trent_arrival', fov=35, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_arrival, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 35, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_stand = LookAtCamera(root=self, name='cam_trent_stand', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_stand, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_stand_far = LookAtCamera(root=self, name='cam_trent_stand_far', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_stand_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_walkout1 = LookAtCamera(root=self, name='cam_walkout1', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_walkout1, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_walkout2 = LookAtCamera(root=self, name='cam_walkout2', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_walkout2, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 11, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 12, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_begin')
        # source event 13, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_begin', target_name='automarker_cam_begin_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 15, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='prop_notebook', anim='Sc_open', duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        # source event 16, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jacobo', target_name='automarker_jacobo_head_ik', duration=851, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 17, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_jacobo', target_name='automarker_jacobo_eye_ik', duration=851, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 18, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=85, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 19, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_bartender', duration=0.0001, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 20, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=1.5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 21, 1.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=1.7, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.7
        # source event 22, 3.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_SPCBODY_s020x_VanPelt_XC_CHRF_TYPE_000DN_06, duration=10, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        t += 0.3
        # source event 24, 3.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_HNEUT_GESTL_TYPING_000LV_XB, duration=7.474, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        # source event 25, 3.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_HNEUT_GESTR_TYPING_000LV_XB, duration=7.459, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        t += 0.5
        # source event 23, 4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_keyboard_flurry02', duration=9, start_time=0, loop=True)
        t += 1
        # source event 14, 5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_begin_focus', target_name='automarker_cam_begin_point2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 5
        # source event 26, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_eyes')
        t += 2
        # source event 27, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_trent_far', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 28, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_far', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 31, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHEAD_MAD_COLD_000LV_XA_, duration=10, time_scale=0.8, start_time=0, loop=False, trans_time=0.25)
        t += 3
        # source event 32, 15s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_bartender_pointer')
        # source event 33, 15s
        CameraAnimEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_bartender_pointer', duration=5, fov=10, smooth=True)
        # source event 34, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.GENERIC_ANIM, duration=10, start_time=0, time_scale=0.6, trans_time=0.25)
        # source event 35, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_CONV_HNDS_CASL_000LV_xa_04, duration=2, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        # source event 41, 15s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender', anim=Male.Sc_MLBODY_STND_000DN_A_29, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 29, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 30, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_notebook_screen', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 36, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 42, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender', anim=Male.Sc_MLBODY_STND_POINT_RHND_270LV_A_03, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 40, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 43, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_CASL_000LV_00, duration=4, time_scale=2, start_time=0, loop=False, trans_time=0.25)
        t += 1
        # source event 37, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_045LV_XA_04, duration=4, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 39, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_HAPPY_SMILE_SNEER_TRENT_000LV_XA_, duration=10, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 1.6
        # source event 38, 21.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=1.4, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 1.4
        # source event 44, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_arriving', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 45, 23s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_arrival')
        # source event 50, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_arrival', target_name='automarker_cam_trent_arrival_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 51, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_trent_arrival_focus', target_name='automarker_cam_trent_arrival_point2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 54, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_SPCBODY_s020x_VanPelt_XC_CHRF_TYPE_000DN_06, duration=14, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 55, 23s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_keyboard_flurry01', duration=14, start_time=0, loop=True)
        # source event 56, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_HNEUT_GESTL_TYPING_000LV_XB, duration=14, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        # source event 57, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_HNEUT_GESTR_TYPING_000LV_XB, duration=14, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        t += 2
        # source event 52, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XC_03, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        main_group.append_time(27)

        # Line 10: source 27s; allocated facial window 4s.
        t = 0
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 20: source 28s; allocated facial window 3s.
        t = 0
        t += 0.5
        # source event 53, 28.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_000DN_A_29, duration=20, time_scale=0.6, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_20', None)
        obj_Char_jacobo.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(1)

        # Line 30: source 32s; allocated facial window 4s.
        t = 0
        # source event 62, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 63, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 64, 32s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_stand')
        t += 3
        # source event 69, 35s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_fingerprint')
        # source event 74, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHEAD_MAD_COLD_000LV_XA_, duration=10, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.5
        # source event 80, 36.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_jacobo_front_left', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(1)

        # Line 40: source 37s; allocated facial window 3s.
        t = 0
        # source event 75, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_IDLE_SMALL_000LV_XA_05, duration=14, time_scale=1, start_time=0, loop=True, trans_time=1)
        # source event 76, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 77, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 81, 37s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_jacobo_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_40', None)
        obj_Char_jacobo.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 45: source 39s; allocated facial window 10s.
        t = 0
        # source event 82, 39s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 83, 39s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_btm', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_45', None)
        obj_Char_jacobo.facial(group=MAIN, index=45, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6)

        # Line 50: source 43s; allocated facial window 10s.
        t = 0
        # source event 86, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_stand')
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_50', None)
        obj_Char_trent.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6)

        # Line 60: source 47s; allocated facial window 20s.
        t = 0
        # source event 100, 47s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_fingerprint')
        t += 2
        # source event 91, 49s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 92, 49s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_notebook_screen', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 111, 49s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_SPCBODY_s020x_VanPelt_XC_CHRF_TYPE_000DN_06, duration=6, time_scale=1, start_time=0, loop=True, trans_time=1)
        # source event 112, 49s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_keyboard_flurry03', duration=6, start_time=0, loop=True)
        t += 2
        # source event 118, 51s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_ui_react_accept01', duration=2, start_time=0, loop=False)
        t += 1
        # source event 93, 52s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen_left', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 119, 52.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_ui_react_accept02', duration=2, start_time=0, loop=False)
        t += 0.5
        # source event 94, 53s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen_right', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 120, 53s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_ui_react_accept02', duration=2, start_time=0, loop=False)
        t += 0.5
        # source event 121, 53.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_ui_react_accept02', duration=2, start_time=0, loop=False)
        t += 0.5
        # source event 95, 54s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 122, 55s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_ui_react_data01', duration=2, start_time=0, loop=False)
        t += 1
        # source event 96, 56s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 97, 56s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_btm', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 113, 57s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 114, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_CONV_RHND_CASL_000LV_XC_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 115, 59s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 98, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 99, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_notebook_screen', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 116, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_SPCBODY_s020x_VanPelt_XC_CHRF_TYPE_000DN_06, duration=7, time_scale=1, start_time=0, loop=True, trans_time=1)
        # source event 117, 61s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sfx_keyboard_flurry01', duration=6, start_time=0, loop=True)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_60', None)
        obj_Char_jacobo.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 70: source 63s; allocated facial window 4s.
        t = 0
        # source event 123, 63s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_stand')
        # source event 128, 63s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_SMALL_000LV_xa_05, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 131, 66s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_fingerprint')
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 80: source 67s; allocated facial window 5s.
        t = 0
        # source event 129, 67s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_trent_btm', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 130, 67s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_jacobo_front', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 136, 68s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_IDLE_SMALL_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_80', None)
        obj_Char_jacobo.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 90: source 70s; allocated facial window 12.5s.
        t = 0
        # source event 138, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo', duration=0.0001, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 139, 70s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_stand_far')
        # source event 146, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_stand_far', target_name='automarker_cam_trent_stand_far_pos2', duration=13, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 152, 70s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 137, 71s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=22, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 153, 71s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 4
        # source event 154, 75s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=2, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 156, 76.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_GESTR_THUMB_000LV_00, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.0
        # source event 155, 77.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_GESTR_180LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 159, 77.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo_outside_half', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 160, 77.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo_outside', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 161, 78.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 162, 78.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 158, 79s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender', anim=Male.Sc_MLBODY_STND_000DN_A_29, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 157, 80s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_GESTR_THUMB_000LV_00, duration=5, time_scale=1, start_time=2, loop=False, trans_time=None)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 100: source 83s; allocated facial window 5s.
        t = 0
        # source event 163, 83s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_notebook_screen', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 164, 83s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_notebook_screen_left', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 167, 83s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_fingerprint')
        # source event 172, 83s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 174, 84s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='prop_notebook', anim='Sc_close', duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 165, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_jacobo_standing', duration=2.9, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 166, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_jacobo_standing', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 173, 85s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_STNDCR_TRNS_090LV_XA_05, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 175, 87s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 176, 87s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 177, 87s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo_final_init', duration=0.0001, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 178, 87s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo_final_init', duration=0.0001, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 195, 87s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_final', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_100', None)
        obj_Char_jacobo.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 179, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo_final_done', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 180, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo_final_done', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 183, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_head_trent_final_half', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 184, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_head_trent_final', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 187, 88s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_walkout1')
        # source event 190, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_walkout1', target_name='automarker_cam_walkout1_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 191, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_walkout1_focus', target_name='automarker_cam_walkout1_point2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 192, 88s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_notebook', parent_name='Char_jacobo', duration=28, target_hardpoint='HpHandConnect', parent_hardpoint='HpLeftConnect')
        # source event 193, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_NEUT_WALK_LEFT_000LV_XA_, duration=1, time_scale=2, start_time=0, loop=False, trans_time=None)
        # source event 194, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='prop_notebook', anim='Sc_close', duration=1, time_scale=5, start_time=0, loop=False, trans_time=None)
        # source event 196, 88s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', target_name='automarker_point_jacobo_final', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 199, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 206, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_000DN_A_29, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 207, 89s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(1.5)

        # Line 110: source 89.5s; allocated facial window 5s.
        t = 0
        t += 1.0
        # source event 200, 90.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        t += 1.0
        # source event 201, 91.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_STND_CONV_RHND_CASL_000LV_xa_01, duration=2, time_scale=1, start_time=0, loop=True, trans_time=1.5)
        # source event 203, 91.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLHAND_HNEUT_GESTR_CASL_000LV_00, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        t += 0.5
        # source event 208, 92s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_000DN_A_29, duration=4, time_scale=0.6, start_time=0, loop=True, trans_time=1)
        t += 1.5
        # source event 202, 93.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.5)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_110', None)
        obj_Char_jacobo.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 181, 94.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_trent_final_front', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 182, 94.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_trent_final_front', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 185, 95s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_head_ik', target_name='automarker_jacobo_final_front', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 186, 95s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_jacobo_eye_ik', target_name='automarker_jacobo_final_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 204, 95s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XC_02, duration=2, time_scale=1.5, start_time=0, loop=False, trans_time=None)
        # source event 209, 95s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        main_group.append_time(2.0)

        # Line 120: source 96.5s; allocated facial window 5s.
        t = 0
        # source event 205, 96.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_WALK_GEST_RHND_TLKING_000LV_XB_02, duration=18, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 210, 96.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=30, time_scale=0.8, start_time=0, loop=True, trans_time=None)
        # source event 211, 96.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_walkout2')
        # source event 214, 96.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_walkout2', target_name='automarker_cam_walkout2_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 215, 96.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_walkout2_focus', target_name='automarker_cam_walkout2_point2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 2, 'Msn2Miner', 'm02_miner')
        self.groups.pop('motion_120', None)
        obj_Char_jacobo.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(2.5)
        restore_dialogue(self)
