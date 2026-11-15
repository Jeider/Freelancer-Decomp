"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_offer_accept'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_ambi_LtG00_Tbl_rTable4_01 = Light(root=self, name='ambi_LtG00_Tbl_rTable4/01', point_name='ambi_LtG00_Tbl_rTable4/01', extra_name='', light_group=5, diffuse=[1, 1, 1], ambient=[0.141176, 0.141176, 0.141176], direction=[0, 0, 1], light_type='L_POINT', on=True, range=451, cutoff=180, theta=180, color=[214, 187, 133], attenuation=[0.0099999998, 0, 5.1500000954])
        preserve_entity(obj_ambi_LtG00_Tbl_rTable4_01, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [214, 187, 133], 'diffuse': [1, 1, 1], 'specular': [0, 0, 0], 'ambient': [0.141176, 0.141176, 0.141176], 'direction': [0, 0, 1], 'range': 451, 'cutoff': 180, 'type': 'L_POINT', 'theta': 180, 'atten': [0.0099999998, 0, 5.1500000954]}})
        obj_ambi_LtG00_Bar_Ovrhd01A = Light(root=self, name='ambi_LtG00_Bar_Ovrhd01A', point_name='ambi_LtG00_Bar_Ovrhd01A', extra_name='', light_group=5, diffuse=[0.596078, 0.572549, 0.403922], ambient=[0.223529, 0.2, 0.192157], direction=[0, 0, 1], light_type='L_POINT', on=True, range=15, cutoff=18, theta=15, color=[233, 208, 150], attenuation=[0.8999999762, 0, 0.0060000001])
        preserve_entity(obj_ambi_LtG00_Bar_Ovrhd01A, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [233, 208, 150], 'diffuse': [0.596078, 0.572549, 0.403922], 'specular': [0, 0, 0], 'ambient': [0.223529, 0.2, 0.192157], 'direction': [0, 0, 1], 'range': 15, 'cutoff': 18, 'type': 'L_POINT', 'theta': 15, 'atten': [0.8999999762, 0, 0.0060000001]}})
        obj_DX_m05_offer_0180_trent = Sound(root=self, name='DX_m05_offer_0180_trent', sound='DX_m05_offer_0180_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m05_offer_0180_trent, {'template_name': 'DX_m05_offer_0180_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m05_offer_0190_hatcher = Sound(root=self, name='DX_m05_offer_0190_hatcher', sound='DX_m05_offer_0190_hatcher', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m05_offer_0190_hatcher, {'template_name': 'DX_m05_offer_0190_hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=5, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_cam_start = StaticCamera(root=self, name='cam_start', fov=25, farplane=5000)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher = LookAtCamera(root=self, name='cam_hatcher', fov=15, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = StaticCamera(root=self, name='cam_trent', fov=25, farplane=5000)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_top = StaticCamera(root=self, name='cam_hatcher_top', fov=20, farplane=5000)
        preserve_entity(obj_cam_hatcher_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_top = LookAtCamera(root=self, name='cam_trent_top', fov=22, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_table = StaticCamera(root=self, name='cam_hatcher_table', fov=25, farplane=5000)
        preserve_entity(obj_cam_hatcher_table, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_table = StaticCamera(root=self, name='cam_table', fov=22, farplane=5000)
        preserve_entity(obj_cam_table, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_reward = StaticCamera(root=self, name='cam_hatcher_reward', fov=20, farplane=5000)
        preserve_entity(obj_cam_hatcher_reward, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_top')
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=2, time_scale=0.7, start_time=0, loop=True, trans_time=None)
        main_group.append_time(0.5)

        # Line 200: source 0.5s; allocated facial window 5s.
        t = 0
        t += 1.5
        # source event 6, 2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_WALK_TRNS_090LV_XA_10, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_200', None)
        obj_Char_trent.facial(group=MAIN, index=200, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 1.5
        # source event 8, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 9, 7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher', target_name='automarker_cam_hatcher_pos2', duration=17, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 10, 7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_TWSTS_FROM_270LV_XA_02, duration=3, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 1.1
        # source event 7, 8.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1.9
        # source event 11, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_GRABR_HEAD_RLEASE_000LV_XA_03, duration=2, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        main_group.append_time(5.5)

        # Line 210: source 11s; allocated facial window 11.8s.
        t = 0
        # source event 15, 11s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_FIST_000LV_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 1
        # source event 12, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_HEAD_HOLDR_000LV_XA_02, duration=4, time_scale=0.8, start_time=0, loop=True, trans_time=1)
        t += 4
        # source event 13, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_HOLD_HEAD_RLEASE_000LV_XA_03, duration=3, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 16, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 2
        # source event 14, 19s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRF_TWSTS_LOOK_270LV_XA_02, duration=3, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Offer', 'm05_offer')
        self.groups.pop('motion_210', None)
        obj_Char_hatcher.facial(group=MAIN, index=210, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(1.2)
        restore_dialogue(self)
