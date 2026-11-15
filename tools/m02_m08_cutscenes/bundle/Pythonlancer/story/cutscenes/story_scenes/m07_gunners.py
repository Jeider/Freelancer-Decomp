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


class Asset_obj_Prop_barcloth_wadded_Bart(Prop):
    COMPOUND_TEMPLATE_NAME = 'barcloth_wadded'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_glass_green(Prop):
    COMPOUND_TEMPLATE_NAME = 'glass_green'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_jester_gun(Prop):
    COMPOUND_TEMPLATE_NAME = 'prop_gun_laser_1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_hammer_gun(Prop):
    COMPOUND_TEMPLATE_NAME = 'gun_laser_2'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_rockford_rifle(Prop):
    COMPOUND_TEMPLATE_NAME = 'rifle'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_peasant(actors.Actor):
    NAME = 'peasant'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'tyler'
    GAME_ACTOR = 'Peasant'


class Actor_obj_Char_jester2(actors.Actor):
    NAME = 'jester2'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'jester'
    GAME_ACTOR = 'jester2'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_gunners'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_music_hall_ambient = Sound(root=self, name='music_hall_ambient', sound='ambience_bar_space', attenuation=-12, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_hall_ambient, {'template_name': 'ambience_bar_space', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -12, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_bar = Sound(root=self, name='music_bar', sound='music_bar_generic03', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_bar, {'template_name': 'music_bar_generic03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_danger = Sound(root=self, name='music_danger', sound='rtc_m07_bg_mix', attenuation=-100, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_danger, {'template_name': 'rtc_m07_bg_mix', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -100, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_fire_attempt = Sound(root=self, name='music_fire_attempt', sound='rtc_m07_fire_attempt', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_fire_attempt, {'template_name': 'rtc_m07_fire_attempt', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_sound_fire_rockford = Sound(root=self, name='sound_fire_rockford', sound='fire_rifle', attenuation=0, dmin=50, dmax=300, priority=None)
        preserve_entity(obj_sound_fire_rockford, {'template_name': 'fire_rifle', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sound_fire_rockford2 = Sound(root=self, name='sound_fire_rockford2', sound='fire_rifle_alt', attenuation=0, dmin=50, dmax=300, priority=None)
        preserve_entity(obj_sound_fire_rockford2, {'template_name': 'fire_rifle_alt', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Prop_barcloth_wadded_Bart = Asset_obj_Prop_barcloth_wadded_Bart(root=self, name='Prop_barcloth_wadded_Bart', light_group=0, init_point='Prop_barcloth_wadded_Bart', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_Prop_barcloth_wadded_Bart, {'template_name': 'barcloth_wadded', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Prop_glass_green = Asset_obj_Prop_glass_green(root=self, name='Prop_glass_green', light_group=0, init_point='Prop_glass_green', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_Prop_glass_green, {'template_name': 'glass_green', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_jester_gun = Asset_obj_prop_jester_gun(root=self, name='prop_jester_gun', light_group=0, init_point='prop_jester_gun', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_jester_gun, {'template_name': 'prop_gun_laser_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_hammer_gun = Asset_obj_prop_hammer_gun(root=self, name='prop_hammer_gun', light_group=0, init_point='prop_hammer_gun', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_hammer_gun, {'template_name': 'gun_laser_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_rockford_rifle = Asset_obj_prop_rockford_rifle(root=self, name='prop_rockford_rifle', light_group=0, init_point='prop_rockford_rifle', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_rockford_rifle, {'template_name': 'rifle', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_barman = Character(root=self, actor=actors.DetroitBarman, light_group=0, init_point='Char_barman', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_barman, {'template_name': 'martin', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Barman', 'category': 'Character'}})
        obj_Char_peasant = Character(root=self, actor=Actor_obj_Char_peasant, light_group=0, init_point='Char_peasant', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_peasant, {'template_name': 'tyler', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Peasant', 'category': 'Character'}})
        obj_Char_hammer = Character(root=self, actor=actors.CadizEnemyTwo, light_group=0, init_point='Char_enemy2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hammer, {'template_name': 'hammer', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'hammer', 'category': 'Character'}})
        obj_Char_jester = Character(root=self, actor=actors.CadizEnemyOne, light_group=0, init_point='Char_enemy1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jester, {'template_name': 'jester', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'jester', 'category': 'Character'}})
        obj_Char_jester2 = Character(root=self, actor=Actor_obj_Char_jester2, light_group=0, init_point='Char_jester2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jester2, {'template_name': 'jester', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'jester2', 'category': 'Character'}})
        obj_Char_rockford = Character(root=self, actor=actors.Rockford, light_group=0, init_point='Char_rockford', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_rockford, {'template_name': 'rockford', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'rockford', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=30, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 30, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_sit = LookAtCamera(root=self, name='cam_sit', fov=22, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_sit, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_barman = LookAtCamera(root=self, name='cam_barman', fov=18, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_barman, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hammer_reveal = LookAtCamera(root=self, name='cam_hammer_reveal', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_hammer_reveal, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jester_ready = LookAtCamera(root=self, name='cam_jester_ready', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_jester_ready, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jester_standing = LookAtCamera(root=self, name='cam_jester_standing', fov=26, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_jester_standing, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 26, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_greet = LookAtCamera(root=self, name='cam_greet', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_greet, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hammer_anger = LookAtCamera(root=self, name='cam_hammer_anger', fov=12, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_hammer_anger, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 12, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jester_aim = LookAtCamera(root=self, name='cam_jester_aim', fov=17, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_jester_aim, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 17, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_jester_fire = LookAtCamera(root=self, name='cam_jester_fire', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_jester_fire, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_fire = LookAtCamera(root=self, name='cam_trent_fire', fov=18, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_fire, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hammer_death = LookAtCamera(root=self, name='cam_hammer_death', fov=16, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_hammer_death, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_rockford_appear = LookAtCamera(root=self, name='cam_rockford_appear', fov=11, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_rockford_appear, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 11, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_fadenegative_variable_1 = Alchemy(root=self, name='fadenegative_variable_1', particles='rtc_fadenegative_variable', point_name='fadenegative_variable_1', sparam=0)
        preserve_entity(obj_fadenegative_variable_1, {'template_name': 'rtc_fadenegative_variable', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        t = 0
        # source event 14, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 15, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 16, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 17, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 18, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 19, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 22, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='Prop_barcloth_wadded_Bart', parent_name='Char_barman', duration=35, target_hardpoint='hprightconnect_prop_barcloth_wadded', parent_hardpoint='hprightconnect')
        # source event 23, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='Prop_glass_green', parent_name='Char_barman', duration=35, target_hardpoint='hpleftconnect_prop_glass_green', parent_hardpoint='hpleftconnect')
        # source event 125, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_hall_ambient', duration=108, start_time=0, loop=True)
        # source event 126, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_bar', duration=25, start_time=0, loop=True)
        t += 0.25
        # source event 20, 0.25s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=25, axis='Y_AXIS', duration=2, smooth=True)
        t += 3.0
        # source event 21, 3.25s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-115, axis='Y_AXIS', duration=4, smooth=True)
        t += 3.75
        # source event 25, 7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_CLEAN_GLAS_000LV_A_26, duration=10, time_scale=1, start_time=4, loop=False, trans_time=None)
        # source event 27, 7s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', angle=-45, axis='Y_AXIS', duration=1, smooth=True)
        t += 1
        # source event 24, 8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_barman')
        # source event 26, 8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_peasant', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 4.9
        # source event 33, 12.9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_stand_to_sit', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 34, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SITCR_TRNS_090DN_XA_07, duration=15, time_scale=1, start_time=1, loop=False, trans_time=None)
        t += 1
        # source event 28, 14s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hammer_reveal')
        # source event 29, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hammer_reveal', target_name='automarker_cam_hammer_reveal_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 30, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hammer_reveal_focus', target_name='automarker_cam_hammer_reveal_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 38, 15s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-20, axis='Y_AXIS', duration=1, smooth=True)
        t += 2
        # source event 35, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 31, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLBODY_CHRB_GESTR_180LV_XA_03, duration=15, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        # source event 32, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLHAND_HNEUT_GESTR_THUMB_000LV_00, duration=0.2, time_scale=1, start_time=2, loop=False, trans_time=None)
        # source event 36, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_TWSTS_LOOK_090LV_XA_02, duration=15, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 128, 20s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_danger', duration=28, start_time=0, loop=True)
        # source event 129, 20s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_danger', duration=5, attenuation=-5)
        t += 2
        # source event 37, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_TWSTS_FROM_090LV_XA_02, duration=15, time_scale=0.65, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 41, 24s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_jester_gun', parent_name='Char_enemy1', duration=159.45, target_hardpoint='hprightconnect_gun', parent_hardpoint='hprightconnect')
        # source event 42, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_MLHAND_HNEUT_GUN_RGHT_000LV_XB_00, duration=0.2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 39, 25s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jester_ready')
        # source event 45, 25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        # source event 127, 25s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_bar', duration=5, attenuation=-100)
        t += 3
        # source event 43, 28s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_hammer_gun', parent_name='Char_enemy2', duration=159.45, target_hardpoint='hprightconnect_gun', parent_hardpoint='hprightconnect')
        # source event 44, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLHAND_HNEUT_GUN_RGHT_000LV_XB_00, duration=0.2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.8
        # source event 40, 28.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jester_standing')
        t += 0.2
        # source event 46, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_270LV_XA_10, duration=3.9, time_scale=0.8, start_time=1.5, loop=False, trans_time=1)
        # source event 50, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_CLEAN_GLAS_000LV_A_26, duration=3, time_scale=1, start_time=7, loop=False, trans_time=None)
        t += 1
        # source event 47, 30s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', angle=-80, axis='Y_AXIS', duration=3, smooth=True)
        # source event 48, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_peasant', anim=Male.Sc_MLBODY_STND_RUN_TRNS_000LV_XD_02, duration=10, time_scale=0.68, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 49, 31.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_peasant', angle=-45, axis='Y_AXIS', duration=2, smooth=True)
        t += 0.5
        # source event 51, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_CROUCHNG_IDLE_000DN_XA_03, duration=10, time_scale=1, start_time=0, loop=False, trans_time=2)
        # source event 52, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 56, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLBODY_CHRB_STNDCR_TRNS_090LV_XA_05, duration=15, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 57, 32.1s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', angle=-90, axis='Y_AXIS', duration=3, smooth=True)
        t += 0.85
        # source event 58, 32.95s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', target_name='automarker_point_jester_ask', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.05
        # source event 53, 33s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_greet')
        # source event 54, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_greet', target_name='automarker_cam_greet_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 55, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_greet_focus', target_name='automarker_cam_greet_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 61, 33s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=15, time_scale=0.8, start_time=0.5, loop=False, trans_time=None)
        # source event 62, 33s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', angle=-40, axis='Y_AXIS', duration=2, smooth=True)
        # source event 64, 33s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_enemy1', target_name='Char_trent', duration=23, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.3
        # source event 63, 33.3s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_enemy1', duration=40, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(34)

        # Line 10: source 34s; allocated facial window 6s.
        t = 0
        # source event 59, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_peasant', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 60, 34s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 65, 34s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_enemy2', target_name='Char_trent', duration=22, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        self.groups.pop('motion_10', None)
        obj_Char_jester.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 20: source 37s; allocated facial window 3.5s.
        t = 0
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 30: source 39s; allocated facial window 17.5s.
        t = 0
        # source event 71, 39s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hammer_anger')
        t += 1
        # source event 70, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=4.444, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        # source event 75, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 3.5
        # source event 76, 43.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=15, time_scale=0.8, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        self.groups.pop('motion_30', None)
        obj_Char_hammer.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.5)

        # Line 40: source 47s; allocated facial window 6s.
        t = 0
        # source event 77, 47s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jester_aim')
        t += 1
        # source event 80, 48s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_SPCBODY_s019b_Drake_XA_STND_000LV_13, duration=3.5, time_scale=0.7, start_time=0, loop=False, trans_time=1.5)
        # source event 99, 48s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_fire_attempt', duration=20, start_time=0, loop=False)
        # source event 130, 48s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_danger', duration=3, attenuation=-100)
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        self.groups.pop('motion_40', None)
        obj_Char_jester.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 50: source 49s; allocated facial window 9.9s.
        t = 0
        t += 2.3
        # source event 85, 51.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_MOTION_EYES_OPENBG_TRENT_000LV_XA_, duration=2, time_scale=1, start_time=0, loop=False, trans_time=0.1)
        t += 0.2
        # source event 83, 51.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_fire')
        # source event 84, 51.5s
        CameraAnimEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_fire', duration=5, fov=18, smooth=True)
        # source event 86, 51.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_GEST_HNDS_WAIT_000LV_XA_03, duration=15, time_scale=0.3, start_time=2, loop=False, trans_time=None)
        t += 2.5
        # source event 87, 54s
        CameraAnimEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jester_fire', duration=3, fov=17, smooth=True)
        t += 0.5
        # source event 88, 54.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jester_fire')
        # source event 89, 54.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim='Sc_SPCBODY_s019b_Drake_XB_STND_000LV_%', duration=6, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 90, 54.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_MLHEAD_MAD_COLD_000LV_XA_, duration=3, time_scale=0.6, start_time=0.5, loop=False, trans_time=None)
        t += 1.5
        # source event 91, 56s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fadenegative_variable_1'], duration=0, psysprops={'sparam': 1})
        t += 0.7
        # source event 92, 56.7s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fadenegative_variable_1', 'cam_jester_fire'], duration=0.308, offset=[0, 0, -0.5], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 93, 56.7s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fadenegative_variable_1', duration=0.307)
        # source event 94, 56.7s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fadenegative_variable_1'], duration=0.307, psysprops={'sparam': 0}, param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 100, 56.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_fire_rockford', duration=20, start_time=0, loop=False)
        t += 0.2
        # source event 104, 56.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', anim=Male.Sc_SPCBODY_s051x_ku_guard01_XC_STND_DEATH_225DN_03, duration=5, time_scale=0.8, start_time=1, loop=False, trans_time=1.5)
        t += 0.1
        # source event 106, 57s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.Sc_SPCBODY_s002x_Vance_XD_STND_000DN_03, duration=15, time_scale=1.3, start_time=0, loop=False, trans_time=1)
        # source event 108, 57s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', angle=45, axis='Y_AXIS', duration=0, smooth=True)
        # source event 110, 57s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hammer_death')
        t += 0.1
        # source event 109, 57.1s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', angle=45, axis='Y_AXIS', duration=2, smooth=True)
        t += 0.1
        # source event 95, 57.2s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fadenegative_variable_1'], duration=0, psysprops={'sparam': 1})
        t += 0.2
        # source event 105, 57.4s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy1', angle=33, axis='Y_AXIS', duration=2, smooth=True)
        t += 0.1
        # source event 96, 57.5s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['fadenegative_variable_1', 'cam_hammer_death'], duration=0.508, offset=[0, 0, -0.5], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 97, 57.5s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='fadenegative_variable_1', duration=0.507)
        # source event 98, 57.5s
        SourceAlchemyAnimEvent(root=self, group=MAIN, time_delay=t, targets=['fadenegative_variable_1'], duration=0.507, psysprops={'sparam': 0}, param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 101, 57.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_fire_rockford2', duration=20, start_time=0, loop=False)
        # source event 102, 57.5s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_fire_attempt', duration=1, attenuation=-100)
        # source event 107, 57.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_enemy2', anim=Male.GENERIC_ANIM, duration=2, start_time=0, time_scale=1, trans_time=0.15)
        t += 0.5
        # source event 111, 58s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', target_name='automarker_point_rockford_aim', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 112, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', anim=Male.Sc_MLHAND_HNEUT_GUN_RGHT_000LV_00, duration=1, time_scale=2, start_time=0, loop=False, trans_time=None)
        # source event 113, 58s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', anim=Male.Sc_MLHAND_HNEUT_RIFLE_LEFT_000LV_00, duration=0.4, time_scale=2, start_time=0, loop=False, trans_time=None)
        # source event 114, 58s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_rockford_rifle', parent_name='Char_rockford', duration=59.45, target_hardpoint='hp_male_rhand_rifle', parent_hardpoint='hprightconnect')
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        self.groups.pop('motion_50', None)
        obj_Char_jester.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.1
        # source event 119, 59s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', anim=Male.Sc_SPCBODY_s010x_Rh_agent01_XA_STND_000LV_03, duration=0.2, time_scale=1, start_time=2, loop=False, trans_time=None)
        t += 1.0
        # source event 115, 60s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_rockford_appear')
        # source event 116, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_rockford_appear', target_name='automarker_cam_rockford_appear_pos2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 117, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_rockford_appear_focus', target_name='automarker_cam_rockford_appear_marker_pos2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 118, 60s
        CameraAnimEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_rockford_appear', duration=4, fov=22, smooth=True)
        main_group.append_time(2.6)

        # Line 60: source 61.5s; allocated facial window 6s.
        t = 0
        t += 2.0
        # source event 120, 63.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        self.groups.pop('motion_60', None)
        obj_Char_rockford.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 65: source 64s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Cadiz', 'm07_cadiz')
        voice_sound = self.lookup_single_sound(65)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        t += 0.55
        # source event 121, 64.55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_rockford', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        main_group.append_time(4.0)
        restore_dialogue(self)
