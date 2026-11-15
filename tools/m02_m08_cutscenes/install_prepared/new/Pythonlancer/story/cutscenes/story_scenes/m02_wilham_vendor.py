"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm02_wilham_vendor'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(15.133)
        obj_the_char = Character(root=self, actor=actors.Wilham, light_group=0, init_point='Char_wilham', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_the_char, {'template_name': 'wilham', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character'}})
        t = 0
        # source event 0, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07, duration=7.232, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 7.233
        # source event 1, 7.233s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_wilham', anim=Male.Sc_MLBODY_CHRB_IDLE_SMALL_000LV_XA_07, duration=7.9, time_scale=1, start_time=0, loop=False, trans_time=None)
        restore_dialogue(self)
