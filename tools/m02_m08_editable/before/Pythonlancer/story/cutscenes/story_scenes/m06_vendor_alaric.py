"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_vendor_alaric'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(61.464)
        obj_char_alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True, use_ambient=True, floor_height=0)
        preserve_entity(obj_char_alaric, {'template_name': 'Alaric', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character'}})
        t = 0
        # source event 0, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=7.9, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 7.9
        # source event 1, 7.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_LOOK_AROU_000LV_XA_04, duration=4, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 4.0
        # source event 2, 11.9s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=7.9, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 7.9
        # source event 3, 19.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_LOOK_AROU_CASL_000LV_XA_04, duration=6.666, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 6.666
        # source event 4, 26.466s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07, duration=7.233, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 7.233
        # source event 5, 33.699s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=2.6, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.6
        # source event 6, 36.299s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_TWSTS_FROM_090LV_XA_04, duration=4.033, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 4.033
        # source event 7, 40.332s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07, duration=7.233, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 7.233
        # source event 8, 47.565s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_LOOK_AROU_CASL_000LV_XA_04, duration=6.666, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 6.666
        # source event 9, 54.231s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_alaric', anim=Male.Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07, duration=7.233, time_scale=1, start_time=0, loop=False, trans_time=None)
        restore_dialogue(self)
