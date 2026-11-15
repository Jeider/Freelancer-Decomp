"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_vendor_hatcher'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(29.812)
        obj_char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=0, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_char_hatcher, {'template_name': 'hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character'}})
        t = 0
        # source event 0, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_SMALL_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 5
        # source event 1, 5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 2, 7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_LOOK_090LV_XA_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 3, 8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TWSTS_FROM_090LV_XA_02, duration=2.333, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.333
        # source event 4, 10.333s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_MED_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5.0
        # source event 5, 15.333s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_BIG_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 5.0
        # source event 6, 20.333s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TWSTS_LOOK_270LV_XA_02, duration=2.166, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.167
        # source event 7, 22.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_TWSTS_FROM_270LV_XA_02, duration=2.333, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 2.333
        # source event 8, 24.833s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_SMALL_000LV_XA_05, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        restore_dialogue(self)
