"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_PlayerShip(Ship):
    COMPOUND_TEMPLATE_NAME = 'PlayerShip'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prisoners_ship02(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prisoners_ship03(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_test_vehicle(Ship):
    COMPOUND_TEMPLATE_NAME = 'li_elite'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_prisoner1(actors.Actor):
    NAME = 'prisoner1'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner01'
    GAME_ACTOR = 'Prisoner1'


class Actor_obj_Char_prisoner2(actors.Actor):
    NAME = 'prisoner2'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner02'
    GAME_ACTOR = 'Prisoner2'


class Actor_obj_Char_prisoner3(actors.Actor):
    NAME = 'prisoner3'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner03'
    GAME_ACTOR = 'Prisoner3'


class Actor_obj_Char_prisoner4(actors.Actor):
    NAME = 'prisoner4'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner04'
    GAME_ACTOR = 'Prisoner4'


class Actor_obj_Char_commander(actors.Actor):
    NAME = 'commander'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_gunner_leader'
    GAME_ACTOR = 'Gunner_commander'


class Actor_obj_Char_gunner01(actors.Actor):
    NAME = 'gunner01'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_gunner_sides1'
    GAME_ACTOR = 'Gunner2'


class Actor_obj_Char_gunner02(actors.Actor):
    NAME = 'gunner02'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_gunner_sides2'
    GAME_ACTOR = 'Gunner3'


class Actor_obj_Char_gunner03(actors.Actor):
    NAME = 'gunner03'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_gunner_back1'
    GAME_ACTOR = 'Gunner4'


class Actor_obj_Char_gunner04(actors.Actor):
    NAME = 'gunner04'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_gunner_back2'
    GAME_ACTOR = 'Gunner5'


class Actor_obj_Char_syd_guard(actors.Actor):
    NAME = 'syd_guard'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_gunner_syd'
    GAME_ACTOR = 'GunnerSyd'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_order_deck'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_music_main = Sound(root=self, name='music_main', sound='music_discordant_psychosis', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_main, {'template_name': 'music_discordant_psychosis', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_PlayerShip = Asset_obj_PlayerShip(root=self, name='PlayerShip', light_group=3, init_point='PlayerShip', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_PlayerShip, {'template_name': 'PlayerShip', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship'}})
        obj_prisoners_ship02 = Asset_obj_prisoners_ship02(root=self, name='prisoners_ship02', light_group=3, init_point='prisoners_ship02', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prisoners_ship02, {'template_name': 'li_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04'}})
        obj_prisoners_ship03 = Asset_obj_prisoners_ship03(root=self, name='prisoners_ship03', light_group=3, init_point='prisoners_ship03', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prisoners_ship03, {'template_name': 'li_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04'}})
        obj_test_vehicle = Asset_obj_test_vehicle(root=self, name='test_vehicle', light_group=3, init_point='test_vehicle', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_test_vehicle, {'template_name': 'li_elite', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Spaceship', 'loadout': 'level_li_elite_loadout04'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=3, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_prisoner1 = Character(root=self, actor=Actor_obj_Char_prisoner1, light_group=3, init_point='Char_prisoner1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner1, {'template_name': 'm06_asf_prisoner01', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner1', 'category': 'Character'}})
        obj_Char_prisoner2 = Character(root=self, actor=Actor_obj_Char_prisoner2, light_group=3, init_point='Char_prisoner2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner2, {'template_name': 'm06_asf_prisoner02', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner2', 'category': 'Character'}})
        obj_Char_prisoner3 = Character(root=self, actor=Actor_obj_Char_prisoner3, light_group=3, init_point='Char_prisoner3', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner3, {'template_name': 'm06_asf_prisoner03', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner3', 'category': 'Character'}})
        obj_Char_prisoner4 = Character(root=self, actor=Actor_obj_Char_prisoner4, light_group=3, init_point='Char_prisoner4', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner4, {'template_name': 'm06_asf_prisoner04', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner4', 'category': 'Character'}})
        obj_Char_commander = Character(root=self, actor=Actor_obj_Char_commander, light_group=3, init_point='Char_commander', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_commander, {'template_name': 'm06_gunner_leader', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Gunner_commander', 'category': 'Character'}})
        obj_Char_gunner01 = Character(root=self, actor=Actor_obj_Char_gunner01, light_group=3, init_point='Char_gunner01', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_gunner01, {'template_name': 'm06_gunner_sides1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Gunner2', 'category': 'Character'}})
        obj_Char_gunner02 = Character(root=self, actor=Actor_obj_Char_gunner02, light_group=3, init_point='Char_gunner02', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_gunner02, {'template_name': 'm06_gunner_sides2', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Gunner3', 'category': 'Character'}})
        obj_Char_gunner03 = Character(root=self, actor=Actor_obj_Char_gunner03, light_group=3, init_point='Char_gunner03', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_gunner03, {'template_name': 'm06_gunner_back1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Gunner4', 'category': 'Character'}})
        obj_Char_gunner04 = Character(root=self, actor=Actor_obj_Char_gunner04, light_group=3, init_point='Char_gunner04', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_gunner04, {'template_name': 'm06_gunner_back2', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Gunner5', 'category': 'Character'}})
        obj_Char_syd = Character(root=self, actor=actors.Ceed, light_group=3, init_point='Char_syd', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_syd, {'template_name': 'syd', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Syd', 'category': 'Character'}})
        obj_Char_syd_guard = Character(root=self, actor=Actor_obj_Char_syd_guard, light_group=3, init_point='Char_syd_guard', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_syd_guard, {'template_name': 'm06_gunner_syd', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'GunnerSyd', 'category': 'Character'}})
        obj_cam_entry = StaticCamera(root=self, name='cam_entry', fov=25, farplane=5000)
        preserve_entity(obj_cam_entry, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_Path_cam_entry = MotionPath(root=self, name='Path_cam_entry', point_name='Path_cam_entry', path_data='{-15, 11, -25}, {0.5,0,-0.5,0},   {-10, 5, -10}, {0.8,0,-0.2,0},   {0, 4, 5}, {0.6,0,0.4,0},  {10, 1, 6}, {0.3,0,0.7,0}')
        preserve_entity(obj_Path_cam_entry, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-15, 11, -25}, {0.5,0,-0.5,0},   {-10, 5, -10}, {0.8,0,-0.2,0},   {0, 4, 5}, {0.6,0,0.4,0},  {10, 1, 6}, {0.3,0,0.7,0},   '}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=20, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd = LookAtCamera(root=self, name='cam_syd', fov=18, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_syd, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 3, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=50, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 4, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 6, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 7, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 8, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_gunner01', anim=Male.Sc_MLBODY_STND_AIM_GUN_FRWD_000LV_XA_02, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 9, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_gunner02', anim=Male.Sc_SPCBODY_s019b_Drake_XA_STND_000LV_13, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_gunner03', anim=Male.Sc_SPCBODY_s019b_Drake_XA_STND_000LV_13, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 11, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_gunner04', anim=Male.Sc_MLBODY_STND_AIM_GUN_FRWD_000LV_XA_02, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_ATEASE_HOLD_000LV_XA_01, duration=1, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 13, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd_guard', anim=Male.Sc_MLBODY_STND_HOLD_RIFLE_MILI_000LV_XA_05, duration=555, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 14, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_entry')
        # source event 15, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['cam_entry', 'Path_cam_entry'], duration=25, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION+ORIENTATION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 44, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=47, start_time=0, loop=True)
        t += 22.9
        # source event 16, 22.9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_commander', target_name='automarker_point_commander_start', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 17, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_commander', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=7, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 5
        # source event 18, 28s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 20, 28s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_lookpoint_commander', duration=25, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 19, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_CONCNTRTE_TRENT_000LV_XA_, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 3
        # source event 22, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_commander', target_name='automarker_point_commander_around_syd', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 28, 32s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_head_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 29, 32s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_eye_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 23, 33s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_commander', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 26, 33s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd')
        # source event 27, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd', target_name='automarker_cam_syd_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 45, 33s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=5, attenuation=-15)
        main_group.append_time(35)

        # Line 10: source 35s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 6, 'Msn6OrderDeck', 'm06_order_deck')
        voice_sound = self.lookup_single_sound(10)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 24, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_commander', anim=Male.Sc_MLBODY_STND_SALUT_000LV_XA_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        # source event 30, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_lookpoint_syd_at_commander', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 31, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_lookpoint_syd_at_commander', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(4)

        # Line 20: source 39s; allocated facial window 19s.
        t = 0
        t += 0.5
        # source event 32, 39.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_lookpoint_syd_forward', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 33, 39.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_lookpoint_syd_forward', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3.5
        # source event 34, 43s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_lookpoint_syd_at_commander', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 43s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_lookpoint_syd_at_commander', duration=1.1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 36, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_lookpoint_syd_forward', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_lookpoint_syd_forward', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 42, 46.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_ATEASE_RLEASE_000LV_XA_01, duration=15, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 43, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6OrderDeck', 'm06_order_deck')
        self.groups.pop('motion_20', None)
        obj_Char_syd.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.0)
        restore_dialogue(self)
