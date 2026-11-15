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


class Actor_obj_Char_trent_base(actors.Actor):
    NAME = 'trent_base'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'trent'
    GAME_ACTOR = 'Player'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_offer_decision'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(140.0)
        obj_Char_bartender_Fixture = Character(root=self, actor=Actor_obj_Char_bartender_Fixture, light_group=0, init_point='Char_bartender_fixture', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_bartender_Fixture, {'template_name': 'li_bartender_1', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'bartender', 'category': 'Character'}})
        obj_Char_trent_base = Character(root=self, actor=Actor_obj_Char_trent_base, light_group=0, init_point='Char_trent_base', rotate_from_quat=True, use_ambient=False, floor_height=-1000)
        preserve_entity(obj_Char_trent_base, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': -1000}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent_original', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'TrentOriginal', 'category': 'Character'}})
        obj_Char_barman = Character(root=self, actor=actors.DetroitBarman, light_group=0, init_point='Char_barman', rotate_from_quat=True, use_ambient=False, floor_height='=-110')
        preserve_entity(obj_Char_barman, {'template_name': 'm07_bartender', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': '=-110'}, 'userprops': {'actor': 'm6_bartender', 'category': 'Character'}})
        obj_cam_trent_deal = LookAtCamera(root=self, name='cam_trent_deal', fov=20, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_trent_deal, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 1, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_bartender_fixture', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 2, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_base', target_name='offscreen', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 3, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_barman', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10000, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 4, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=10000, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 5, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_deal')
        restore_dialogue(self)
