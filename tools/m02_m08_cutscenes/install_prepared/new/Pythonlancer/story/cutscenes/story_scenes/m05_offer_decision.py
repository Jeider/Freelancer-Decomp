"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_offer_decision'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(50000.0)
        obj_ambi_LtG00_Tbl_rTable4_01 = Light(root=self, name='ambi_LtG00_Tbl_rTable4/01', point_name='ambi_LtG00_Tbl_rTable4/01', extra_name='', light_group=5, diffuse=[1, 1, 1], ambient=[0.141176, 0.141176, 0.141176], direction=[0, 0, 1], light_type='L_POINT', on=True, range=451, cutoff=180, theta=180, color=[214, 187, 133], attenuation=[0.0099999998, 0, 5.1500000954])
        preserve_entity(obj_ambi_LtG00_Tbl_rTable4_01, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [214, 187, 133], 'diffuse': [1, 1, 1], 'specular': [0, 0, 0], 'ambient': [0.141176, 0.141176, 0.141176], 'direction': [0, 0, 1], 'range': 451, 'cutoff': 180, 'type': 'L_POINT', 'theta': 180, 'atten': [0.0099999998, 0, 5.1500000954]}})
        obj_ambi_LtG00_Bar_Ovrhd01A = Light(root=self, name='ambi_LtG00_Bar_Ovrhd01A', point_name='ambi_LtG00_Bar_Ovrhd01A', extra_name='', light_group=5, diffuse=[0.596078, 0.572549, 0.403922], ambient=[0.223529, 0.2, 0.192157], direction=[0, 0, 1], light_type='L_POINT', on=True, range=15, cutoff=18, theta=15, color=[233, 208, 150], attenuation=[0.8999999762, 0, 0.0060000001])
        preserve_entity(obj_ambi_LtG00_Bar_Ovrhd01A, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [233, 208, 150], 'diffuse': [0.596078, 0.572549, 0.403922], 'specular': [0, 0, 0], 'ambient': [0.223529, 0.2, 0.192157], 'direction': [0, 0, 1], 'range': 15, 'cutoff': 18, 'type': 'L_POINT', 'theta': 15, 'atten': [0.8999999762, 0, 0.0060000001]}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=5, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Hatcher', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_cam_table = LookAtCamera(root=self, name='cam_table', fov=25, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_table, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_table')
        # source event 2, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=50000, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 3, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_CHRB_IDLE_000LV_XA_06, duration=50000, time_scale=1, start_time=0, loop=True, trans_time=None)
        restore_dialogue(self)
