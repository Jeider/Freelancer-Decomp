"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Actor_obj_Char_li_bartender(actors.Actor):
    NAME = 'li_bartender'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm05_bartender'
    GAME_ACTOR = 'li_host'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_barman'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(63.498)
        obj_Char_li_bartender = Character(root=self, actor=Actor_obj_Char_li_bartender, light_group=0, init_point='Char_li_bartender', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_li_bartender, {'template_name': 'm05_bartender', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'li_host', 'category': 'Character'}})
        t = 0
        # source event 0, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_IDLE_BRTH_000LV_xa_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5
        # source event 1, 5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=3.833, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 3.833
        # source event 2, 8.833s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_02, duration=5, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 5.0
        # source event 3, 13.833s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=2.033, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.033
        # source event 4, 15.866s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_LOOK_WATC_IMPA_315DN_XA_07, duration=7.099, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 7.099
        # source event 5, 22.965s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_IDLE_BRTH_000LV_xa_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5.0
        # source event 6, 27.965s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 3.0
        # source event 7, 30.965s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_ATEASE_HOLD_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 3.0
        # source event 8, 33.965s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_ATEASE_RLEASE_000LV_XA_01, duration=2.966, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.966
        # source event 9, 36.931s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_LOOK_AROU_CASL_000LV_XA_08, duration=8.666, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 8.666
        # source event 10, 45.597s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_GESTR_COME_000LV_XA_02, duration=2.266, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.266
        # source event 11, 47.863s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_IDLE_BRTH_000LV_xa_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5.0
        # source event 12, 52.863s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_LEAN_LLEG_000LV_XA_02, duration=2.166, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.166
        # source event 13, 55.029s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_LEAN_LLEG_SWAY_000LV_XA_03, duration=6.2, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 6.2
        # source event 14, 61.229s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_li_bartender', anim=Male.Sc_MLBODY_STND_RETURNL_NEUT_000LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        restore_dialogue(self)
