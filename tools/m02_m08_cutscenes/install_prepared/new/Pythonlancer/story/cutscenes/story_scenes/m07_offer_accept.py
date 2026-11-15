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


class Actor_obj_Char_trent_base(actors.Actor):
    NAME = 'trent_base'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'trent'
    GAME_ACTOR = 'Player'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_offer_accept'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_prop_cigarette_2 = Asset_obj_prop_cigarette_2(root=self, name='prop_cigarette_2', light_group=0, init_point='prop_cigarette_2', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_prop_cigarette_2, {'template_name': 'cigarette_2', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_DX_m06_freeport_0010_delta1 = Sound(root=self, name='DX_m06_freeport_0010_delta1', sound='DX_m06_freeport_0010_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0010_delta1, {'template_name': 'DX_m06_freeport_0010_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0020_trent = Sound(root=self, name='DX_m06_freeport_0020_trent', sound='DX_m06_freeport_0020_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0020_trent, {'template_name': 'DX_m06_freeport_0020_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0030_delta1 = Sound(root=self, name='DX_m06_freeport_0030_delta1', sound='DX_m06_freeport_0030_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0030_delta1, {'template_name': 'DX_m06_freeport_0030_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0040_delta1 = Sound(root=self, name='DX_m06_freeport_0040_delta1', sound='DX_m06_freeport_0040_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0040_delta1, {'template_name': 'DX_m06_freeport_0040_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0050_delta1 = Sound(root=self, name='DX_m06_freeport_0050_delta1', sound='DX_m06_freeport_0050_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0050_delta1, {'template_name': 'DX_m06_freeport_0050_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0060_delta1 = Sound(root=self, name='DX_m06_freeport_0060_delta1', sound='DX_m06_freeport_0060_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0060_delta1, {'template_name': 'DX_m06_freeport_0060_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0070_trent = Sound(root=self, name='DX_m06_freeport_0070_trent', sound='DX_m06_freeport_0070_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0070_trent, {'template_name': 'DX_m06_freeport_0070_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0090_delta1 = Sound(root=self, name='DX_m06_freeport_0090_delta1', sound='DX_m06_freeport_0090_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0090_delta1, {'template_name': 'DX_m06_freeport_0090_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m06_freeport_0100_delta1 = Sound(root=self, name='DX_m06_freeport_0100_delta1', sound='DX_m06_freeport_0100_delta1', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m06_freeport_0100_delta1, {'template_name': 'DX_m06_freeport_0100_delta1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0010_barman = Sound(root=self, name='DX_m07_offer_0010_barman', sound='DX_m07_offer_0010_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0010_barman, {'template_name': 'DX_m07_offer_0010_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0020_trent = Sound(root=self, name='DX_m07_offer_0020_trent', sound='DX_m07_offer_0020_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0020_trent, {'template_name': 'DX_m07_offer_0020_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0030_barman = Sound(root=self, name='DX_m07_offer_0030_barman', sound='DX_m07_offer_0030_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0030_barman, {'template_name': 'DX_m07_offer_0030_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0040_trent = Sound(root=self, name='DX_m07_offer_0040_trent', sound='DX_m07_offer_0040_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0040_trent, {'template_name': 'DX_m07_offer_0040_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0050_barman = Sound(root=self, name='DX_m07_offer_0050_barman', sound='DX_m07_offer_0050_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0050_barman, {'template_name': 'DX_m07_offer_0050_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0060_trent = Sound(root=self, name='DX_m07_offer_0060_trent', sound='DX_m07_offer_0060_trent', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0060_trent, {'template_name': 'DX_m07_offer_0060_trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0070_barman = Sound(root=self, name='DX_m07_offer_0070_barman', sound='DX_m07_offer_0070_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0070_barman, {'template_name': 'DX_m07_offer_0070_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0080_barman = Sound(root=self, name='DX_m07_offer_0080_barman', sound='DX_m07_offer_0080_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0080_barman, {'template_name': 'DX_m07_offer_0080_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0090_barman = Sound(root=self, name='DX_m07_offer_0090_barman', sound='DX_m07_offer_0090_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0090_barman, {'template_name': 'DX_m07_offer_0090_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_DX_m07_offer_0100_barman = Sound(root=self, name='DX_m07_offer_0100_barman', sound='DX_m07_offer_0100_barman', attenuation=0, dmin=50, dmax=1000, priority=None)
        preserve_entity(obj_DX_m07_offer_0100_barman, {'template_name': 'DX_m07_offer_0100_barman', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 1000, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_Char_trent_base = Character(root=self, actor=Actor_obj_Char_trent_base, light_group=0, init_point='Char_trent_base', rotate_from_quat=True, use_ambient=False, floor_height=-1000)
        preserve_entity(obj_Char_trent_base, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': -1000}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent_original', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'TrentOriginal', 'category': 'Character'}})
        obj_Char_barman = Character(root=self, actor=actors.DetroitBarman, light_group=0, init_point='Char_barman', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_barman, {'template_name': 'm07_bartender', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'm6_bartender', 'category': 'Character'}})
        obj_cam_trent_deal = LookAtCamera(root=self, name='cam_trent_deal', fov=15, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_deal, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        main_group.append_time(0)

        # Line 110: source 0s; allocated facial window 6s.
        t = 0
        # source event 1, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender_fixture', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 2, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_base', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 3, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10000, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 4, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_deal')
        # source event 7, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=15, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        # source event 8, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_deal')
        # source event 9, 0s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_head_barman_near', duration=100, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 7, 'Msn7Offer', 'm07_offer')
        self.groups.pop('motion_110', None)
        obj_Char_trent.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)
        restore_dialogue(self)
