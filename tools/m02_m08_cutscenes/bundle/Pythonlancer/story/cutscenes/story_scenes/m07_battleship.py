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


class Asset_obj_prop_notebook(Prop):
    COMPOUND_TEMPLATE_NAME = 'notebook'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_tome(Prop):
    COMPOUND_TEMPLATE_NAME = 'tome_075'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_battleship'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_prop_cigarette_2 = Asset_obj_prop_cigarette_2(root=self, name='prop_cigarette_2', light_group=0, init_point='prop_cigarette_2', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_prop_cigarette_2, {'template_name': 'cigarette_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_prop_notebook = Asset_obj_prop_notebook(root=self, name='prop_notebook', light_group=0, init_point='prop_notebook', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_notebook, {'template_name': 'notebook', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_tome = Asset_obj_prop_tome(root=self, name='prop_tome', light_group=0, init_point='prop_tome', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_tome, {'template_name': 'tome_075', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_LIGHT_trent2 = Light(root=self, name='LIGHT_trent2', point_name='LIGHT_trent2', extra_name='', light_group=30, diffuse=[0.8, 0.8, 0.8], ambient=[0.1, 0.15, 0.18], direction=[0, 0, -1], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_trent2, {'template_name': '', 'lt_grp': 30, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.8, 0.8, 0.8], 'specular': [0, 0, 0], 'ambient': [0.1, 0.15, 0.18], 'direction': [0, 0, -1], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=30, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 30, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_bartender = Character(root=self, actor=actors.WalesBarman, light_group=0, init_point='Char_barman', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_Char_bartender, {'template_name': 'm07_bartender_bship', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Bartender_Battleship', 'category': 'Character'}})
        obj_Char_darcy = Character(root=self, actor=actors.Darcy, light_group=0, init_point='Char_darcy', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_darcy, {'template_name': 'darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Darcy', 'category': 'Character'}})
        obj_cam_trent_runner = LookAtCamera(root=self, name='cam_trent_runner', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_runner, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_bartender = LookAtCamera(root=self, name='cam_bartender', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_bartender, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_intro = LookAtCamera(root=self, name='cam_darcy_intro', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy_intro, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy = LookAtCamera(root=self, name='cam_darcy', fov=15, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_darcy, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_artifact = LookAtCamera(root=self, name='cam_darcy_artifact', fov=19, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_darcy_artifact, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 19, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 8, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_runner')
        # source event 9, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=0.1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 10, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-60, axis='Y_AXIS', duration=0, smooth=False)
        # source event 11, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', angle=5, axis='Y_AXIS', duration=0, smooth=False)
        # source event 11.9, 0s
        MoveFastEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_Char_trent_runner')
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_RNNG_STND_TRNS_000LV_XA_07, duration=5, time_scale=0.7, start_time=0.3, loop=False, trans_time=None)
        # source event 13, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=30, axis='Y_AXIS', duration=1, smooth=False)
        t += 1
        # source event 16, 1s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_barman', target_name='automarker_bartender_head_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 17, 1s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_barman', target_name='automarker_bartender_eye_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(2.5)

        # Line 10: source 2.5s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        voice_sound = self.lookup_single_sound(10)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 15, 2.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.GENERIC_ANIM, duration=6, start_time=0, time_scale=1, trans_time=0.25)
        main_group.append_time(3.3)

        # Line 20: source 5.8s; allocated facial window 6s.
        t = 0
        # source event 18, 5.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_bartender')
        t += 3.0
        # source event 23, 8.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_bartender_head_ik', target_name='automarker_darcy_sit_point', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 24, 8.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_bartender_eye_ik', target_name='automarker_darcy_sit_point', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 26, 9.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_POINT_LHND_000LV_A_04, duration=15, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 25, 10.8s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', angle=15, axis='Y_AXIS', duration=3, smooth=False)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_20', None)
        obj_Char_bartender.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 30: source 11.8s; allocated facial window 6s.
        t = 0
        t += 4.2
        # source event 30, 16s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='automarker_darcy_eye_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 31, 16s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='prop_notebook', angle=-46, axis='Y_AXIS', duration=0, smooth=False)
        # source event 32, 16s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 33, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRF_HEAD_HOLDR_000LV_XA_02, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.01
        # source event 34, 16.01s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHAND_HNEUT_GESTR_THUMB_000LV_00, duration=0.1, time_scale=1, start_time=0.3, loop=False, trans_time=None)
        t += 1.0
        # source event 35, 17.01s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHAND_WALK_TALK_LEFT_CASL_000LV_XB_, duration=7, time_scale=0.8, start_time=0.5, loop=True, trans_time=1)
        t += 0.49
        # source event 27, 17.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_intro')
        # source event 28, 17.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_darcy_intro', target_name='automarker_cam_darcy_intro_pos2', duration=5.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 29, 17.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_darcy_intro_focus', target_name='automarker_cam_darcy_intro_marker_pos2', duration=7.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_30', None)
        obj_Char_bartender.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.2
        # source event 36, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_near_darcy_wlkg', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 39, 19s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 40, 19s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.0001
        # source event 36.9, 20.0001s
        MoveFastEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_Char_trent')
        # source event 37, 20.0001s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=6, time_scale=0.65, start_time=0, loop=False, trans_time=None)
        main_group.append_time(5.5)

        # Line 40: source 23.3s; allocated facial window 12s.
        t = 0
        # source event 41, 23.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        t += 0.9
        # source event 38, 24.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=6, time_scale=0.65, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.3)

        # Line 50: source 29s; allocated facial window 27s.
        t = 0
        # source event 44, 29s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy')
        # source event 45, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRF_HOLD_HEAD_RLEASE_000LV_XA_03, duration=7, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 46, 30s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHAND_NEUT_RGHT_000LV_A_00, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 47, 30s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='automarker_darcy_head_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 48, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_50', None)
        obj_Char_darcy.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19)

        # Line 60: source 37s; allocated facial window 28.5s.
        t = 0
        # source event 49, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 50, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRF_CONV_RHND_CASL_000LV_XA_03, duration=3, time_scale=0.4, start_time=0, loop=True, trans_time=1)
        # source event 52, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        # source event 53, 38s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_darcy_notebook_view_top', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 54, 38s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_darcy_notebook_view', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 51, 41s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 5
        # source event 55, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 56, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_60', None)
        obj_Char_darcy.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19.0)

        # Line 70: source 46.5s; allocated facial window 25s.
        t = 0
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_70', None)
        obj_Char_darcy.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-18.0)

        # Line 80: source 53.5s; allocated facial window 12s.
        t = 0
        # source event 65, 53.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 4.0
        # source event 66, 57.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=6, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_80', None)
        obj_Char_trent.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.0)

        # Line 90: source 58.5s; allocated facial window 12s.
        t = 0
        t += 2.0
        # source event 67, 60.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_GIVE_VEND_000LV_B_07, duration=12, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 80, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_tome', target_name='automarker_point_tome_darcy_hand', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 83, 62s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', target_name='automarker_point_darcy_init', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 84, 62.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-10, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.5
        # source event 75, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_darcy_tome_view_top_upper', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 76, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_darcy_tome_view', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 81, 63s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='prop_tome', angle=35, axis='Y_AXIS', duration=0, smooth=False)
        # source event 85, 63s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_GRABR_PRDRNK_TABL_000LV_XA_09, duration=0, time_scale=0.8, start_time=5.3, loop=False, trans_time=None)
        t += 0.2
        # source event 82, 63.2s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='prop_tome', angle=15.5, axis='Z_AXIS', duration=0, smooth=False)
        t += 0.1
        # source event 86, 63.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHAND_HNEUT_GESTL_THUMB_000LV_00, duration=0.1, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 0.3
        # source event 87, 63.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMHAND_HNEUT_HOLDD_RGHT_000LV_00, duration=0.1, time_scale=1, start_time=0.8, loop=False, trans_time=None)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.5)

        # Line 100: source 65s; allocated facial window 3s.
        t = 0
        # source event 72, 65s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_artifact')
        # source event 73, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_darcy_artifact', target_name='automarker_cam_darcy_artifact_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 74, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_darcy_artifact_focus', target_name='automarker_cam_darcy_artifact_marker_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_100', None)
        obj_Char_darcy.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 110: source 68s; allocated facial window 25.2s.
        t = 0
        # source event 77, 68s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_darcy_tome_view_top', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 78, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 79, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_110', None)
        obj_Char_darcy.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-17.2)

        # Line 120: source 76s; allocated facial window 12s.
        t = 0
        # source event 92, 76s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 93, 76s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_120', None)
        obj_Char_trent.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10)

        # Line 130: source 78s; allocated facial window 25s.
        t = 0
        # source event 96, 78s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy')
        t += 5.5
        # source event 97, 83.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_darcy_tome_view_top_upper', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 98, 83.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_darcy_tome_view', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_130', None)
        obj_Char_darcy.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19)

        # Line 140: source 84s; allocated facial window 27s.
        t = 0
        t += 2.5
        # source event 99, 86.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 100, 86.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_140', None)
        obj_Char_darcy.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19.5)

        # Line 150: source 91.5s; allocated facial window 28.5s.
        t = 0
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_150', None)
        obj_Char_darcy.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-18.0)

        # Line 160: source 102s; allocated facial window 12s.
        t = 0
        # source event 109, 102s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 2
        # source event 110, 104s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=6, time_scale=0.65, start_time=0, loop=False, trans_time=1)
        t += 4
        # source event 113, 108s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_tome', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 114, 108s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', target_name='automarker_point_darcy_init', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 115, 108.1s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.1
        # source event 116, 108.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_160', None)
        obj_Char_trent.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5)

        # Line 170: source 109s; allocated facial window 25s.
        t = 0
        # source event 117, 109s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_darcy_notebook_view_top', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 118, 109s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_darcy_notebook_view', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 121, 109s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy')
        t += 3
        # source event 119, 112s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 120, 112s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_170', None)
        obj_Char_darcy.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-21.5)

        # Line 180: source 112.5s; allocated facial window 30s.
        t = 0
        t += 4.5
        # source event 127, 117s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=122, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 6.0
        # source event 128, 123s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 7, 'Msn7Battleship', 'm07_battleship')
        self.groups.pop('motion_180', None)
        obj_Char_darcy.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-19.5)
        restore_dialogue(self)
