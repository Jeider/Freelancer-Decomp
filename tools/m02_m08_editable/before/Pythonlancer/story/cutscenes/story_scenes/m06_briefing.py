"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_scene_obj_01(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_free_flow_ion_drive'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_02(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_03(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_04(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_05(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_06(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_free_flow_ion_drive'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_07(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_08(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_09(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_obj_10(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_li_fusion_reactor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_monitor_projector(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_ge_nano_weavers1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_scene_cloaking_device(Equipment):
    COMPOUND_TEMPLATE_NAME = 'rtcprop_hardware_co_stealth2'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_infopanel_shipyard_view(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_infopanel05'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_infopanel_shipyard_ships(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_infopanel04'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_infopanel_stealth_connection(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_infopanel06'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_ship_monitor(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_fiber_struts_sml'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_infopanel_monitor(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_monitor'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_sphere_map(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_sphere_map_1_5x'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_glasses(Prop):
    COMPOUND_TEMPLATE_NAME = 'new_fem_glasses'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_briefing'
    SCENE_AMBIENT = [55, 55, 55]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_scene_obj_01 = Asset_obj_scene_obj_01(root=self, name='scene_obj_01', light_group=3, init_point='scene_obj_01', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_01, {'template_name': 'rtcprop_hardware_li_free_flow_ion_drive', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_02 = Asset_obj_scene_obj_02(root=self, name='scene_obj_02', light_group=3, init_point='scene_obj_02', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_02, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_03 = Asset_obj_scene_obj_03(root=self, name='scene_obj_03', light_group=3, init_point='scene_obj_03', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_03, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_04 = Asset_obj_scene_obj_04(root=self, name='scene_obj_04', light_group=3, init_point='scene_obj_04', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_04, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_05 = Asset_obj_scene_obj_05(root=self, name='scene_obj_05', light_group=3, init_point='scene_obj_05', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_05, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_06 = Asset_obj_scene_obj_06(root=self, name='scene_obj_06', light_group=3, init_point='scene_obj_06', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_06, {'template_name': 'rtcprop_hardware_li_free_flow_ion_drive', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_07 = Asset_obj_scene_obj_07(root=self, name='scene_obj_07', light_group=3, init_point='scene_obj_07', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_07, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_08 = Asset_obj_scene_obj_08(root=self, name='scene_obj_08', light_group=3, init_point='scene_obj_08', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_08, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_09 = Asset_obj_scene_obj_09(root=self, name='scene_obj_09', light_group=3, init_point='scene_obj_09', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_09, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_obj_10 = Asset_obj_scene_obj_10(root=self, name='scene_obj_10', light_group=3, init_point='scene_obj_10', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_obj_10, {'template_name': 'rtcprop_hardware_li_fusion_reactor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_monitor_projector = Asset_obj_scene_monitor_projector(root=self, name='scene_monitor_projector', light_group=3, init_point='scene_monitor_projector', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_monitor_projector, {'template_name': 'rtcprop_hardware_ge_nano_weavers1', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_scene_cloaking_device = Asset_obj_scene_cloaking_device(root=self, name='scene_cloaking_device', light_group=3, init_point='scene_cloaking_device', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_scene_cloaking_device, {'template_name': 'rtcprop_hardware_co_stealth2', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Equipment'}})
        obj_infopanel_shipyard_view = Asset_obj_infopanel_shipyard_view(root=self, name='infopanel_shipyard_view', light_group=3, init_point='infopanel_shipyard_view', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_infopanel_shipyard_view, {'template_name': 'm6_infopanel05', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_infopanel_shipyard_ships = Asset_obj_infopanel_shipyard_ships(root=self, name='infopanel_shipyard_ships', light_group=3, init_point='infopanel_shipyard_ships', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_infopanel_shipyard_ships, {'template_name': 'm6_infopanel04', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_infopanel_stealth_connection = Asset_obj_infopanel_stealth_connection(root=self, name='infopanel_stealth_connection', light_group=3, init_point='infopanel_stealth_connection', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_infopanel_stealth_connection, {'template_name': 'm6_infopanel06', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_ship_monitor = Asset_obj_ship_monitor(root=self, name='ship_monitor', light_group=3, init_point='ship_monitor', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_ship_monitor, {'template_name': 'm6_fiber_struts_sml', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_infopanel_monitor = Asset_obj_infopanel_monitor(root=self, name='infopanel_monitor', light_group=3, init_point='infopanel_monitor', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_infopanel_monitor, {'template_name': 'm6_monitor', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_sphere_map = Asset_obj_sphere_map(root=self, name='sphere_map', light_group=3, init_point='sphere_map', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_sphere_map, {'template_name': 'm6_sphere_map_1_5x', 'lt_grp': 3, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=-13)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': -13}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True, use_ambient=True, floor_height=-13)
        preserve_entity(obj_Char_alaric, {'template_name': 'alaric', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': -13}, 'userprops': {'actor': 'Alaric', 'category': 'Character'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=0, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=True, floor_height=-13)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher_glassless', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': -13}, 'userprops': {'actor': 'Hatcher_noglass', 'category': 'Character'}})
        obj_prop_glasses = Asset_obj_prop_glasses(root=self, name='prop_glasses', light_group=0, init_point='prop_glasses', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_prop_glasses, {'template_name': 'new_fem_glasses', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=25, farplane=5000, look_duration=30)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=22, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric = LookAtCamera(root=self, name='cam_alaric', fov=20, farplane=5000, look_duration=30)
        preserve_entity(obj_cam_alaric, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher = LookAtCamera(root=self, name='cam_hatcher', fov=25, farplane=5000, look_duration=250)
        preserve_entity(obj_cam_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_stealth = LookAtCamera(root=self, name='cam_stealth', fov=28, farplane=5000, look_duration=150)
        preserve_entity(obj_cam_stealth, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 28, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 6, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 7, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 8, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 9, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=8, time_scale=0.7, start_time=0.73, loop=True, trans_time=None)
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=7.5, time_scale=0.7, start_time=0.53, loop=True, trans_time=None)
        # source event 11, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_glasses', parent_name='Char_hatcher', duration=12, target_hardpoint='hp_eyewear', parent_hardpoint='hp_eyewear')
        # source event 12, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_03, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 4
        # source event 13, 4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        main_group.append_time(4.8)

        # Line 10: source 4.8s; allocated facial window 7s.
        t = 0
        t += 0.2
        # source event 14, 5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=13, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 15, 5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=13, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 3.0
        # source event 16, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 17, 8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.2
        # source event 21, 10.2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_stand', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 23, 10.2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='automarker_point_alaric_stand', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 22, 10.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_XB_04, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 24, 10.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_IDLE_000LV_XB_04, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.2
        # source event 27, 10.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_head_ik', duration=250, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 28, 10.5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_eye_ik', duration=250, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_10', None)
        obj_Char_hatcher.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.8)

        # Line 20: source 11s; allocated facial window 15s.
        t = 0
        # source event 29, 11s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 1.5
        # source event 32, 12.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 33, 12.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-13)

        # Line 30: source 13s; allocated facial window 8s.
        t = 0
        # source event 34, 13s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 35, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 48, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        # source event 49, 13s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_PROBE_RGHT_000LV_00, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 50, 13s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_glasses', parent_name='Char_hatcher', duration=6.1399, target_hardpoint='hp_eyewear', parent_hardpoint='hp_eyewear')
        t += 5
        # source event 51, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_SALUT_000LV_XA_03, duration=2, time_scale=1, start_time=1, loop=False, trans_time=1)
        t += 1
        # source event 44, 19s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=551, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 45, 19s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=551, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 46, 19s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_point_glass_clean_middle', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 47, 19s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_point_glass_clean', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 52, 19s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_glass_connect_marker', 'Char_hatcher'], duration=10, offset=[0.05, 0.05, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='HpRightGlassTouch', target_type='HARDPOINT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 53, 19s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_glass_connect_marker_second', 'automarker_glass_connect_marker'], duration=10, offset=[0, 0, -0.015], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE+ORIENTATION_RELATIVE')
        t += 0.15
        # source event 54, 19.15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_glasses', target_name='automarker_glass_connect_marker_second', duration=0.1, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 55, 19.25s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_glasses', parent_name='Char_hatcher', duration=5.199, target_hardpoint='HpRightTouch', parent_hardpoint='HpRightGlassTouch')
        t += 0.75
        # source event 25, 20s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 26, 20s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=55, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 56, 20s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_MED_000LV_xa_05, duration=3.5, time_scale=1, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_30', None)
        obj_Char_hatcher.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 40: source 21s; allocated facial window 6s.
        t = 0
        t += 1
        # source event 62, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 63, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 57, 23.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_SALUT_000LV_XA_03, duration=5, time_scale=1, start_time=1, loop=False, trans_time=1)
        t += 0.5
        # source event 58, 24s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_glass_head_connect_marker', 'Char_hatcher'], duration=5, offset=[0, -0.01, -0.08], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hp_eyewear', target_type='HARDPOINT', flags='POSITION+ENTITY_RELATIVE')
        # source event 59, 24s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_glass_head_connect_marker_second', 'automarker_glass_head_connect_marker'], duration=5, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE+ORIENTATION_RELATIVE')
        # source event 64, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 65, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 76, 24s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_CONCNTRTE_000LV_XA_, duration=0.5, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 0.45
        # source event 60, 24.45s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='prop_glasses', target_name='automarker_glass_head_connect_marker_second', duration=0.4, smooth=False, adjust_pos=True, adjust_orient=False)
        t += 0.4
        # source event 61, 24.85s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_glasses', parent_name='Char_hatcher', duration=351, target_hardpoint='hp_eyewear', parent_hardpoint='hp_eyewear')
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_40', None)
        obj_Char_hatcher.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 50: source 25s; allocated facial window 11s.
        t = 0
        # source event 36, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_pos3', duration=20, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_marker_pos3', duration=20, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 82, 25.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TALK_EMPH_000LV_A_04, duration=7.5, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 1.5
        # source event 66, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 67, 27s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.35, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4
        # source event 68, 31s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 69, 31s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.35, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 83, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 2
        # source event 84, 34s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=4, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        t += 1
        # source event 70, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 71, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.35, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_50', None)
        obj_Char_hatcher.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 60: source 35.5s; allocated facial window 15s.
        t = 0
        t += 2.5
        # source event 85, 38s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 2.0
        # source event 72, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 73, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.35, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_60', None)
        obj_Char_hatcher.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.0)

        # Line 70: source 41.5s; allocated facial window 6.5s.
        t = 0
        t += 0.3
        # source event 86, 41.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 1.2
        # source event 74, 43s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 75, 43s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_70', None)
        obj_Char_hatcher.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 80: source 46s; allocated facial window 12s.
        t = 0
        # source event 92, 46s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        # source event 95, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_trent_alaric_middle', duration=3.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 96, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 102, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 1.5
        # source event 97, 48.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_trent_alaric_middle', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 98, 48.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_80', None)
        obj_Char_alaric.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.5)

        # Line 90: source 49.5s; allocated facial window 15s.
        t = 0
        # source event 99, 49.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-13.0)

        # Line 100: source 51.5s; allocated facial window 7s.
        t = 0
        # source event 105, 51.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 109, 51.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_MED_000LV_xa_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=2)
        t += 0.5
        # source event 103, 52s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 104, 52s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.35, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_100', None)
        obj_Char_hatcher.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 110: source 56.5s; allocated facial window 12.8s.
        t = 0
        # source event 110, 56.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_trent_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 111, 56.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_trent_front', duration=1.3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 112, 56.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 113, 56.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent', target_name='automarker_cam_trent_pos2', duration=13, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 118, 56.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_GESTR_THMBSUP_000LV_XA_02, duration=4, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 4.0
        # source event 119, 60.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 2.0
        # source event 120, 62.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HOLD_000LV_XA_02, duration=3, time_scale=0.7, start_time=0, loop=True, trans_time=0.5)
        t += 6.5
        # source event 121, 69s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 122, 69s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 146, 69s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_monitor', target_name='automarker_monitor_start_point', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_110', None)
        obj_Char_trent.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.2)

        # Line 120: source 69.5s; allocated facial window 12s.
        t = 0
        # source event 139, 69.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        t += 0.5
        # source event 147, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_monitor', target_name='automarker_monitor_viewpoint', duration=10, smooth=True, adjust_pos=True, adjust_orient=False)
        t += 0.5
        # source event 140, 70.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_brief_pos1', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 141, 70.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_brief_marker_pos1', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.5
        # source event 123, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 124, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 6.0
        # source event 125, 79s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 126, 79s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_120', None)
        obj_Char_hatcher.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 130: source 80.5s; allocated facial window 19.5s.
        t = 0
        # source event 148, 80.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_shipyard_view', target_name='automarker_monitor_viewpoint', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        # source event 154, 80.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        t += 2.0
        # source event 155, 82.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=6, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 2.5
        # source event 127, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 128, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 158, 86.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_NEUT_RGHT_000LV_A_00, duration=2, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 2.0
        # source event 156, 88.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 1.0
        # source event 157, 89.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=6, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 1.5
        # source event 129, 91s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 130, 91s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_130', None)
        obj_Char_hatcher.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 140: source 96.5s; allocated facial window 13.5s.
        t = 0
        t += 0.5
        # source event 163, 97s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=0.5)
        # source event 169, 97s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_shipyard_view', target_name='offscreen', duration=1e-05, smooth=False, adjust_pos=True, adjust_orient=False)
        t += 1e-05
        # source event 170, 97s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_stealth_connection', target_name='automarker_monitor_viewpoint', duration=1e-06, smooth=False, adjust_pos=True, adjust_orient=False)
        t += 2.99999
        # source event 164, 100s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=4, time_scale=0.6, start_time=0, loop=True, trans_time=0.5)
        t += 5.0
        # source event 131, 105s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 132, 105s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 165, 106s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_140', None)
        obj_Char_hatcher.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 167, 110s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_stealth')
        # source event 168, 110s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_stealth', target_name='automarker_cam_stealth_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(0.5)

        # Line 150: source 110.5s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        voice_sound = self.lookup_single_sound(150)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        t += 0.5
        # source event 133, 111s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 134, 111s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4.0
        # source event 181, 115s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_stealth_connection', target_name='offscreen', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        t += 0.01
        # source event 182, 115.01s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='ship_monitor', target_name='automarker_monitor_viewpoint', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        main_group.append_time(7.5)

        # Line 160: source 118s; allocated facial window 13.5s.
        t = 0
        # source event 171, 118s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 172, 118s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_brief_pos2', duration=25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 173, 118s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_brief_marker_pos2', duration=25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 178, 119.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=3.6, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 3.6
        # source event 179, 123.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_03, duration=3.4, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 1.9
        # source event 135, 125s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 136, 125s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 180, 126.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=8, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_160', None)
        obj_Char_hatcher.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 170: source 131s; allocated facial window 13.5s.
        t = 0
        # source event 137, 131s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 138, 131s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 187, 131.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 190, 131.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 2.0
        # source event 188, 133.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=3, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 3.0
        # source event 189, 136.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_170', None)
        obj_Char_hatcher.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.0)

        # Line 180: source 139.5s; allocated facial window 13.5s.
        t = 0
        t += 0.5
        # source event 195, 140s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=0.5)
        t += 3.0
        # source event 196, 143s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=4, time_scale=0.6, start_time=0, loop=True, trans_time=0.5)
        t += 3.0
        # source event 200, 146s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_180', None)
        obj_Char_hatcher.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.0)

        # Line 190: source 148s; allocated facial window 15s.
        t = 0
        # source event 197, 148s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_190', None)
        obj_Char_trent.facial(group=MAIN, index=190, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-12.5)

        # Line 200: source 150.5s; allocated facial window 5s.
        t = 0
        # source event 201, 150.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 202, 150.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_brief_pos3', duration=25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 203, 150.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_brief_marker_pos1', duration=25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 212, 150.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 215, 150.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 3.5
        # source event 204, 154s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 205, 154s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_200', None)
        obj_Char_hatcher.facial(group=MAIN, index=200, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 210: source 156s; allocated facial window 15s.
        t = 0
        t += 0.5
        # source event 220, 156.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=3.6, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 3.5
        # source event 206, 160s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 207, 160s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 221, 160.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_03, duration=6.4, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 6.4
        # source event 222, 166.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=8, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_210', None)
        obj_Char_hatcher.facial(group=MAIN, index=210, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 220: source 170s; allocated facial window 15.5s.
        t = 0
        t += 0.5
        # source event 228, 170.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 231, 170.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 2.0
        # source event 229, 172.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=3, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 1.5
        # source event 208, 174s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 209, 174s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 230, 175.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=1, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 4.5
        # source event 210, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 211, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 232, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_hatcher', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 233, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_hatcher', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 5
        # source event 238, 185s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_220', None)
        obj_Char_hatcher.facial(group=MAIN, index=220, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 230: source 186s; allocated facial window 14.5s.
        t = 0
        # source event 234, 186s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_230', None)
        obj_Char_alaric.facial(group=MAIN, index=230, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-9.5)

        # Line 240: source 191s; allocated facial window 16s.
        t = 0
        # source event 239, 191s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 240, 191s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=0.9, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 243, 191s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        t += 0.5
        # source event 249, 191.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        t += 2.5
        # source event 250, 194s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=3, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 3
        # source event 241, 197s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 242, 197s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 251, 197s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=3, time_scale=0.6, start_time=0, loop=False, trans_time=0.5)
        t += 8
        # source event 252, 205s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='ship_monitor', target_name='offscreen', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        # source event 253, 205s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_monitor', target_name='automarker_monitor_start_point', duration=10, smooth=True, adjust_pos=True, adjust_orient=False)
        t += 1
        # source event 262, 206s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_240', None)
        obj_Char_hatcher.facial(group=MAIN, index=240, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 250: source 207s; allocated facial window 5s.
        t = 0
        # source event 255, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_brief_pos4', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 256, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_brief_marker_pos4', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 257, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='sphere_map', target_name='automarker_sphere_projector_viewpoint', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        t += 0.001
        # source event 258, 207.001s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='sphere_map', angle=-360, axis='Y_AXIS', duration=19, smooth=False)
        t += 0.999
        # source event 263, 208s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=3, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 3
        # source event 264, 211s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=2, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_250', None)
        obj_Char_hatcher.facial(group=MAIN, index=250, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 265, 212s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_sphere_projector_viewpoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 266, 212s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_sphere_projector_viewpoint', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(1)

        # Line 260: source 213s; allocated facial window 12s.
        t = 0
        # source event 267, 213s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        t += 3
        # source event 254, 216s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='infopanel_monitor', target_name='automarker_monitor_start_point', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_260', None)
        obj_Char_alaric.facial(group=MAIN, index=260, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8)

        # Line 270: source 217s; allocated facial window 10s.
        t = 0
        # source event 270, 217s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 271, 217s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 282, 217s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        t += 8
        # source event 272, 225s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 273, 225s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_270', None)
        obj_Char_hatcher.facial(group=MAIN, index=270, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 280: source 226s; allocated facial window 14.5s.
        t = 0
        # source event 286, 226s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_final_pos1', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 287, 226s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_final_marker_pos1', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 259, 226.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='sphere_map', target_name='offscreen', duration=0.01, smooth=False, adjust_pos=True, adjust_orient=False)
        t += 2.9
        # source event 274, 229s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 275, 229s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4
        # source event 276, 233s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 277, 233s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4
        # source event 292, 237s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_280', None)
        obj_Char_hatcher.facial(group=MAIN, index=280, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 290: source 239s; allocated facial window 7s.
        t = 0
        # source event 278, 239s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 279, 239s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 293, 239s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_final_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 294, 239s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_focus', target_name='automarker_cam_hatcher_final_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 280, 241s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 281, 241s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Briefieng', 'm06_briefing')
        self.groups.pop('motion_290', None)
        obj_Char_hatcher.facial(group=MAIN, index=290, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.0)
        preserve_spatial(self.get_entity('scene_obj_01'), source_basis=[[2, 0, 0], [0, 2, 0], [0, 0, 2]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_02'), source_basis=[[2, 0, 0], [0, 2, 0], [0, 0, 2]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_03'), source_basis=[[2, 0, 0], [0, 2, 0], [0, 0, 2]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_04'), source_basis=[[2, 0, 0], [0, 2, 0], [0, 0, 2]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_05'), source_basis=[[2, 0, 0], [0, 2, 0], [0, 0, 2]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_06'), source_basis=[[-2, 0, 0], [0, 2, 0], [0, 0, -2]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_07'), source_basis=[[-2, 0, 0], [0, 2, 0], [0, 0, -2]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_08'), source_basis=[[-2, 0, 0], [0, 2, 0], [0, 0, -2]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_09'), source_basis=[[-2, 0, 0], [0, 2, 0], [0, 0, -2]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        preserve_spatial(self.get_entity('scene_obj_10'), source_basis=[[-2, 0, 0], [0, 2, 0], [0, 0, -2]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        preserve_spatial(self.get_entity('scene_monitor_projector'), source_basis=[[-0.8, 0, 0], [0, 0.8, 0], [0, 0, -0.8]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        preserve_spatial(self.get_entity('scene_cloaking_device'), source_basis=[[-1.5, 0, 0], [0, 1.5, 0], [0, 0, -1.5]], reference_orientation=[0.0, -0.0, 1.0, -0.0])
        restore_dialogue(self)
