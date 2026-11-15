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


class ReconstructedScene(Scene):
    DUMP_FILE = 'm04_hatcher'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_ambi_LtG00_Bar_Ovrhd01A = Light(root=self, name='ambi_LtG00_Bar_Ovrhd01A', point_name='ambi_LtG00_Bar_Ovrhd01A', extra_name='', light_group=5, diffuse=[0.596078, 0.572549, 0.403922], ambient=[0.223529, 0.2, 0.192157], direction=[0, 0, 1], light_type='L_POINT', on=True, range=15, cutoff=18, theta=15, color=[233, 208, 150], attenuation=[0.8999999762, 0, 0.0060000001])
        preserve_entity(obj_ambi_LtG00_Bar_Ovrhd01A, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [233, 208, 150], 'diffuse': [0.596078, 0.572549, 0.403922], 'specular': [0, 0, 0], 'ambient': [0.223529, 0.2, 0.192157], 'direction': [0, 0, 1], 'range': 15, 'cutoff': 18, 'type': 'L_POINT', 'theta': 15, 'atten': [0.8999999762, 0, 0.0060000001]}})
        obj_ambi_LtG00_Bar_Ovrhd01B = Light(root=self, name='ambi_LtG00_Bar_Ovrhd01B', point_name='ambi_LtG00_Bar_Ovrhd01B', extra_name='', light_group=5, diffuse=[0.596078, 0.572549, 0.403922], ambient=[0, 0, 0], direction=[0, 0, 1], light_type='L_POINT', on=True, range=5, cutoff=18, theta=15, color=[233, 208, 150], attenuation=[0.8999999762, 0, 0.0060000001])
        preserve_entity(obj_ambi_LtG00_Bar_Ovrhd01B, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [233, 208, 150], 'diffuse': [0.596078, 0.572549, 0.403922], 'specular': [0, 0, 0], 'ambient': [0, 0, 0], 'direction': [0, 0, 1], 'range': 5, 'cutoff': 18, 'type': 'L_POINT', 'theta': 15, 'atten': [0.8999999762, 0, 0.0060000001]}})
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=5, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_alaric, {'template_name': 'alaric', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Alaric', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_firstlook = LookAtCamera(root=self, name='cam_hatcher_firstlook', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_firstlook, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_people_arrive = LookAtCamera(root=self, name='cam_hatcher_people_arrive', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_people_arrive, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_near = LookAtCamera(root=self, name='cam_hatcher_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric = LookAtCamera(root=self, name='cam_alaric', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_alaric, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_alaric_near = LookAtCamera(root=self, name='cam_alaric_near', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_alaric_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_final = LookAtCamera(root=self, name='cam_hatcher_final', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 10, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['wlkg_trent_front', 'Char_trent'], duration=35, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 11, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_alaric', 'Char_alaric'], duration=200, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 12, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_wlkg_alaric_front_near', 'Char_alaric'], duration=200, offset=[0.75, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION')
        # source event 13, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 22, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=6.91, time_scale=0.75, start_time=0, loop=True, trans_time=None)
        # source event 26, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=6.91, time_scale=0.75, start_time=0.2, loop=True, trans_time=None)
        # source event 31, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STLB_000LV_A_21, duration=16, time_scale=0.75, start_time=2, loop=False, trans_time=None)
        # source event 34, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 6.91
        # source event 23, 6.91s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=None)
        # source event 27, 6.91s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=3, time_scale=0.75, start_time=0.22, loop=False, trans_time=0.2)
        t += 1.09
        # source event 15, 8s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 16, 8s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 17, 8s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_head_ik', duration=10, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.5
        # source event 18, 9.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_wlkg_alaric_front_near', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 24, 9.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_POINT_RHND_000LV_A_03, duration=5, time_scale=0.75, start_time=0, loop=False, trans_time=0.5)
        # source event 25, 9.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.GENERIC_ANIM, duration=6, start_time=0, time_scale=1, trans_time=0.25)
        t += 0.5
        # source event 20, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_marker_hatcher_sitpoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 28, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 19, 13s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_trent_front_exitpoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 36, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_firstlook', target_name='automarker_cam_hatcher_firstlook_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 37, 14s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_firstlook')
        t += 1
        # source event 21, 15s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_alaric_front_exitpoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 30, 16s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 32, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STLB_LSTN_270LV_C_07, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 29, 17s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=4, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 5
        # source event 33, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STLB_STDSL_TRNS_225LV_A_03, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 38, 22s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_people_arrive')
        # source event 39, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_wayforward', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 40, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='automarker_point_alaric_wayforward', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 41, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STLB_STDSL_TRNS_225LV_A_03, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 42, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.25, time_scale=0.75, start_time=0, loop=True, trans_time=None)
        # source event 45, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.25, time_scale=0.75, start_time=0, loop=True, trans_time=None)
        # source event 48, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 49, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 50, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_head_ik', target_name='automarker_head_hatcher', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 51, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_alaric_eye_ik', target_name='automarker_head_hatcher', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 56, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_front', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 57, 23s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_front', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 58, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_near', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 59, 24s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 62, 24s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 63, 24s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=90, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 52, 24.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=67.5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 53, 24.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_head_ik', duration=67.5, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(25)

        # Line 10: source 25s; allocated facial window 2.8s.
        t = 0
        t += 0.25
        # source event 43, 25.25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_TURN_180LV_XA_04, duration=1, time_scale=1, start_time=0.75, loop=False, trans_time=1)
        # source event 46, 25.25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=1.25, time_scale=1, start_time=0.75, loop=False, trans_time=1)
        t += 1.0
        # source event 44, 26.25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=30, time_scale=0.7, start_time=0, loop=False, trans_time=2)
        t += 0.25
        # source event 47, 26.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10, time_scale=0.7, start_time=2, loop=False, trans_time=2)
        # source event 54, 26.5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=60, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 55, 26.5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_alaric', target_name='automarker_alaric_eye_ik', duration=60, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 70, 26.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_alaric_focus', target_name='automarker_cam_alaric_marker_pos2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 71, 26.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric')
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_10', None)
        obj_Char_hatcher.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.1)

        # Line 20: source 26.7s; allocated facial window 5.8s.
        t = 0
        t += 1.1
        # source event 66, 27.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_alaric_near', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 67, 27.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_20', None)
        obj_Char_trent.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.5)

        # Line 30: source 28s; allocated facial window 7.5s.
        t = 0
        t += 2
        # source event 60, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 61, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 68, 31s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 69, 31s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_30', None)
        obj_Char_alaric.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 40: source 32s; allocated facial window 6s.
        t = 0
        # source event 77, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 78, 32s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 79, 32s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TALK_000LV_B_10, duration=17, time_scale=0.5, start_time=0, loop=True, trans_time=None)
        # source event 80, 32s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_people_arrive')
        t += 3.5
        # source event 83, 35.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_near', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 84, 35.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_40', None)
        obj_Char_hatcher.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 45: source 36s; allocated facial window 6.5s.
        t = 0
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_45', None)
        obj_Char_hatcher.facial(group=MAIN, index=45, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 50: source 39s; allocated facial window 6.4s.
        t = 0
        t += 1
        # source event 85, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 86, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_50', None)
        obj_Char_hatcher.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.4)

        # Line 55: source 44s; allocated facial window 3.1s.
        t = 0
        # source event 87, 44s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.8
        # source event 88, 45.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_55', None)
        obj_Char_hatcher.facial(group=MAIN, index=55, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.1
        # source event 97, 47.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 1.3
        # source event 98, 48.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        main_group.append_time(1.5)

        # Line 60: source 48.6s; allocated facial window 5.9s.
        t = 0
        t += 1.9
        # source event 107, 50.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_people_arrive', target_name='automarker_cam_hatcher_people_arrive_pos2', duration=14.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 108, 50.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_people_arrive')
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_60', None)
        obj_Char_trent.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 70: source 51s; allocated facial window 12.6s.
        t = 0
        t += 1.5
        # source event 101, 52.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 7.0
        # source event 102, 59.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 103, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_alaric_near', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 104, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_alaric', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 105, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 106, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_70', None)
        obj_Char_hatcher.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(1.4)

        # Line 80: source 65s; allocated facial window 6s.
        t = 0
        # source event 114, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_alaric_near', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 115, 65s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_alaric', duration=0.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 118, 65s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_alaric_near')
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_80', None)
        obj_Char_alaric.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 90: source 67s; allocated facial window 10s.
        t = 0
        # source event 121, 67s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        t += 0.5
        # source event 116, 67.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 117, 67.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 5.5
        # source event 126, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 127, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 100: source 74s; allocated facial window 8.5s.
        t = 0
        # source event 128, 74s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_near')
        # source event 129, 74s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_100', None)
        obj_Char_hatcher.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 110: source 80s; allocated facial window 10s.
        t = 0
        # source event 133, 80s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_110', None)
        obj_Char_trent.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 120: source 88.5s; allocated facial window 6s.
        t = 0
        # source event 138, 88.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_near', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 139, 88.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_near')
        # source event 140, 88.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 143, 91s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        # source event 148, 91s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=2)
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_120', None)
        obj_Char_hatcher.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.25)

        # Line 130: source 91.25s; allocated facial window 1.75s.
        t = 0
        select_dialogue(self, 4, 'Msn4Reward', 'm04_reward')
        self.groups.pop('motion_130', None)
        obj_Char_trent.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 146, 93s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=6, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        # source event 147, 93s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=2)
        t += 1.0
        # source event 152, 94s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_front', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 153, 94s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_front', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 151, 95s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_final')
        # source event 154, 95s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_marker_bar_exitpoint', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 155, 95s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_marker_bar_exitpoint', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.001
        # source event 149, 95.001s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 150, 95.001s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.499
        # source event 157, 95.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', angle=-45, axis='Y_AXIS', duration=2, smooth=True)
        t += 1.5
        # source event 156, 97s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        main_group.append_time(7.0)
        restore_dialogue(self)
