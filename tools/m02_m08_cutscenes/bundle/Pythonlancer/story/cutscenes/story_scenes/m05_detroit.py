"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_Prop_barcloth_wadded_Bart(Prop):
    COMPOUND_TEMPLATE_NAME = 'barcloth_wadded'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_glass_green(Prop):
    COMPOUND_TEMPLATE_NAME = 'glass_green'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_bartender_Fixture(actors.Actor):
    NAME = 'bartender_fixture'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'li_bartender_1'
    GAME_ACTOR = 'bartender'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_detroit'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Prop_barcloth_wadded_Bart = Asset_obj_Prop_barcloth_wadded_Bart(root=self, name='Prop_barcloth_wadded_Bart', light_group=0, init_point='Prop_barcloth_wadded_Bart', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_Prop_barcloth_wadded_Bart, {'template_name': 'barcloth_wadded', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Prop_glass_green = Asset_obj_Prop_glass_green(root=self, name='Prop_glass_green', light_group=0, init_point='Prop_glass_green', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_Prop_glass_green, {'template_name': 'glass_green', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_bartender = Character(root=self, actor=actors.DetroitBarman, light_group=0, init_point='Char_barman', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_bartender, {'template_name': 'm05_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'm05_barman', 'category': 'Character'}})
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_bartender = LookAtCamera(root=self, name='cam_bartender', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_bartender, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_bartender_closest = LookAtCamera(root=self, name='cam_bartender_closest', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_bartender_closest, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_bartender_near = LookAtCamera(root=self, name='cam_bartender_near', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_bartender_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_wlkg_trent = StaticCamera(root=self, name='cam_wlkg_trent', fov=15, farplane=5000)
        preserve_entity(obj_cam_wlkg_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 8, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='Prop_barcloth_wadded_Bart', parent_name='Char_barman', duration=512, target_hardpoint='hprightconnect_prop_barcloth_wadded', parent_hardpoint='hprightconnect')
        # source event 9, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 10, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=9.99, time_scale=0.9, start_time=0, loop=True, trans_time=None)
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_WIPE_BAR_000LV_A_24, duration=25, time_scale=0.95, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 11, 3s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=51, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 4
        # source event 13, 7s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=35, axis='Y_AXIS', duration=2.99, smooth=True)
        main_group.append_time(10)

        # Line 10: source 10s; allocated facial window 15s.
        t = 0
        # source event 15, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_stand', duration=1, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 16, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_bartender')
        t += 1
        # source event 17, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_LEAN_BAR_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_10', None)
        obj_Char_trent.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.5)

        # Line 20: source 15.5s; allocated facial window 15s.
        t = 0
        t += 1.5
        # source event 22, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_LEAN_STND_BAR_TRNS_000LV_XA_03, duration=3, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_20', None)
        obj_Char_bartender.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.5)

        # Line 30: source 20s; allocated facial window 15s.
        t = 0
        # source event 23, 20s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 24, 20s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 25, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_GIVE_VEND_000LV_B_07, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.5)

        # Line 40: source 26.5s; allocated facial window 17s.
        t = 0
        # source event 28, 26.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_bartender_near')
        # source event 29, 26.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=2, time_scale=0.2, start_time=0, loop=False, trans_time=None)
        t += 2.0
        # source event 30, 28.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_GESTL_180LV_XA_02, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 4.0
        # source event 31, 32.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_LOOK_WATC_IMPA_315DN_XA_07, duration=4.2, time_scale=0.9, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_40', None)
        obj_Char_bartender.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.0)

        # Line 45: source 35.5s; allocated facial window 15s.
        t = 0
        t += 1.2
        # source event 32, 36.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_CLEAN_GLAS_000LV_A_26, duration=55, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_45', None)
        obj_Char_bartender.facial(group=MAIN, index=45, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.5)

        # Line 50: source 40s; allocated facial window 15s.
        t = 0
        # source event 38, 40s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        # source event 39, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_LEAN_BAR_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 42, 42s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='Prop_glass_green', parent_name='Char_barman', duration=50, target_hardpoint='hpleftconnect_prop_glass_green', parent_hardpoint='hpleftconnect')
        # source event 43, 42s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLHAND_HNEUT_HOLDD_LEFT_000LV_00, duration=0.1, time_scale=1, start_time=5, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_50', None)
        obj_Char_trent.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-12)

        # Line 60: source 43s; allocated facial window 20s.
        t = 0
        # source event 44, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_bartender_near')
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_60', None)
        obj_Char_bartender.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9)

        # Line 70: source 54s; allocated facial window 15s.
        t = 0
        # source event 48, 54s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 51, 54s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_LEAN_STND_BAR_TRNS_000LV_XA_03, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 5
        # source event 52, 59s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 53, 61s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_walkout', duration=0.00011, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 54, 61s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_wlkg_trent', 'Char_trent'], duration=15, offset=[0.75, 0.6, 2], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION')
        # source event 55, 61s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_wlkg_trent')
        # source event 56, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XC_01, duration=25, time_scale=0.7, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7)

        # Line 80: source 62s; allocated facial window 15s.
        t = 0
        select_dialogue(self, 5, 'Msn5Detroit', 'm05_detroit')
        self.groups.pop('motion_80', None)
        obj_Char_trent.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.0)
        restore_dialogue(self)
