"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm08_offer'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_DX_m08_offer_0440_trent = Sound(root=self, name='DX_m08_offer_0440_trent', sound='DX_m08_offer_0440_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_offer_0440_trent, {'template_name': 'DX_m08_offer_0440_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_offer_0450_kaitlyn = Sound(root=self, name='DX_m08_offer_0450_kaitlyn', sound='DX_m08_offer_0450_kaitlyn', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_offer_0450_kaitlyn, {'template_name': 'DX_m08_offer_0450_kaitlyn', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_offer_0460_kaitlyn = Sound(root=self, name='DX_m08_offer_0460_kaitlyn', sound='DX_m08_offer_0460_kaitlyn', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_offer_0460_kaitlyn, {'template_name': 'DX_m08_offer_0460_kaitlyn', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_offer_0470_brighton = Sound(root=self, name='DX_m08_offer_0470_brighton', sound='DX_m08_offer_0470_brighton', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_offer_0470_brighton, {'template_name': 'DX_m08_offer_0470_brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_offer_0480_darcy = Sound(root=self, name='DX_m08_offer_0480_darcy', sound='DX_m08_offer_0480_darcy', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_offer_0480_darcy, {'template_name': 'DX_m08_offer_0480_darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_bship_wales_0010_brighton = Sound(root=self, name='DX_m08_bship_wales_0010_brighton', sound='DX_m08_bship_wales_0010_brighton', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_bship_wales_0010_brighton, {'template_name': 'DX_m08_bship_wales_0010_brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_bship_wales_0020_brighton = Sound(root=self, name='DX_m08_bship_wales_0020_brighton', sound='DX_m08_bship_wales_0020_brighton', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_bship_wales_0020_brighton, {'template_name': 'DX_m08_bship_wales_0020_brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_bship_wales_0030_brighton = Sound(root=self, name='DX_m08_bship_wales_0030_brighton', sound='DX_m08_bship_wales_0030_brighton', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_bship_wales_0030_brighton, {'template_name': 'DX_m08_bship_wales_0030_brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_bship_wales_0040_trent = Sound(root=self, name='DX_m08_bship_wales_0040_trent', sound='DX_m08_bship_wales_0040_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_bship_wales_0040_trent, {'template_name': 'DX_m08_bship_wales_0040_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_bship_wales_0050_brighton = Sound(root=self, name='DX_m08_bship_wales_0050_brighton', sound='DX_m08_bship_wales_0050_brighton', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_bship_wales_0050_brighton, {'template_name': 'DX_m08_bship_wales_0050_brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_bship_wales_0060_darcy = Sound(root=self, name='DX_m08_bship_wales_0060_darcy', sound='DX_m08_bship_wales_0060_darcy', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_bship_wales_0060_darcy, {'template_name': 'DX_m08_bship_wales_0060_darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_final_0010_mandrake = Sound(root=self, name='DX_m08_final_0010_mandrake', sound='DX_m08_final_0010_mandrake', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_final_0010_mandrake, {'template_name': 'DX_m08_final_0010_mandrake', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_final_0020_hatcher = Sound(root=self, name='DX_m08_final_0020_hatcher', sound='DX_m08_final_0020_hatcher', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_final_0020_hatcher, {'template_name': 'DX_m08_final_0020_hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_final_0030_darcy = Sound(root=self, name='DX_m08_final_0030_darcy', sound='DX_m08_final_0030_darcy', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_final_0030_darcy, {'template_name': 'DX_m08_final_0030_darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m08_final_0040_darcy = Sound(root=self, name='DX_m08_final_0040_darcy', sound='DX_m08_final_0040_darcy', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m08_final_0040_darcy, {'template_name': 'DX_m08_final_0040_darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_kaytlin = Character(root=self, actor=actors.Kaitlyn, light_group=0, init_point='Char_kaitlyn', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_kaytlin, {'template_name': 'kaytlin', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Kaytlin', 'category': 'Character'}})
        obj_Char_brighton = Character(root=self, actor=actors.Brighton, light_group=0, init_point='Char_brighton', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_brighton, {'template_name': 'brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Brighton', 'category': 'Character'}})
        obj_Char_darcy = Character(root=self, actor=actors.Darcy, light_group=0, init_point='Char_darcy', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_darcy, {'template_name': 'darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Darcy', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_start_darcy = LookAtCamera(root=self, name='cam_start_darcy', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start_darcy, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_start_trent = LookAtCamera(root=self, name='cam_start_trent', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_greetings = LookAtCamera(root=self, name='cam_greetings', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_greetings, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_greetings_kaytlin = LookAtCamera(root=self, name='cam_greetings_kaytlin', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_greetings_kaytlin, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_darcy_sit = LookAtCamera(root=self, name='cam_darcy_sit', fov=22, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_darcy_sit, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_brighton = LookAtCamera(root=self, name='cam_brighton', fov=18, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_brighton, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_brighton_near = LookAtCamera(root=self, name='cam_brighton_near', fov=18, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_brighton_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_sit = LookAtCamera(root=self, name='cam_trent_sit', fov=18, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_trent_sit, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_far = LookAtCamera(root=self, name='cam_trent_far', fov=18, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_trent_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_near = LookAtCamera(root=self, name='cam_trent_near', fov=18, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_trent_near, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_xnear = LookAtCamera(root=self, name='cam_trent_xnear', fov=15, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_trent_xnear, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_kaytlin = LookAtCamera(root=self, name='cam_kaytlin', fov=15, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_kaytlin, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_IDLE_000LV_XA_05, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 16, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 20, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=9, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 22, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=2.6, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 27, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-67, axis='Y_AXIS', duration=0, smooth=False)
        # source event 28, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_03, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.01
        # source event 15, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', angle=-125, axis='Y_AXIS', duration=0, smooth=False)
        # source event 17, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', angle=10, axis='Y_AXIS', duration=0, smooth=False)
        # source event 19, 0.01s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        t += 2.59
        # source event 23, 2.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=6, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 24, 2.6s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=5, axis='Y_AXIS', duration=1, smooth=False)
        t += 0.4
        # source event 29, 3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        main_group.append_time(5)

        # Line 10: source 5s; allocated facial window 7s.
        t = 0
        # source event 32, 5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_darcy')
        t += 3
        # source event 30, 8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_10', None)
        obj_Char_darcy.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.2)

        # Line 20: source 10.8s; allocated facial window 5s.
        t = 0
        t += 2.7
        # source event 31, 13.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_STND_WALK_TRNS_270LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_20', None)
        obj_Char_darcy.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 30: source 14.3s; allocated facial window 3.5s.
        t = 0
        # source event 37, 14.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_trent')
        t += 0.5
        # source event 40, 14.8s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_head_darcy_move_from_start', duration=5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2.2
        # source event 25, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=1, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        # source event 26, 17s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=-8, axis='Y_AXIS', duration=1, smooth=False)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_30', None)
        obj_Char_trent.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.2
        # source event 41, 18s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_greetings')
        # source event 42, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_greetings', target_name='automarker_cam_greetings_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 43, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_greetings_focus', target_name='automarker_cam_greetings_marker_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 44, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', target_name='automarker_point_darcy_walk', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 46, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_WLKG_000LV_XA_01, duration=4, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 47, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_walk', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 49, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=4, time_scale=0.6, start_time=0.5, loop=True, trans_time=None)
        t += 0.01
        # source event 45, 18.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 48, 18.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=25, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.99
        # source event 52, 19s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_brighton', target_name='automarker_head_darcy_near_table', duration=15, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        main_group.append_time(2.2)

        # Line 40: source 20s; allocated facial window 6s.
        t = 0
        # source event 53, 20s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_head_darcy_near_table', duration=5, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_40', None)
        obj_Char_brighton.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 50: source 25s; allocated facial window 12s.
        t = 0
        # source event 54, 25s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_greetings_kaytlin')
        # source event 57, 25s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_head_trent_near_table_up', duration=15, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 58, 25s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_head_trent_near_table', duration=15, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 2
        # source event 55, 27s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_GRABR_CHIN_RLEASE_000LV_XA_03, duration=7, time_scale=0.3, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 56, 29s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHAND_HNEUT_GESTR_THUMB_000LV_00, duration=0.5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 4
        # source event 62, 33s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', target_name='automarker_point_darcy_sit', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 63, 33s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 66, 33s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='automarker_darcy_head_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 67, 33s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='automarker_darcy_eye_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.01
        # source event 64, 33.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-15, axis='Y_AXIS', duration=0, smooth=False)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_50', None)
        obj_Char_kaytlin.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 60: source 34s; allocated facial window 11.5s.
        t = 0
        # source event 65, 34s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_sit')
        t += 1
        # source event 68, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent_front', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 69, 35s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 70, 35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_CONV_LHNDUP_TRNS_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 0.8
        # source event 71, 35.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_CONV_LHND_CASL_000LV_xa_03, duration=3, time_scale=0.4, start_time=0, loop=True, trans_time=1)
        t += 3.0
        # source event 72, 38.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_CONV_LHNDDN_TRNS_000LV_XA_01, duration=3, time_scale=0.5, start_time=0, loop=False, trans_time=1.5)
        t += 0.2
        # source event 79, 39s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_brighton', target_name='automarker_brighton_head_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 80, 39s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_brighton', target_name='automarker_brighton_eye_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_60', None)
        obj_Char_darcy.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.5)

        # Line 70: source 40s; allocated facial window 6s.
        t = 0
        # source event 76, 40s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_sit', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 77, 40s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=1050, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 81, 40s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 0.01
        # source event 78, 40.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=20, axis='Y_AXIS', duration=0, smooth=False)
        t += 0.99
        # source event 84, 41s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 85, 41s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_70', None)
        obj_Char_brighton.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 80: source 43s; allocated facial window 3.5s.
        t = 0
        # source event 86, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_xnear')
        t += 1.7
        # source event 89, 44.7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_80', None)
        obj_Char_trent.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 90: source 44.8s; allocated facial window 6s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_90', None)
        obj_Char_brighton.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 100: source 50.3s; allocated facial window 3.5s.
        t = 0
        # source event 92, 50.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_100', None)
        obj_Char_trent.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.8)

        # Line 110: source 52s; allocated facial window 8s.
        t = 0
        # source event 95, 52s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 1
        # source event 96, 53s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_GESTR_SELF_000LV_XA_03, duration=2.3, time_scale=0.2, start_time=0, loop=False, trans_time=0.3)
        # source event 97, 53s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_CASL_000LV_XB_01, duration=2.3, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 98, 55.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_110', None)
        obj_Char_brighton.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.3)

        # Line 120: source 55.7s; allocated facial window 3.5s.
        t = 0
        # source event 102, 55.7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_120', None)
        obj_Char_trent.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 130: source 57.2s; allocated facial window 6s.
        t = 0
        # source event 105, 57.2s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_130', None)
        obj_Char_brighton.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.2)

        # Line 140: source 60s; allocated facial window 5.5s.
        t = 0
        # source event 108, 60s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_xnear')
        # source event 109, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_SHRG_SHLDRS_SMALL_000LV_XA_03, duration=100, time_scale=0.4, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_140', None)
        obj_Char_trent.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 150: source 63s; allocated facial window 8s.
        t = 0
        # source event 114, 63s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 6
        # source event 118, 69s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_kaytlin_front_fwd2', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 119, 69s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_kaytlin_lwr', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 122, 69s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_GESTL_180LV_XA_03, duration=100, time_scale=0.4, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_150', None)
        obj_Char_brighton.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.3)

        # Line 160: source 69.7s; allocated facial window 4.7s.
        t = 0
        t += 2.3
        # source event 120, 72s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_trent_brightonside_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 121, 72s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_trent_brightonside', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_160', None)
        obj_Char_brighton.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.3)

        # Line 170: source 74.7s; allocated facial window 5.3s.
        t = 0
        # source event 125, 74.7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_170', None)
        obj_Char_trent.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 180: source 80s; allocated facial window 5s.
        t = 0
        # source event 129, 80s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_180', None)
        obj_Char_brighton.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 190: source 85s; allocated facial window 3.9s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_190', None)
        obj_Char_brighton.facial(group=MAIN, index=190, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 200: source 89.4s; allocated facial window 3.5s.
        t = 0
        # source event 134, 89.4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_200', None)
        obj_Char_trent.facial(group=MAIN, index=200, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.9)

        # Line 210: source 92s; allocated facial window 7.8s.
        t = 0
        # source event 137, 92s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 2
        # source event 144, 94s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_kaytlin_ik_not_interested_head', duration=1000, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 145, 94s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_kaytlin_ik_not_interested_eye', duration=1000, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 138, 94.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_kaytlin_front_fwd2', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 139, 94.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_kaytlin_lwr', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 146, 95s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_GRABR_HEAD_RLEASE_000LV_XA_03, duration=7, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 147, 95s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=0.9, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_210', None)
        obj_Char_brighton.facial(group=MAIN, index=210, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.8)

        # Line 215: source 97s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        voice_sound = self.lookup_single_sound(215)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 143, 97s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_kaytlin')
        # source event 149, 97s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHEAD_MAD_COLD_000LV_XA_, duration=5, time_scale=1, start_time=0.8, loop=False, trans_time=0.25)
        t += 2.5
        # source event 150, 99.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        # source event 151, 99.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_trent_brightonside_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 152, 99.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_trent_brightonside', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(3)

        # Line 220: source 100s; allocated facial window 4.7s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_220', None)
        obj_Char_brighton.facial(group=MAIN, index=220, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.2)

        # Line 230: source 104.5s; allocated facial window 4.7s.
        t = 0
        t += 1.8
        # source event 157, 106.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLHEAD_MAD_COLD_000LV_XA_, duration=4.7, time_scale=1, start_time=0.6, loop=False, trans_time=0.25)
        t += 0.7
        # source event 160, 107s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_CHRF_TRNS_000LV_XA_02, duration=100, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_230', None)
        obj_Char_brighton.facial(group=MAIN, index=230, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 235: source 108.2s; allocated facial window 4.7s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_235', None)
        obj_Char_brighton.facial(group=MAIN, index=235, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 240: source 111.2s; allocated facial window 3.5s.
        t = 0
        # source event 161, 111.2s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_240', None)
        obj_Char_trent.facial(group=MAIN, index=240, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 250: source 113s; allocated facial window 7.3s.
        t = 0
        # source event 164, 113s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 4
        # source event 168, 117s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDUP_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_250', None)
        obj_Char_brighton.facial(group=MAIN, index=250, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.9)

        # Line 260: source 117.4s; allocated facial window 16.6s.
        t = 0
        t += 0.6
        # source event 171, 118s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLHAND_HNEUT_GESTR_CASL_000LV_00, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.7
        # source event 169, 118.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRF_CONV_RHND_CASL_000LV_xb_03, duration=2.3, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 2.3
        # source event 170, 121s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_260', None)
        obj_Char_brighton.facial(group=MAIN, index=260, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.4)

        # Line 270: source 127.6s; allocated facial window 3.5s.
        t = 0
        # source event 176, 127.6s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_270', None)
        obj_Char_trent.facial(group=MAIN, index=270, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.1)

        # Line 280: source 131s; allocated facial window 14s.
        t = 0
        # source event 179, 131s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_280', None)
        obj_Char_brighton.facial(group=MAIN, index=280, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 290: source 141s; allocated facial window 12.5s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_290', None)
        obj_Char_brighton.facial(group=MAIN, index=290, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.5)

        # Line 300: source 150s; allocated facial window 3.5s.
        t = 0
        # source event 186, 150s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_300', None)
        obj_Char_trent.facial(group=MAIN, index=300, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 310: source 151.8s; allocated facial window 4.3s.
        t = 0
        # source event 189, 151.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_310', None)
        obj_Char_brighton.facial(group=MAIN, index=310, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.2)

        # Line 320: source 156.3s; allocated facial window 5.2s.
        t = 0
        # source event 192, 156.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_320', None)
        obj_Char_trent.facial(group=MAIN, index=320, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.2)

        # Line 330: source 160.3s; allocated facial window 7s.
        t = 0
        # source event 196, 160.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_330', None)
        obj_Char_brighton.facial(group=MAIN, index=330, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.3)

        # Line 340: source 167s; allocated facial window 7s.
        t = 0
        # source event 199, 167s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_340', None)
        obj_Char_trent.facial(group=MAIN, index=340, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.6)

        # Line 350: source 173.4s; allocated facial window 12s.
        t = 0
        # source event 202, 173.4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_kaytlin')
        # source event 203, 173.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_kaytlin_ik_not_interested_head_pos2', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 205, 173.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_kaytlin_ik_not_interested_eye_pos2', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 207, 173.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_HOLD_HEAD_RLEASE_000LV_XA_03, duration=7, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        t += 1.0
        # source event 206, 174.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_kaytlin_ik_not_interested_eye_pos3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 204, 174.9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_kaytlin_ik_not_interested_head_pos3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 210, 175.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHEAD_MAD_COLD_000LV_XA_, duration=0.8, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_350', None)
        obj_Char_kaytlin.facial(group=MAIN, index=350, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.0)

        # Line 360: source 177.4s; allocated facial window 7s.
        t = 0
        # source event 211, 177.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_kaytlin_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 212, 177.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_kaytlin', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 213, 177.4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        t += 2.6
        # source event 224, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_kaytlin_front_fwd2', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 225, 180s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_kaytlin_lwr', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_360', None)
        obj_Char_trent.facial(group=MAIN, index=360, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3.6)

        # Line 370: source 180.8s; allocated facial window 12s.
        t = 0
        # source event 216, 180.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_kaytlin')
        # source event 219, 180.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_kaytlin_ik_not_interested_head_init', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 220, 180.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_kaytlin_ik_not_interested_eye_init', duration=1.8, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.6
        # source event 217, 181.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_GRABR_HEAD_RLEASE_000LV_XA_03, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        # source event 218, 181.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=0.9, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 2.5
        # source event 223, 183.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHEAD_MAD_COLD_000LV_XA_, duration=0.6, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_370', None)
        obj_Char_kaytlin.facial(group=MAIN, index=370, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.4)

        # Line 380: source 185.4s; allocated facial window 8s.
        t = 0
        # source event 226, 185.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_trent_brightonside_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 227, 185.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_trent_brightonside', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 228, 185.4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 3.0
        # source event 231, 188.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_brighton', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 232, 188.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_brighton', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_380', None)
        obj_Char_brighton.facial(group=MAIN, index=380, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.2)

        # Line 390: source 189.2s; allocated facial window 7s.
        t = 0
        # source event 233, 189.2s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_390', None)
        obj_Char_trent.facial(group=MAIN, index=390, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.6)

        # Line 400: source 191.6s; allocated facial window 8s.
        t = 0
        # source event 236, 191.6s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        t += 6.8
        # source event 239, 198.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=0.3)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_400', None)
        obj_Char_brighton.facial(group=MAIN, index=400, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 410: source 198.6s; allocated facial window 8s.
        t = 0
        t += 3.8
        # source event 240, 202.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_GESTR_SELF_000LV_XA_03, duration=2.3, time_scale=0.2, start_time=0, loop=False, trans_time=0.3)
        # source event 241, 202.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_CASL_000LV_XB_01, duration=2.3, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        t += 2.5
        # source event 242, 204.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_410', None)
        obj_Char_brighton.facial(group=MAIN, index=410, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 420: source 205.6s; allocated facial window 13s.
        t = 0
        # source event 245, 205.6s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_near')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_420', None)
        obj_Char_trent.facial(group=MAIN, index=420, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.2)

        # Line 430: source 214.4s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        voice_sound = self.lookup_single_sound(430)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 250, 214.4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_kaytlin')
        # source event 251, 214.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_kaytlin_ik_not_interested_head_pos2', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 253, 214.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_kaytlin_ik_not_interested_eye_pos2', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 255, 214.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_HOLD_HEAD_RLEASE_000LV_XA_03, duration=7, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        # source event 257, 214.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHEAD_MAD_COLD_000LV_XA_, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1.5
        # source event 252, 215.9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_kaytlin_ik_not_interested_head_pos3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 254, 215.9s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_kaytlin_ik_not_interested_eye_pos3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(2.5)

        # Line 435: source 216.9s; allocated facial window 19s.
        t = 0
        t += 5.0
        # source event 262, 221.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_CONV_RHNDDN_TRNS_000LV_XA_02, duration=8, time_scale=0.3, start_time=0, loop=False, trans_time=1)
        # source event 263, 221.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=10, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 7.5
        # source event 264, 229.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_kaytlin_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 265, 229.4s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_kaytlin', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_435', None)
        obj_Char_kaytlin.facial(group=MAIN, index=435, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5.9)
        restore_dialogue(self)
