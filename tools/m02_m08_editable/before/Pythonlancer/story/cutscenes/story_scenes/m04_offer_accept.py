"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm04_offer_accept'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_DX_m04_offer_0010_jacobo = Sound(root=self, name='DX_m04_offer_0010_jacobo', sound='DX_m04_offer_0010_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0010_jacobo, {'template_name': 'DX_m04_offer_0010_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0020_jacobo = Sound(root=self, name='DX_m04_offer_0020_jacobo', sound='DX_m04_offer_0020_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0020_jacobo, {'template_name': 'DX_m04_offer_0020_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0030_trent = Sound(root=self, name='DX_m04_offer_0030_trent', sound='DX_m04_offer_0030_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0030_trent, {'template_name': 'DX_m04_offer_0030_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0040_jacobo = Sound(root=self, name='DX_m04_offer_0040_jacobo', sound='DX_m04_offer_0040_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0040_jacobo, {'template_name': 'DX_m04_offer_0040_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0050_trent = Sound(root=self, name='DX_m04_offer_0050_trent', sound='DX_m04_offer_0050_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0050_trent, {'template_name': 'DX_m04_offer_0050_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0060_jacobo = Sound(root=self, name='DX_m04_offer_0060_jacobo', sound='DX_m04_offer_0060_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0060_jacobo, {'template_name': 'DX_m04_offer_0060_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0062_jacobo = Sound(root=self, name='DX_m04_offer_0062_jacobo', sound='DX_m04_offer_0062_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0062_jacobo, {'template_name': 'DX_m04_offer_0062_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0065_jacobo = Sound(root=self, name='DX_m04_offer_0065_jacobo', sound='DX_m04_offer_0065_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0065_jacobo, {'template_name': 'DX_m04_offer_0065_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m04_offer_0067_jacobo = Sound(root=self, name='DX_m04_offer_0067_jacobo', sound='DX_m04_offer_0067_jacobo', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m04_offer_0067_jacobo, {'template_name': 'DX_m04_offer_0067_jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_jacobo = Character(root=self, actor=actors.Jacobo, light_group=0, init_point='Char_jacobo', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jacobo, {'template_name': 'jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'jacobo'}})
        obj_cam_jacobo_sitting = LookAtCamera(root=self, name='cam_jacobo_sitting', fov=16, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_jacobo_sitting, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_sitting = LookAtCamera(root=self, name='cam_trent_sitting', fov=16, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_trent_sitting, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        main_group.append_time(0)

        # Line 70: source 0s; allocated facial window 7s.
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        # source event 4, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 6, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sitting')
        # source event 10, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_CHRB_TRNS_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_70', None)
        obj_Char_trent.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 80: source 4s; allocated facial window 11s.
        t = 0
        # source event 11, 4s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_jacobo_sitting')
        t += 8
        # source event 16, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_STNDCL_TRNS_270LV_XA_06, duration=2.5, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 17, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo_standing', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 18, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo_standing', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 19, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_jacobo_standing_go_out', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 20, 14s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_jacobo_standing_go_out', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 21, 14s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=2, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 22, 14s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=2, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_80', None)
        obj_Char_jacobo.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 90: source 14.5s; allocated facial window 4s.
        t = 0
        # source event 23, 14.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_sitting')
        t += 1.0
        # source event 26, 15.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_STNDCR_TRNS_090LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 4, 'Msn4Offer', 'm04_offer')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(1.0)
        restore_dialogue(self)
