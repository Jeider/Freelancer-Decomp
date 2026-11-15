"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm08_offer_accept'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
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
        main_group.append_time(0)

        # Line 440: source 0s; allocated facial window 10.5s.
        t = 0
        # source event 14, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 16, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_IDLE_000LV_XA_05, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 18, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 20, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 22, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_kaytlin_ik_not_interested_head_pos3', duration=0, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 23, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_kaytlin_ik_not_interested_eye_pos3', duration=0, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 24, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent_front', duration=0, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 25, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent', duration=0, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 26, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='automarker_darcy_head_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 27, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_darcy', target_name='automarker_darcy_eye_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 28, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_brighton', target_name='automarker_brighton_head_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 29, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_brighton', target_name='automarker_brighton_eye_ik', duration=2555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 30, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 31, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=555, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 32, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_kaytlin_ik_not_interested_head', duration=1000, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 33, 0s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_kaitlyn', target_name='automarker_kaytlin_ik_not_interested_eye', duration=1000, transition_duration=2, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 34, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_kaytlin_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 35, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_kaytlin', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 36, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sit')
        t += 0.01
        # source event 15, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 17, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', angle=-125, axis='Y_AXIS', duration=0, smooth=False)
        # source event 19, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', angle=10, axis='Y_AXIS', duration=0, smooth=False)
        # source event 21, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=20, axis='Y_AXIS', duration=0, smooth=False)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_440', None)
        obj_Char_trent.facial(group=MAIN, index=440, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 450: source 10s; allocated facial window 20s.
        t = 0
        # source event 40, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_kaytlin')
        t += 2
        # source event 47, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaitlyn', anim=Female.Sc_FMBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=100, time_scale=0.3, start_time=0, loop=False, trans_time=1)
        t += 6
        # source event 50, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_kaytlin_front_fwd2', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 51, 18s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_kaytlin_lwr', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3.5
        # source event 48, 21.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_head', target_name='automarker_head_brighton_front_fwd', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 49, 21.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_kaytlin_ik_not_interested_eye', target_name='automarker_head_brighton_front_lwr', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_450', None)
        obj_Char_kaytlin.facial(group=MAIN, index=450, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.6)

        # Line 460: source 22.4s; allocated facial window 12s.
        t = 0
        t += 2.6
        # source event 52, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_head_ik', target_name='automarker_head_trent_brightonside_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 53, 25s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_brighton_eye_ik', target_name='automarker_head_trent_brightonside', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_460', None)
        obj_Char_kaytlin.facial(group=MAIN, index=460, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.9)

        # Line 470: source 25.5s; allocated facial window 8s.
        t = 0
        # source event 54, 25.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_brighton')
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_470', None)
        obj_Char_brighton.facial(group=MAIN, index=470, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.2)

        # Line 480: source 33.3s; allocated facial window 9s.
        t = 0
        # source event 57, 33.3s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_darcy_sit')
        t += 3.0
        # source event 63, 36.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRB_STNDCR_TRNS_090LV_XA_04, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        t += 0.3
        # source event 61, 36.6s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_head_ik', target_name='automarker_head_trent_side_darcyout', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 62, 36.6s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_darcy_eye_ik', target_name='automarker_head_trent_side_darcyout', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 8, 'Msn8Offer', 'm08_offer')
        self.groups.pop('motion_480', None)
        obj_Char_darcy.facial(group=MAIN, index=480, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.7)
        restore_dialogue(self)
