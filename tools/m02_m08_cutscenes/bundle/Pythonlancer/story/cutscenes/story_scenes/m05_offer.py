"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_hatcher_bottle(Prop):
    COMPOUND_TEMPLATE_NAME = 'bottle_wine_3'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_hatcher_glass(Prop):
    COMPOUND_TEMPLATE_NAME = 'glass'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_trent_glass(Prop):
    COMPOUND_TEMPLATE_NAME = 'glass'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_offer'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_ambi_LtG00_Tbl_rTable4_01 = Light(root=self, name='ambi_LtG00_Tbl_rTable4/01', point_name='ambi_LtG00_Tbl_rTable4/01', extra_name='', light_group=5, diffuse=[1, 1, 1], ambient=[0.141176, 0.141176, 0.141176], direction=[0, 0, 1], light_type='L_POINT', on=True, range=451, cutoff=180, theta=180, color=[214, 187, 133], attenuation=[0.0099999998, 0, 5.1500000954])
        preserve_entity(obj_ambi_LtG00_Tbl_rTable4_01, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [214, 187, 133], 'diffuse': [1, 1, 1], 'specular': [0, 0, 0], 'ambient': [0.141176, 0.141176, 0.141176], 'direction': [0, 0, 1], 'range': 451, 'cutoff': 180, 'type': 'L_POINT', 'theta': 180, 'atten': [0.0099999998, 0, 5.1500000954]}})
        obj_ambi_LtG00_Bar_Ovrhd01A = Light(root=self, name='ambi_LtG00_Bar_Ovrhd01A', point_name='ambi_LtG00_Bar_Ovrhd01A', extra_name='', light_group=5, diffuse=[0.596078, 0.572549, 0.403922], ambient=[0.223529, 0.2, 0.192157], direction=[0, 0, 1], light_type='L_POINT', on=True, range=15, cutoff=18, theta=15, color=[233, 208, 150], attenuation=[0.8999999762, 0, 0.0060000001])
        preserve_entity(obj_ambi_LtG00_Bar_Ovrhd01A, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [233, 208, 150], 'diffuse': [0.596078, 0.572549, 0.403922], 'specular': [0, 0, 0], 'ambient': [0.223529, 0.2, 0.192157], 'direction': [0, 0, 1], 'range': 15, 'cutoff': 18, 'type': 'L_POINT', 'theta': 15, 'atten': [0.8999999762, 0, 0.0060000001]}})
        obj_hatcher_bottle = Asset_obj_hatcher_bottle(root=self, name='hatcher_bottle', light_group=0, init_point='hatcher_bottle', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_hatcher_bottle, {'template_name': 'bottle_wine_3', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_hatcher_glass = Asset_obj_hatcher_glass(root=self, name='hatcher_glass', light_group=0, init_point='hatcher_glass', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_hatcher_glass, {'template_name': 'glass', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_trent_glass = Asset_obj_trent_glass(root=self, name='trent_glass', light_group=0, init_point='trent_glass', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_trent_glass, {'template_name': 'glass', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_DX_m05_offer_0200_trent = Sound(root=self, name='DX_m05_offer_0200_trent', sound='DX_m05_offer_0200_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m05_offer_0200_trent, {'template_name': 'DX_m05_offer_0200_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=5, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher = LookAtCamera(root=self, name='cam_hatcher', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_top = LookAtCamera(root=self, name='cam_hatcher_top', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_top = LookAtCamera(root=self, name='cam_trent_top', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_table = LookAtCamera(root=self, name='cam_hatcher_table', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_table, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_table = LookAtCamera(root=self, name='cam_table', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_table, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_reward = LookAtCamera(root=self, name='cam_hatcher_reward', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_reward, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 15, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=8, time_scale=0.7, start_time=0, loop=True, trans_time=None)
        # source event 16, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 17, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 18, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 10, 3s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 13, 5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=200, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 14, 7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_sit', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 19, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        main_group.append_time(7.5)

        # Line 10: source 7.5s; allocated facial window 4s.
        t = 0
        t += 0.6
        # source event 22, 8.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 23, 8.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.8
        # source event 11, 10s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=29, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 24, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TALK_000LV_A_16, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.25
        # source event 25, 10.25s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_top')
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_10', None)
        obj_Char_hatcher.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 20: source 10.5s; allocated facial window 8s.
        t = 0
        t += 7.0
        # source event 28, 17.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='hatcher_bottle', parent_name='Char_hatcher', duration=7, target_hardpoint='HpRightConnect_prop_bottle_wine_1', parent_hardpoint='HpRightConnect')
        # source event 29, 17.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='hatcher_glass', parent_name='Char_hatcher', duration=7, target_hardpoint='hpleftconnect_prop_glass_green', parent_hardpoint='hpleftconnect')
        # source event 32, 17.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_HOLDD_LEFT_000LV_00, duration=0.2, time_scale=10, start_time=0, loop=False, trans_time=0.25)
        # source event 33, 17.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 34, 17.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_GRABR_PRDRNK_TABL_000LV_XA_09, duration=8, time_scale=0.3, start_time=0.9, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.9)

        # Line 30: source 17.6s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_30', None)
        obj_Char_hatcher.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.6)

        # Line 40: source 23s; allocated facial window 8s.
        t = 0
        # source event 37, 23s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 38, 23s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 30, 25.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='hatcher_bottle', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 31, 25.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='hatcher_glass', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_40', None)
        obj_Char_trent.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 50: source 27s; allocated facial window 6s.
        t = 0
        # source event 41, 27s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_top')
        # source event 42, 27s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_50', None)
        obj_Char_hatcher.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 60: source 29s; allocated facial window 9.6s.
        t = 0
        t += 0.5
        # source event 48, 29.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_PUSH_DRINK_TABL_000LV_XA_05, duration=9, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 7.5
        # source event 49, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 51, 37s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_60', None)
        obj_Char_hatcher.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.6)

        # Line 70: source 38s; allocated facial window 8s.
        t = 0
        # source event 52, 38s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='trent_glass', parent_name='Char_trent', duration=10, target_hardpoint='hpleftconnect_prop_glass_green', parent_hardpoint='hpleftconnect')
        # source event 54, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_HOLDD_LEFT_000LV_00, duration=0.2, time_scale=10, start_time=0, loop=False, trans_time=0.25)
        t += 1.5
        # source event 50, 39.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_DRINK_LHND_SIP_000LV_XA_04, duration=7, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 55, 40.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=2, time_scale=0.2, start_time=0, loop=False, trans_time=0.25)
        t += 1.5
        # source event 62, 42s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=0.8, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 80: source 42.5s; allocated facial window 8.2s.
        t = 0
        # source event 58, 42.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        t += 0.5
        # source event 63, 43s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CONV_LHNDUP_TRNS_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 67, 44s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTL_CASL_000LV_00, duration=10, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        t += 0.8
        # source event 64, 44.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CONV_LHND_CASL_000LV_xa_03, duration=3, time_scale=0.5, start_time=0, loop=True, trans_time=1)
        t += 0.2
        # source event 12, 45s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2.8
        # source event 65, 47.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CONV_LHNDDN_TRNS_000LV_XA_01, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 0.2
        # source event 53, 48s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='trent_glass', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1.8
        # source event 66, 49.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_80', None)
        obj_Char_hatcher.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.7)

        # Line 90: source 50s; allocated facial window 5s.
        t = 0
        t += 3
        # source event 70, 53s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=0.1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 71, 54.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_top')
        # source event 72, 54.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_PUTDNL_DRINK_TABL_000LV_XA_06, duration=15, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        # source event 73, 54.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='trent_glass', parent_name='Char_trent', duration=3, target_hardpoint='hpleftconnect_prop_glass_green', parent_hardpoint='hpleftconnect')
        # source event 74, 54.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_HOLDD_LEFT_000LV_00, duration=0.2, time_scale=10, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_90', None)
        obj_Char_hatcher.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 100: source 55s; allocated facial window 8s.
        t = 0
        t += 2.7
        # source event 75, 57.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=6, time_scale=0.01, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_100', None)
        obj_Char_trent.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 110: source 61s; allocated facial window 9.6s.
        t = 0
        # source event 78, 61s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_table')
        # source event 79, 61s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CONV_LHNDUP_TRNS_000LV_XA_02, duration=2.6, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 2.6
        # source event 80, 63.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CONV_LHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 3.0
        # source event 81, 66.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_IDLE_000LV_XA_05, duration=3, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_110', None)
        obj_Char_hatcher.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.6)

        # Line 120: source 69s; allocated facial window 7.6s.
        t = 0
        t += 0.5
        # source event 85, 69.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 6.0
        # source event 89, 75.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 90, 75.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_LSTN_000UP_A_18, duration=6, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_120', None)
        obj_Char_hatcher.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.9)

        # Line 130: source 75.7s; allocated facial window 8s.
        t = 0
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_130', None)
        obj_Char_trent.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.7)

        # Line 140: source 81s; allocated facial window 13s.
        t = 0
        # source event 93, 81s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_top')
        # source event 94, 81s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_TALK_EMPH_000UP_A_10, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_140', None)
        obj_Char_hatcher.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.5
        # source event 99, 94.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_top')
        # source event 100, 94.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_LSTN_000UP_A_18, duration=55, time_scale=0.7, start_time=0, loop=True, trans_time=None)
        main_group.append_time(1)

        # Line 150: source 95s; allocated facial window 8s.
        t = 0
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_150', None)
        obj_Char_trent.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.5)

        # Line 160: source 98.5s; allocated facial window 11.5s.
        t = 0
        # source event 103, 98.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 104, 98.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TALK_000LV_A_08, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 10.0
        # source event 105, 108.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TALK_000UP_A_14, duration=15, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_160', None)
        obj_Char_hatcher.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 170: source 110s; allocated facial window 7.21s.
        t = 0
        # source event 111, 110s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_PUSH_DRINK_TABL_000LV_XA_05, duration=15, time_scale=1, start_time=1, loop=False, trans_time=1)
        t += 5
        # source event 112, 115s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=10, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 116, 115s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 117, 116s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_marker_card', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 118, 116s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_marker_card', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_170', None)
        obj_Char_hatcher.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.21)

        # Line 180: source 117s; allocated facial window 5s.
        t = 0
        # source event 121, 117s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 3
        # source event 119, 120s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 120, 120s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher_lower', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_180', None)
        obj_Char_trent.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 190: source 122s; allocated facial window 7.21s.
        t = 0
        # source event 124, 122s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 125, 122s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_reward')
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_190', None)
        obj_Char_hatcher.facial(group=MAIN, index=190, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.21)
        restore_dialogue(self)
