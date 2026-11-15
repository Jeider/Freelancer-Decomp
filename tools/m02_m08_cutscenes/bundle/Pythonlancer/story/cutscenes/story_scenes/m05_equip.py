"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_prop_pda(Prop):
    COMPOUND_TEMPLATE_NAME = 'pda'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_hand(Prop):
    COMPOUND_TEMPLATE_NAME = 'equip_hand1_sml'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_pod(Prop):
    COMPOUND_TEMPLATE_NAME = 'equip_pod'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_podA(Prop):
    COMPOUND_TEMPLATE_NAME = 'equip_pod'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_podB(Prop):
    COMPOUND_TEMPLATE_NAME = 'equip_pod'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_Prop_Maglev(Prop):
    COMPOUND_TEMPLATE_NAME = 'maglev'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_hatcher2(actors.Actor):
    NAME = 'hatcher2'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'hatcher'
    GAME_ACTOR = 'hatcher2'


class Actor_obj_Char_medic1(actors.Actor):
    NAME = 'medic1'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'medic_3'
    GAME_ACTOR = 'medic_1'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_equip'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_ambi_additional = Light(root=self, name='ambi_additional', point_name='ambi_additional', extra_name='', light_group=0, diffuse=[0.92549, 0.835294, 0.92549], ambient=[0.121569, 0.121569, 0.121569], direction=[0, 0, 1], light_type='L_POINT', on=True, range=150, cutoff=30, theta=26.999985, color=[180, 180, 180], attenuation=[1, 0, 0.003])
        preserve_entity(obj_ambi_additional, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [180, 180, 180], 'diffuse': [0.92549, 0.835294, 0.92549], 'specular': [0, 0, 0], 'ambient': [0.121569, 0.121569, 0.121569], 'direction': [0, 0, 1], 'range': 150, 'cutoff': 30, 'type': 'L_POINT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_sound_cart_start = Sound(root=self, name='sound_cart_start', sound='equipment_cart_start', attenuation=-5, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_sound_cart_start, {'template_name': 'equipment_cart_start', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sound_cart_stop = Sound(root=self, name='sound_cart_stop', sound='equipment_cart_stop', attenuation=-5, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_sound_cart_stop, {'template_name': 'equipment_cart_stop', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sound_cart_loop = Sound(root=self, name='sound_cart_loop', sound='equipment_cart_loop', attenuation=-25, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_sound_cart_loop, {'template_name': 'equipment_cart_loop', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -25, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_sound_syd_clang = Sound(root=self, name='sound_syd_clang', sound='sfx_syd_clang', attenuation=-10, dmin=50, dmax=250, priority=None)
        preserve_entity(obj_sound_syd_clang, {'template_name': 'sfx_syd_clang', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 250, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio'}})
        obj_music_hall_ambient = Sound(root=self, name='music_hall_ambient', sound='ambience_equip_ground_larger', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_hall_ambient, {'template_name': 'ambience_equip_ground_larger', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_reveal_and_exposition = Sound(root=self, name='music_reveal_and_exposition', sound='rtc_music_reveal_and_exposition', attenuation=-12, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_reveal_and_exposition, {'template_name': 'rtc_music_reveal_and_exposition', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -12, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_anticipation_light = Sound(root=self, name='music_anticipation_light', sound='rtc_music_anticipation_light', attenuation=-8, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_anticipation_light, {'template_name': 'rtc_music_anticipation_light', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -8, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_reveal_special_mystery = Sound(root=self, name='music_reveal_special_mystery', sound='rtc_music_reveal_special_mystery', attenuation=-12, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_reveal_special_mystery, {'template_name': 'rtc_music_reveal_special_mystery', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -12, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_prop_pda = Asset_obj_prop_pda(root=self, name='prop_pda', light_group=0, init_point='prop_pda', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_pda, {'template_name': 'pda', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_hand = Asset_obj_hand(root=self, name='hand', light_group=0, init_point='hand', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_hand, {'template_name': 'equip_hand1_sml', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_pod = Asset_obj_pod(root=self, name='pod', light_group=0, init_point='pod', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_pod, {'template_name': 'equip_pod', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_podA = Asset_obj_podA(root=self, name='podA', light_group=0, init_point='podA', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_podA, {'template_name': 'equip_pod', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_podB = Asset_obj_podB(root=self, name='podB', light_group=0, init_point='podB', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_podB, {'template_name': 'equip_pod', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Prop_Maglev = Asset_obj_Prop_Maglev(root=self, name='Prop_Maglev', light_group=0, init_point='Prop_Maglev', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_Prop_Maglev, {'template_name': 'maglev', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'player', 'category': 'Character'}})
        obj_Char_hatcher = Character(root=self, actor=actors.Hatcher, light_group=0, init_point='Char_hatcher', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher, {'template_name': 'hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'hatcher', 'category': 'Character'}})
        obj_Char_hatcher2 = Character(root=self, actor=Actor_obj_Char_hatcher2, light_group=0, init_point='Char_hatcher2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_hatcher2, {'template_name': 'hatcher', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'hatcher2', 'category': 'Character'}})
        obj_Char_mandrake = Character(root=self, actor=actors.Mandrake, light_group=0, init_point='Char_mandrake', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_mandrake, {'template_name': 'mandrake', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'mandrake', 'category': 'Character'}})
        obj_Char_medic1 = Character(root=self, actor=Actor_obj_Char_medic1, light_group=0, init_point='Char_medic1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_medic1, {'template_name': 'medic_3', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'medic_1', 'category': 'Character'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=35, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 35, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake_full = LookAtCamera(root=self, name='cam_mandrake_full', fov=25, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_mandrake_full, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake = LookAtCamera(root=self, name='cam_mandrake', fov=20, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_mandrake, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake_top = LookAtCamera(root=self, name='cam_mandrake_top', fov=20, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_mandrake_top, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake_trentside = LookAtCamera(root=self, name='cam_mandrake_trentside', fov=20, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_mandrake_trentside, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_down = LookAtCamera(root=self, name='cam_hatcher_down', fov=10, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_hatcher_down, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 10, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher = LookAtCamera(root=self, name='cam_hatcher', fov=16, farplane=5000, look_duration=100)
        preserve_entity(obj_cam_hatcher, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = LookAtCamera(root=self, name='cam_trent', fov=15, farplane=5000, look_duration=200)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript1 = StaticCamera(root=self, name='cam_hatcher_descript1', fov=22, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript1, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 22, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript2 = StaticCamera(root=self, name='cam_hatcher_descript2', fov=15, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript2, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript3 = StaticCamera(root=self, name='cam_hatcher_descript3', fov=15, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript3, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_answer1 = StaticCamera(root=self, name='cam_trent_answer1', fov=14, farplane=5000)
        preserve_entity(obj_cam_trent_answer1, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 14, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript4 = StaticCamera(root=self, name='cam_hatcher_descript4', fov=15, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript4, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript5 = StaticCamera(root=self, name='cam_hatcher_descript5', fov=25, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript5, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_answer2 = StaticCamera(root=self, name='cam_trent_answer2', fov=14, farplane=5000)
        preserve_entity(obj_cam_trent_answer2, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 14, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_answer3 = StaticCamera(root=self, name='cam_trent_answer3', fov=14, farplane=5000)
        preserve_entity(obj_cam_trent_answer3, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 14, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake_trentwell = StaticCamera(root=self, name='cam_mandrake_trentwell', fov=16, farplane=5000)
        preserve_entity(obj_cam_mandrake_trentwell, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript6 = StaticCamera(root=self, name='cam_hatcher_descript6', fov=15, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript6, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript7 = StaticCamera(root=self, name='cam_hatcher_descript7', fov=15, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript7, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript8 = StaticCamera(root=self, name='cam_hatcher_descript8', fov=20, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript8, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript9 = StaticCamera(root=self, name='cam_hatcher_descript9', fov=15, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript9, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_descript10 = StaticCamera(root=self, name='cam_hatcher_descript10', fov=14, farplane=5000)
        preserve_entity(obj_cam_hatcher_descript10, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 14, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_answer4 = StaticCamera(root=self, name='cam_trent_answer4', fov=16, farplane=5000)
        preserve_entity(obj_cam_trent_answer4, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_angry01 = StaticCamera(root=self, name='cam_hatcher_angry01', fov=20, farplane=5000)
        preserve_entity(obj_cam_hatcher_angry01, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_angry02 = StaticCamera(root=self, name='cam_hatcher_angry02', fov=18, farplane=5000)
        preserve_entity(obj_cam_hatcher_angry02, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_objective01 = StaticCamera(root=self, name='cam_hatcher_objective01', fov=16, farplane=5000)
        preserve_entity(obj_cam_hatcher_objective01, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake_objective01 = StaticCamera(root=self, name='cam_mandrake_objective01', fov=18, farplane=5000)
        preserve_entity(obj_cam_mandrake_objective01, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_mandrake_objective02 = StaticCamera(root=self, name='cam_mandrake_objective02', fov=15, farplane=5000)
        preserve_entity(obj_cam_mandrake_objective02, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_objective02 = StaticCamera(root=self, name='cam_hatcher_objective02', fov=16, farplane=5000)
        preserve_entity(obj_cam_hatcher_objective02, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_hatcher_objective03 = StaticCamera(root=self, name='cam_hatcher_objective03', fov=16, farplane=5000)
        preserve_entity(obj_cam_hatcher_objective03, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_final = StaticCamera(root=self, name='cam_trent_final', fov=16, farplane=5000)
        preserve_entity(obj_cam_trent_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_final = StaticCamera(root=self, name='cam_final', fov=30, farplane=5000)
        preserve_entity(obj_cam_final, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 30, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_window = LookAtCamera(root=self, name='cam_window', fov=45, farplane=5000, look_duration=1)
        preserve_entity(obj_cam_window, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 45, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 35, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='podA', angle=40, axis='Z_AXIS', duration=0.01, smooth=False)
        # source event 36, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='podB', angle=40, axis='Z_AXIS', duration=0.01, smooth=False)
        # source event 37, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='pod', target_name='automarker_pod_move_bottom', duration=5, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 39, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='hand', target_name='automarker_hand_move_bottom', duration=5, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 41, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=15, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 42, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_medic1', anim=Male.Sc_MLBODY_STND_DEALR_PDA_000LV_XA_09, duration=8, time_scale=0.75, start_time=2, loop=False, trans_time=None)
        # source event 43, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_pda', parent_name='Char_medic1', duration=50, target_hardpoint='Hp_LHand_PDA', parent_hardpoint='HpLeftConnect')
        # source event 44, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_XB_04, duration=55, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 45, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_LEFT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 46, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_NEUT_RGHT_000LV_A_00, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 47, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STROLL_000LV_XA_01, duration=8.5, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 49, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher2', anim=Female.Sc_FMBODY_STND_000LV_B_07, duration=9, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 56, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 57, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 470, 0s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_cart_loop', duration=1, attenuation=-5)
        # source event 473, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_hall_ambient', duration=108, start_time=0, loop=True)
        t += 0.01
        # source event 55, 0.01s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        t += 0.29
        # source event 466, 0.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_cart_loop', duration=3.2, start_time=0, loop=True)
        t += 3.2
        # source event 38, 3.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='pod', angle=38, axis='X_AXIS', duration=1.5, smooth=True)
        # source event 467, 3.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_cart_stop', duration=2, start_time=0, loop=False)
        t += 1.0
        # source event 472, 4.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_syd_clang', duration=2, start_time=0, loop=False)
        t += 0.5
        # source event 40, 5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='hand', target_name='automarker_hand_move_top', duration=7, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 50, 5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_hatcher', duration=15, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 468, 5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_cart_start', duration=2, start_time=0, loop=False)
        t += 1
        # source event 471, 6s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_cart_loop', duration=5, attenuation=-25)
        t += 0.3
        # source event 469, 6.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='sound_cart_loop', duration=10, start_time=0, loop=True)
        t += 0.7
        # source event 51, 7s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_head_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 52, 7s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_hatcher', target_name='automarker_hatcher_eye_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 53, 7s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_mandrake', target_name='automarker_mandrake_head_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 54, 7s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_mandrake', target_name='automarker_mandrake_eye_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 58, 7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_down')
        t += 1
        # source event 474, 8s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_hall_ambient', duration=2, attenuation=-10)
        main_group.append_time(8.5)

        # Line 10: source 8.5s; allocated facial window 3s.
        t = 0
        # source event 48, 8.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STROLL_STND_TRNS_000LV_XA_01, duration=9, time_scale=0.825, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_10', None)
        obj_Char_hatcher.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 20: source 10.5s; allocated facial window 3s.
        t = 0
        # source event 61, 10.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake_top')
        # source event 62, 10.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_medic1', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=12, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 63, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_medic1', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=55, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_20', None)
        obj_Char_mandrake.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 30: source 12.5s; allocated facial window 5s.
        t = 0
        # source event 66, 12.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_down')
        # source event 67, 12.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=9, time_scale=0.9, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 68, 14s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=46, time_scale=1, start_time=0, loop=True, trans_time=0.5)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_30', None)
        obj_Char_hatcher.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 40: source 17s; allocated facial window 9s.
        t = 0
        # source event 71, 17s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake')
        # source event 72, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_TALK_000LV_A_16, duration=10, time_scale=1, start_time=1, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_40', None)
        obj_Char_mandrake.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 50: source 25.5s; allocated facial window 5s.
        t = 0
        # source event 76, 25.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_down')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_50', None)
        obj_Char_hatcher.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.0)

        # Line 60: source 29.5s; allocated facial window 6.5s.
        t = 0
        # source event 79, 29.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake')
        # source event 80, 29.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_60', None)
        obj_Char_mandrake.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.5)

        # Line 70: source 36.5s; allocated facial window 10s.
        t = 0
        # source event 84, 36.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_down')
        t += 6.5
        # source event 92, 43s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_70', None)
        obj_Char_hatcher.facial(group=MAIN, index=70, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 80: source 44s; allocated facial window 12s.
        t = 0
        # source event 88, 44s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake')
        t += 1
        # source event 93, 45s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_CONV_RHNDUP_TRNS_000LV_XA_02, duration=7, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        t += 1.5
        # source event 96, 46.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLHAND_HNEUT_GESTR_CASL_000LV_00, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 0.5
        # source event 94, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_CONV_RHND_CASL_000LV_xa_04, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 95, 50s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_CONV_RHNDDN_TRNS_000LV_XA_02, duration=4, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 97, 52s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_SHRG_SHLDRS_SMALL_000LV_XA_03, duration=7, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 3
        # source event 101, 55s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=45, axis='Y_AXIS', duration=0.01, smooth=False)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_80', None)
        obj_Char_mandrake.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 90: source 56s; allocated facial window 4.5s.
        t = 0
        # source event 98, 56s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_down')
        # source event 102, 56s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 103, 56s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=500, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_90', None)
        obj_Char_hatcher.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 100: source 60s; allocated facial window 8s.
        t = 0
        # source event 104, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher_near_mandrake_half', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 105, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher_near_mandrake', duration=1.75, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 108, 60s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 109, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_GEST_HNDS_WAIT_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 106, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_mandrake_upper', duration=3.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 107, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_mandrake', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 110, 63s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SHRG_SHLDRS_SMALL_000LV_XA_01, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        # source event 113, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_center_point1', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 114, 63s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_center_point1', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 115, 66s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_trent_lower', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 116, 66s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 117, 66s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake_trentside')
        # source event 118, 66s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=8, time_scale=0.45, start_time=0.8, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_100', None)
        obj_Char_trent.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 110: source 66.5s; allocated facial window 3s.
        t = 0
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_110', None)
        obj_Char_mandrake.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 120: source 69.5s; allocated facial window 15s.
        t = 0
        # source event 123, 69.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 124, 69.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 121, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher_near_mandrake_half', duration=3.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 122, 70s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher_near_mandrake', duration=2.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3.0
        # source event 127, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_mandrake_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 128, 73s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 129, 73.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_120', None)
        obj_Char_trent.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10.5)

        # Line 130: source 74s; allocated facial window 5s.
        t = 0
        # source event 130, 74s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=4, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_130', None)
        obj_Char_hatcher.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 140: source 77s; allocated facial window 15s.
        t = 0
        # source event 135, 77s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 136, 77s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 3.6
        # source event 133, 80.6s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_mandrake_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.4
        # source event 134, 81s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_mandrake', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.5
        # source event 140, 83.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_center_point1_btm', duration=2.8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 141, 83.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_center_point1_btm2', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 144, 83.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake_trentside')
        # source event 145, 83.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_TWSTS_FROM_090LV_XA_04, duration=8, time_scale=0.8, start_time=0.5, loop=False, trans_time=None)
        t += 1.5
        # source event 149, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_mandrake_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 150, 85s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_mandrake', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.8
        # source event 142, 85.8s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_hatcher_near_mandrake_half_btm', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_140', None)
        obj_Char_trent.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6)

        # Line 150: source 86s; allocated facial window 3s.
        t = 0
        # source event 143, 86s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_hatcher_near_mandrake', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_150', None)
        obj_Char_mandrake.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 160: source 88s; allocated facial window 10s.
        t = 0
        # source event 148, 88s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 153, 88s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 154, 88s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 151, 89s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent_mandrake_half', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 152, 89s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 155, 90s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=8, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 159, 91s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher_near_mandrake_half', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 160, 91s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher_near_mandrake', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_160', None)
        obj_Char_hatcher.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2)

        # Line 170: source 96s; allocated facial window 10s.
        t = 0
        # source event 161, 96s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 162, 96s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_02, duration=7, time_scale=1, start_time=0, loop=True, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_170', None)
        obj_Char_trent.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-6.25)

        # Line 180: source 99.75s; allocated facial window 4s.
        t = 0
        # source event 165, 99.75s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher')
        # source event 166, 99.75s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=8, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        t += 0.25
        # source event 10, 100s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript1', 'automarker_cam_hatcher_descript1_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 11, 100s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript2', 'automarker_cam_hatcher_descript2_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 12, 100s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript3', 'automarker_cam_hatcher_descript3_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 13, 100s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent_answer1', 'automarker_cam_trent_answer1_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 14, 100s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript4', 'automarker_cam_hatcher_descript4_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 475, 100s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_hall_ambient', duration=8, attenuation=-100)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_180', None)
        obj_Char_hatcher.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.75)

        # Line 190: source 103s; allocated facial window 15s.
        t = 0
        # source event 170, 103s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 171, 103s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=7, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 169, 105s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=4, time_scale=1, start_time=0, loop=False, trans_time=0.2)
        t += 1.5
        # source event 185, 106.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=1.5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.0
        # source event 183, 107.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript1')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_190', None)
        obj_Char_trent.facial(group=MAIN, index=190, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-10)

        # Line 200: source 108s; allocated facial window 14.5s.
        t = 0
        # source event 184, 108s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_XB_04, duration=30, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 186, 108s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_SHRG_SHLDRS_SMALL_000LV_XA_02, duration=4, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 476, 108s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_anticipation_light', duration=90, start_time=0, loop=True)
        t += 2
        # source event 174, 110s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=0.2)
        t += 1
        # source event 187, 111s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 190, 111s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=6, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 2
        # source event 188, 113s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=6, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 4
        # source event 191, 117s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_NEUT_RGHT_000LV_A_00, duration=2, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 1
        # source event 181, 118s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher_description3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 182, 118s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher_description3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 189, 119s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=1, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 175, 119.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_road_left', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 176, 119.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_road_left', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 199, 120s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_WALK_TRNS_090LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_200', None)
        obj_Char_hatcher.facial(group=MAIN, index=200, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 210: source 122s; allocated facial window 17s.
        t = 0
        # source event 196, 122s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript2')
        # source event 197, 122s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript2', target_name='automarker_cam_hatcher_descript2_pos2', duration=16, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 198, 122s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_descript2_marker', target_name='automarker_cam_hatcher_descript2_marker_pos2', duration=16, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 200, 122s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_WALK_STND_TRNS_000LV_XA_01, duration=2, time_scale=0.8, start_time=0.1, loop=False, trans_time=None)
        t += 1
        # source event 201, 123s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=0.5)
        t += 3
        # source event 202, 126s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=4, time_scale=0.6, start_time=0, loop=True, trans_time=0.5)
        t += 4
        # source event 177, 130s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_description3_look_left_nearest', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 178, 130s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_description3_look_left', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 203, 132s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=2, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 2
        # source event 179, 134s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 180, 134s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 204, 134s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TURN_180LV_XA_04, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 209, 137s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript3')
        # source event 210, 137s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript3', target_name='automarker_cam_hatcher_descript3_pos2', duration=16, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 211, 137s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_descript3_marker', target_name='automarker_cam_hatcher_descript3_marker_pos2', duration=16, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_210', None)
        obj_Char_hatcher.facial(group=MAIN, index=210, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 220: source 138s; allocated facial window 6.5s.
        t = 0
        # source event 212, 138s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_LHNDUP_TRNS_000LV_XA_01, duration=1.3, time_scale=0.75, start_time=0, loop=False, trans_time=0.25)
        t += 1.3
        # source event 213, 139.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_LHND_CASL_000LV_xa_04, duration=3.7, time_scale=0.5, start_time=0, loop=True, trans_time=0.1)
        t += 3.7
        # source event 214, 143s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_LHNDDN_TRNS_000LV_XA_00, duration=1.5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_220', None)
        obj_Char_hatcher.facial(group=MAIN, index=220, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 230: source 144.5s; allocated facial window 10s.
        t = 0
        # source event 218, 144.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=3.6, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 3.6
        # source event 219, 148.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_03, duration=1.4, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 1.4
        # source event 220, 149.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=8, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 0.5
        # source event 15, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript5', 'automarker_cam_hatcher_descript5_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 16, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent_answer2', 'automarker_cam_trent_answer2_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 17, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent_answer3', 'automarker_cam_trent_answer3_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 18, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_mandrake_trentwell', 'automarker_cam_mandrake_trentwell_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 19, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript6', 'automarker_cam_hatcher_descript6_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 20, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript7', 'automarker_cam_hatcher_descript7_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 21, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript8', 'automarker_cam_hatcher_descript8_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 22, 150s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript9', 'automarker_cam_hatcher_descript9_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_230', None)
        obj_Char_hatcher.facial(group=MAIN, index=230, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 240: source 154s; allocated facial window 7.5s.
        t = 0
        # source event 225, 154s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 226, 154s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_answer1', target_name='automarker_cam_trent_answer1_pos2', duration=8.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 227, 154s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer1')
        # source event 228, 154s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_IDLE_000LV_XB_04, duration=3, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 229, 157s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        t += 3
        # source event 230, 160s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_ATEASE_HOLD_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=True, trans_time=0.5)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_240', None)
        obj_Char_trent.facial(group=MAIN, index=240, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 233, 161.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=2, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        main_group.append_time(1.0)

        # Line 250: source 162.5s; allocated facial window 10s.
        t = 0
        # source event 234, 162.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript4', target_name='automarker_cam_hatcher_descript4_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 235, 162.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript4')
        # source event 236, 162.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=1, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 1.0
        # source event 237, 163.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 240, 163.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 2.0
        # source event 238, 165.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=3, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 3.0
        # source event 239, 168.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=1, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_250', None)
        obj_Char_hatcher.facial(group=MAIN, index=250, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 260: source 172.5s; allocated facial window 10s.
        t = 0
        # source event 245, 172.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer2')
        # source event 246, 172.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 2.5
        # source event 254, 175s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLHAND_HNEUT_GESTR_FIST_000LV_00, duration=4, time_scale=2, start_time=0, loop=False, trans_time=0.25)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_260', None)
        obj_Char_trent.facial(group=MAIN, index=260, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.0)

        # Line 270: source 175.5s; allocated facial window 10s.
        t = 0
        # source event 249, 175.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript5')
        # source event 250, 175.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 253, 175.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=4, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 2.0
        # source event 251, 177.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=3, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 3.0
        # source event 252, 180.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=2, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_270', None)
        obj_Char_hatcher.facial(group=MAIN, index=270, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.0)

        # Line 280: source 183.5s; allocated facial window 10s.
        t = 0
        # source event 259, 183.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript4', target_name='automarker_cam_hatcher_descript4_pos3', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 260, 183.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript4')
        # source event 261, 183.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        t += 2.5
        # source event 262, 186s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=3, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 3.0
        # source event 263, 189s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=3, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 1.0
        # source event 273, 190s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_center_point2', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 274, 190s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_center_point2', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_280', None)
        obj_Char_hatcher.facial(group=MAIN, index=280, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 290: source 193s; allocated facial window 3s.
        t = 0
        # source event 268, 193s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer3')
        # source event 269, 193s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 275, 195s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_hatcher_description3', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 276, 195s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_hatcher_description3', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 281, 195s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_mandrake_upper', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 282, 195s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_mandrake', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.7
        # source event 272, 195.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=15, time_scale=0.5, start_time=0, loop=False, trans_time=2)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_290', None)
        obj_Char_trent.facial(group=MAIN, index=290, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 277, 196s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake_trentwell')
        # source event 278, 196s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_270LV_XA_03, duration=3, time_scale=0.5, start_time=0.5, loop=False, trans_time=None)
        main_group.append_time(0.1)

        # Line 300: source 196.1s; allocated facial window 3s.
        t = 0
        t += 0.9
        # source event 477, 197s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_anticipation_light', duration=1, attenuation=-100)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_300', None)
        obj_Char_mandrake.facial(group=MAIN, index=300, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.1)

        # Line 310: source 198s; allocated facial window 10s.
        t = 0
        # source event 285, 198s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript6', target_name='automarker_cam_hatcher_descript6_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 286, 198s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_descript6_marker', target_name='automarker_cam_hatcher_descript6_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 287, 198s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript6')
        t += 1
        # source event 283, 199s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 284, 199s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 478, 199s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_reveal_and_exposition', duration=77, start_time=0, loop=True)
        t += 0.1
        # source event 293, 199.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=0.4, time_scale=0.5, start_time=0, loop=False, trans_time=0.4)
        t += 0.9
        # source event 23, 200s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_descript10', 'automarker_cam_hatcher_descript10_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 24, 200s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent_answer4', 'automarker_cam_trent_answer4_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 288, 200s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDSUP_TRNS_000LV_XA_01, duration=4, time_scale=0.5, start_time=0, loop=False, trans_time=0.25)
        t += 2
        # source event 289, 202s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDS_CASL_000LV_xa_03, duration=4, time_scale=0.5, start_time=0, loop=True, trans_time=0.5)
        t += 4
        # source event 290, 206s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_310', None)
        obj_Char_hatcher.facial(group=MAIN, index=310, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 320: source 207.5s; allocated facial window 10s.
        t = 0
        # source event 298, 207.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript7', target_name='automarker_cam_hatcher_descript7_pos2', duration=14.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 299, 207.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript7')
        # source event 300, 207.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        # source event 303, 207.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_HNEUT_GESTR_CASL_000LV_00, duration=6, time_scale=0.8, start_time=0, loop=True, trans_time=0.25)
        t += 2.0
        # source event 301, 209.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHND_CASL_000LV_xa_03, duration=6, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 4.0
        # source event 304, 213.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHAND_NEUT_RGHT_000LV_A_00, duration=2, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 2.0
        # source event 302, 215.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_01, duration=2, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_320', None)
        obj_Char_hatcher.facial(group=MAIN, index=320, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.5)

        # Line 330: source 217s; allocated facial window 5s.
        t = 0
        t += 4
        # source event 296, 221s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_description8_lookexit', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 297, 221s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_description8_lookexit', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 305, 221s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TURN_270LV_XA_03, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_330', None)
        obj_Char_hatcher.facial(group=MAIN, index=330, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 340: source 222s; allocated facial window 12s.
        t = 0
        # source event 312, 222s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript8')
        t += 2
        # source event 313, 224s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=3.6, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 3.6
        # source event 314, 227.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_HOLD_ARMS_CROSSED_000LV_XA_03, duration=1.4, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 1.4
        # source event 315, 229s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=8, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_340', None)
        obj_Char_hatcher.facial(group=MAIN, index=340, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1)

        # Line 350: source 233s; allocated facial window 7s.
        t = 0
        # source event 325, 233s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript9')
        # source event 326, 233s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_IDLE_000LV_xa_05, duration=7, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 1
        # source event 321, 234s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_description8_lookbottom_to_trent_half', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 322, 234s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_description8_lookbottom_to_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 323, 236s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_description8_lookbottom', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 324, 236s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_description8_lookbottom', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3.3
        # source event 330, 239.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMHEAD_BASEPOSE_000LV_02_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=1.2)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_350', None)
        obj_Char_hatcher.facial(group=MAIN, index=350, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 360: source 240s; allocated facial window 10s.
        t = 0
        # source event 331, 240s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer3')
        # source event 332, 240s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_SHRG_SHLDRS_SMALL_000LV_XA_01, duration=15, time_scale=0.8, start_time=0.25, loop=False, trans_time=None)
        t += 2
        # source event 335, 242s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=15, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_360', None)
        obj_Char_trent.facial(group=MAIN, index=360, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.5)

        # Line 370: source 242.5s; allocated facial window 10s.
        t = 0
        # source event 336, 242.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_description8_lookbottom_to_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 337, 242.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_description8_lookbottom_to_trent_max', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 340, 242.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_descript10', target_name='automarker_cam_hatcher_descript10_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 341, 242.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_descript10_marker', target_name='automarker_cam_hatcher_descript10_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 342, 242.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_descript10')
        # source event 343, 242.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=3, time_scale=0.4, start_time=0, loop=False, trans_time=0.5)
        t += 3.0
        # source event 338, 245.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_description8_lookbottom', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 339, 245.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_description8_lookbottom', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 344, 245.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HOLD_000LV_XA_01, duration=3, time_scale=0.6, start_time=0, loop=True, trans_time=0.5)
        t += 4.0
        # source event 345, 249.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=2, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 0.5
        # source event 25, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_angry01', 'automarker_cam_hatcher_angry01_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 26, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_angry02', 'automarker_cam_hatcher_angry02_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 27, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_objective01', 'automarker_cam_hatcher_objective01_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 28, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_mandrake_objective01', 'automarker_cam_mandrake_objective01_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 29, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_mandrake_objective02', 'automarker_cam_mandrake_objective02_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 30, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_objective02', 'automarker_cam_hatcher_objective02_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 31, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_hatcher_objective03', 'automarker_cam_hatcher_objective03_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 32, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent_final', 'automarker_cam_trent_final_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 33, 250s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_final', 'automarker_cam_final_marker'], duration=100, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        t += 2.0
        # source event 350, 252s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer4')
        # source event 351, 252s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_370', None)
        obj_Char_hatcher.facial(group=MAIN, index=370, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0.0)

        # Line 380: source 252.5s; allocated facial window 10s.
        t = 0
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_380', None)
        obj_Char_trent.facial(group=MAIN, index=380, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.0)

        # Line 390: source 255.5s; allocated facial window 14.3s.
        t = 0
        # source event 354, 255.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 355, 255.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 356, 255.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_angry01', target_name='automarker_cam_hatcher_angry01_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 357, 255.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_angry01_marker', target_name='automarker_cam_hatcher_angry01_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 359, 255.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_angry01')
        # source event 360, 255.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_STEP_TRNS_090LV_XA_04, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 4.5
        # source event 361, 260s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=2, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1.5
        # source event 358, 261.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_angry01', target_name='automarker_cam_hatcher_angry01_pos3', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 362, 262.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=3, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 2.0
        # source event 363, 264.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_EMPH_HNDSUP_TRNS_000LV_XA_01, duration=1.5, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1.5
        # source event 364, 266s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_EMPH_HNDSDN_TRNS_000LV_XA_01, duration=2, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 1.7
        # source event 370, 267.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_hatcher_angry02', target_name='automarker_cam_hatcher_angry02_pos2', duration=6.3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 371, 267.7s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_hatcher_angry02_marker', target_name='automarker_cam_hatcher_angry02_marker_pos2', duration=6.3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 372, 267.7s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_angry02')
        # source event 373, 267.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_CROSS_ARMS_000LV_xa_03, duration=4, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_390', None)
        obj_Char_hatcher.facial(group=MAIN, index=390, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.8)

        # Line 400: source 268s; allocated facial window 6s.
        t = 0
        t += 5
        # source event 479, 273s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_reveal_and_exposition', duration=3, attenuation=-25)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_400', None)
        obj_Char_hatcher.facial(group=MAIN, index=400, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(0)

        # Line 410: source 274s; allocated facial window 10s.
        t = 0
        # source event 376, 274s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer4')
        # source event 377, 274s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_UNCRSS_ARMS_000LV_XA_02, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_410', None)
        obj_Char_trent.facial(group=MAIN, index=410, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8)

        # Line 420: source 276s; allocated facial window 4s.
        t = 0
        # source event 380, 276s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_angry02')
        # source event 382, 276s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_UNCRSS_ARMS_000LV_XA_03, duration=5, time_scale=1, start_time=0.75, loop=False, trans_time=None)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_420', None)
        obj_Char_hatcher.facial(group=MAIN, index=420, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 430: source 277.5s; allocated facial window 10s.
        t = 0
        # source event 384, 277.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_answer4')
        t += 1.0
        # source event 387, 278.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_430', None)
        obj_Char_trent.facial(group=MAIN, index=430, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.5)

        # Line 440: source 279s; allocated facial window 4s.
        t = 0
        # source event 388, 279s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_mandrake_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 389, 279s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_mandrake', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 390, 279s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_hatcher_near_mandrake', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 391, 279s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_hatcher_near_mandrake', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 392, 279s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_objective01')
        # source event 393, 279s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TURN_090LV_XA_03, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 394, 279s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', angle=20, axis='Y_AXIS', duration=2, smooth=False)
        # source event 480, 279s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_reveal_special_mystery', duration=31, start_time=0, loop=True)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_440', None)
        obj_Char_hatcher.facial(group=MAIN, index=440, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 397, 283s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake_objective01')
        # source event 398, 283s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_CHRB_SHRG_SHLDRS_SMALL_000LV_XA_03, duration=7, time_scale=0.7, start_time=0.5, loop=False, trans_time=None)
        main_group.append_time(0.5)

        # Line 450: source 283.5s; allocated facial window 3s.
        t = 0
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_450', None)
        obj_Char_mandrake.facial(group=MAIN, index=450, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 460: source 284.8s; allocated facial window 4s.
        t = 0
        # source event 401, 284.8s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_objective01')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_460', None)
        obj_Char_hatcher.facial(group=MAIN, index=460, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.8)

        # Line 470: source 287s; allocated facial window 11.3s.
        t = 0
        # source event 412, 287s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_mandrake_objective02')
        t += 1
        # source event 408, 288s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_mandrake_objective02', target_name='automarker_cam_mandrake_objective02_pos2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 409, 288s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_mandrake_objective02_marker', target_name='automarker_cam_mandrake_objective02_marker_pos2', duration=4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 413, 289s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_2STEP_FRWD_TRNS_000LV_XA_02, duration=1.5, time_scale=0.5, start_time=1.5, loop=False, trans_time=1.5)
        t += 2.2
        # source event 414, 291.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_EMPH_HNDSUP_TRNS_000LV_XA_00, duration=1, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 0.8
        # source event 410, 292s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_mandrake_objective02', target_name='automarker_cam_mandrake_objective02_pos3', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 411, 292s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_mandrake_objective02_marker', target_name='automarker_cam_mandrake_objective02_marker_pos3', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 415, 292s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_CONV_HNDS_EMPH_000LV_XC_01, duration=1, time_scale=0.8, start_time=0, loop=True, trans_time=0.5)
        t += 1
        # source event 416, 293s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_EMPH_HNDSDN_TRNS_000LV_XA_00, duration=3, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 2
        # source event 404, 295s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_trent_mandrakes_look', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 405, 295s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_trent_mandrakes_look_far', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 417, 295s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01, duration=2, time_scale=0.8, start_time=0, loop=False, trans_time=0.5)
        t += 2
        # source event 406, 297s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_hatcher_near_mandrake', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 407, 297s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_hatcher_near_mandrake', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 418, 297.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_FSTHIPB_RLEASE_000LV_XA_01, duration=2, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_470', None)
        obj_Char_mandrake.facial(group=MAIN, index=470, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 425, 298.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=1, time_scale=1.5, start_time=0, loop=False, trans_time=0.2)
        t += 0.2
        # source event 426, 298.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_mandrake_stand', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 427, 298.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_mandrake_stand', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 431, 299s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_mandrake_stand', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 432, 299s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_mandrake_stand', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(1.2)

        # Line 480: source 299.5s; allocated facial window 10s.
        t = 0
        # source event 428, 299.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        t += 0.5
        # source event 433, 300s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 434, 300s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 435, 300.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_TURN_315LV_XA_03, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 436, 301s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', angle=-10, axis='Y_AXIS', duration=1, smooth=False)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_480', None)
        obj_Char_trent.facial(group=MAIN, index=480, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8.0)

        # Line 490: source 301.5s; allocated facial window 3s.
        t = 0
        # source event 437, 301.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_objective02')
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_490', None)
        obj_Char_hatcher.facial(group=MAIN, index=490, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.5)

        # Line 500: source 303s; allocated facial window 10s.
        t = 0
        # source event 440, 303s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_hatcher_description3', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 441, 303s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_hatcher_description3', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 442, 303s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_final')
        t += 2.5
        # source event 445, 305.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Trent.Sc_MLHEAD_BASEPOSE_TRENT_000LV_01_01, duration=1, time_scale=1, start_time=0, loop=False, trans_time=1)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_500', None)
        obj_Char_trent.facial(group=MAIN, index=500, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7)

        # Line 510: source 306s; allocated facial window 4s.
        t = 0
        # source event 446, 306s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_hatcher_objective02')
        t += 3.9999
        # source event 449, 310s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', angle=25, axis='Y_AXIS', duration=1e-05, smooth=False)
        select_dialogue(self, 5, 'Msn5Equip', 'm05_equip')
        self.groups.pop('motion_510', None)
        obj_Char_hatcher.facial(group=MAIN, index=510, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 450, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_head_ik', target_name='automarker_head_hatcher_exitpoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 451, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_hatcher_eye_ik', target_name='automarker_head_hatcher_exitpoint', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 452, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_trent_final_exitpoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 453, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_trent_final_exitpoint', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 454, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_head_ik', target_name='automarker_head_mandrake_exipoint', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 455, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_mandrake_eye_ik', target_name='automarker_head_mandrake_exipoint', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 456, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_final', target_name='automarker_cam_final_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 457, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_final_marker', target_name='automarker_cam_final_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 458, 310s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_final')
        # source event 459, 310s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Prop_Maglev', target_name='automarker_maglev_pos2', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 460, 310s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 464, 310s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_STND_WALK_TRNS_270LV_XA_02, duration=2.35, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 481, 310s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_reveal_special_mystery', duration=0.001, attenuation=-5)
        # source event 482, 310s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_reveal_special_mystery', duration=10000, start_time=16500, loop=False)
        t += 1
        # source event 462, 311s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 461, 312s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=51, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.09
        # source event 463, 312.09s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_mandrake', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=51, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.26
        # source event 465, 312.35s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_hatcher', anim=Female.Sc_FMBODY_WLKG_000LV_XA_01, duration=21, time_scale=1, start_time=0, loop=True, trans_time=None)
        main_group.append_time(10.0)
        restore_dialogue(self)
