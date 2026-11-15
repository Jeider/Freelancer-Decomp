"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_doors(Prop):
    COMPOUND_TEMPLATE_NAME = 'prison_doors'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_cigarette(Prop):
    COMPOUND_TEMPLATE_NAME = 'cigarette_3'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_case1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_case'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_panel1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_panel'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_case2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_case'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_panel2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_panel'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_body1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_pirate_body1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_body2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_pirate_body2'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_body3(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_pirate_body1'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_mask_trent(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_neck_bomb'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_mask_pris1(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_neck_bomb'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_mask_pris2(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_neck_bomb'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_mask_pris3(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_neck_bomb'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_mask_pris4(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_neck_bomb'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_prop_mask_pris5(Prop):
    COMPOUND_TEMPLATE_NAME = 'm6_prison_neck_bomb'
    SRT_GRP = 0
    USR_FLG = 0


class Actor_obj_Char_prisoner1(actors.Actor):
    NAME = 'prisoner1'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner04'
    GAME_ACTOR = 'Prisoner1'


class Actor_obj_Char_prisoner2(actors.Actor):
    NAME = 'prisoner2'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner02'
    GAME_ACTOR = 'Prisoner2'


class Actor_obj_Char_trent_classic(actors.Actor):
    NAME = 'trent_classic'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'trent_original'
    GAME_ACTOR = 'TrentOriginal'


class Actor_obj_Char_prisoner1b(actors.Actor):
    NAME = 'prisoner1b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner01b'
    GAME_ACTOR = 'Prisoner1b'


class Actor_obj_Char_prisoner2b(actors.Actor):
    NAME = 'prisoner2b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner02b'
    GAME_ACTOR = 'Prisoner2b'


class Actor_obj_Char_prisoner3b(actors.Actor):
    NAME = 'prisoner3b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner03b'
    GAME_ACTOR = 'Prisoner3b'


class Actor_obj_Char_prisoner4b(actors.Actor):
    NAME = 'prisoner4b'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'm06_asf_prisoner04b'
    GAME_ACTOR = 'Prisoner4b'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_prison_new'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_doors = Asset_obj_doors(root=self, name='doors', light_group=9, init_point='doors', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_doors, {'template_name': 'prison_doors', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_cigarette = Asset_obj_prop_cigarette(root=self, name='prop_cigarette', light_group=9, init_point='prop_cigarette', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_cigarette, {'template_name': 'cigarette_3', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_vfx_rtc_cigaretteglow_4 = Alchemy(root=self, name='vfx_rtc_cigaretteglow_4', particles='rtc_cigaretteglow', point_name='vfx_rtc_cigaretteglow_4', sparam=0)
        preserve_entity(obj_vfx_rtc_cigaretteglow_4, {'template_name': 'rtc_cigaretteglow', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_vfx_rtc_sydsmoke_3 = Alchemy(root=self, name='vfx_rtc_sydsmoke_3', particles='rtc_sydsmoke', point_name='vfx_rtc_sydsmoke_3', sparam=0)
        preserve_entity(obj_vfx_rtc_sydsmoke_3, {'template_name': 'rtc_sydsmoke', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'psysprops': {'sparam': 0}})
        obj_case1 = Asset_obj_case1(root=self, name='case1', light_group=9, init_point='case1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_case1, {'template_name': 'm6_prison_case', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_panel1 = Asset_obj_panel1(root=self, name='panel1', light_group=9, init_point='panel1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_panel1, {'template_name': 'm6_prison_panel', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_case2 = Asset_obj_case2(root=self, name='case2', light_group=9, init_point='case2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_case2, {'template_name': 'm6_prison_case', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_panel2 = Asset_obj_panel2(root=self, name='panel2', light_group=9, init_point='panel2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_panel2, {'template_name': 'm6_prison_panel', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_body1 = Asset_obj_body1(root=self, name='body1', light_group=9, init_point='body1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_body1, {'template_name': 'm6_prison_pirate_body1', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_body2 = Asset_obj_body2(root=self, name='body2', light_group=9, init_point='body2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_body2, {'template_name': 'm6_prison_pirate_body2', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_body3 = Asset_obj_body3(root=self, name='body3', light_group=9, init_point='body3', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_body3, {'template_name': 'm6_prison_pirate_body1', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_mask_trent = Asset_obj_prop_mask_trent(root=self, name='prop_mask_trent', light_group=9, init_point='prop_mask_trent', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_mask_trent, {'template_name': 'm6_prison_neck_bomb', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_mask_pris1 = Asset_obj_prop_mask_pris1(root=self, name='prop_mask_pris1', light_group=9, init_point='prop_mask_pris1', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_mask_pris1, {'template_name': 'm6_prison_neck_bomb', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_mask_pris2 = Asset_obj_prop_mask_pris2(root=self, name='prop_mask_pris2', light_group=9, init_point='prop_mask_pris2', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_mask_pris2, {'template_name': 'm6_prison_neck_bomb', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_mask_pris3 = Asset_obj_prop_mask_pris3(root=self, name='prop_mask_pris3', light_group=9, init_point='prop_mask_pris3', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_mask_pris3, {'template_name': 'm6_prison_neck_bomb', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_mask_pris4 = Asset_obj_prop_mask_pris4(root=self, name='prop_mask_pris4', light_group=9, init_point='prop_mask_pris4', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_mask_pris4, {'template_name': 'm6_prison_neck_bomb', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_prop_mask_pris5 = Asset_obj_prop_mask_pris5(root=self, name='prop_mask_pris5', light_group=9, init_point='prop_mask_pris5', rotate_from_quat=True, use_ambient=False)
        preserve_entity(obj_prop_mask_pris5, {'template_name': 'm6_prison_neck_bomb', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'userprops': {'category': 'Prop'}})
        obj_ambience_hall = Sound(root=self, name='ambience_hall', sound='ambience_deck_space_smaller', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_ambience_hall, {'template_name': 'ambience_deck_space_smaller', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_ambience_room = Sound(root=self, name='ambience_room', sound='ambience_deck_space_larger', attenuation=-1000000, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_ambience_room, {'template_name': 'ambience_deck_space_larger', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -1000000, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step1 = Sound(root=self, name='step1', sound='fs_ml_steel04', attenuation=-45, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step1, {'template_name': 'fs_ml_steel04', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -45, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step2 = Sound(root=self, name='step2', sound='fs_ml_steel01', attenuation=-45, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step2, {'template_name': 'fs_ml_steel01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -45, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step3 = Sound(root=self, name='step3', sound='fs_ml_steel03', attenuation=-45, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step3, {'template_name': 'fs_ml_steel03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -45, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step1_cmdr = Sound(root=self, name='step1_cmdr', sound='fs_ml_steel04', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step1_cmdr, {'template_name': 'fs_ml_steel04', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step2_cmdr = Sound(root=self, name='step2_cmdr', sound='fs_ml_steel01', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step2_cmdr, {'template_name': 'fs_ml_steel01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_step3_cmdr = Sound(root=self, name='step3_cmdr', sound='fs_ml_steel03', attenuation=-20, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_step3_cmdr, {'template_name': 'fs_ml_steel03', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -20, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_snd_open_door = Sound(root=self, name='snd_open_door', sound='depot_open_sound', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_snd_open_door, {'template_name': 'depot_open_sound', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_snd_close_door = Sound(root=self, name='snd_close_door', sound='depot_close_sound', attenuation=0, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_snd_close_door, {'template_name': 'depot_close_sound', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': 0, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_snd_close_door_clothesbox = Sound(root=self, name='snd_close_door_clothesbox', sound='depot_close_sound', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_snd_close_door_clothesbox, {'template_name': 'depot_close_sound', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_Char_prisoner1 = Character(root=self, actor=Actor_obj_Char_prisoner1, light_group=9, init_point='Char_prisoner1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner1, {'template_name': 'm06_asf_prisoner04', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner1', 'category': 'Character'}})
        obj_Char_prisoner2 = Character(root=self, actor=Actor_obj_Char_prisoner2, light_group=9, init_point='Char_prisoner2', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner2, {'template_name': 'm06_asf_prisoner02', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner2', 'category': 'Character'}})
        obj_Char_prisoner3 = Character(root=self, actor=actors.DeltaThree, light_group=9, init_point='Char_delta3', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner3, {'template_name': 'm06_asf_prisoner03', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner3', 'category': 'Character'}})
        obj_Char_prisoner4 = Character(root=self, actor=actors.DeltaOne, light_group=9, init_point='Char_delta1', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner4, {'template_name': 'm06_asf_prisoner01', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner4', 'category': 'Character'}})
        obj_Char_commander = Character(root=self, actor=actors.OrderGuard, light_group=9, init_point='Char_guard', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_commander, {'template_name': 'm06_gunner_leader', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Gunner_commander', 'category': 'Character'}})
        obj_Char_syd = Character(root=self, actor=actors.Ceed, light_group=9, init_point='Char_syd', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_syd, {'template_name': 'syd', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Syd', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=9, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_Char_trent_classic = Character(root=self, actor=Actor_obj_Char_trent_classic, light_group=9, init_point='Char_trent_classic', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent_classic, {'template_name': 'trent_original', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'TrentOriginal', 'category': 'Character'}})
        obj_Char_prisoner1b = Character(root=self, actor=Actor_obj_Char_prisoner1b, light_group=9, init_point='Char_prisoner1b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner1b, {'template_name': 'm06_asf_prisoner01b', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner1b', 'category': 'Character'}})
        obj_Char_prisoner2b = Character(root=self, actor=Actor_obj_Char_prisoner2b, light_group=9, init_point='Char_prisoner2b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner2b, {'template_name': 'm06_asf_prisoner02b', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner2b', 'category': 'Character'}})
        obj_Char_prisoner3b = Character(root=self, actor=Actor_obj_Char_prisoner3b, light_group=9, init_point='Char_prisoner3b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner3b, {'template_name': 'm06_asf_prisoner03b', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner3b', 'category': 'Character'}})
        obj_Char_prisoner4b = Character(root=self, actor=Actor_obj_Char_prisoner4b, light_group=9, init_point='Char_prisoner4b', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_prisoner4b, {'template_name': 'm06_asf_prisoner04b', 'lt_grp': 9, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Prisoner4b', 'category': 'Character'}})
        obj_cam_start_outside = LookAtCamera(root=self, name='cam_start_outside', fov=35, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start_outside, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 35, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_start_inside = LookAtCamera(root=self, name='cam_start_inside', fov=30, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start_inside, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 30, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_appear = LookAtCamera(root=self, name='cam_syd_appear', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_syd_appear, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_salut = LookAtCamera(root=self, name='cam_salut', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_salut, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_gives_order = LookAtCamera(root=self, name='cam_syd_gives_order', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_syd_gives_order, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_order = LookAtCamera(root=self, name='cam_syd_order', fov=25, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_syd_order, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 25, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_opendoor = StaticCamera(root=self, name='cam_syd_opendoor', fov=20, farplane=5000)
        preserve_entity(obj_cam_syd_opendoor, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_doorclosed = StaticCamera(root=self, name='cam_syd_doorclosed', fov=15, farplane=5000)
        preserve_entity(obj_cam_syd_doorclosed, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_sydgreet_begin = StaticCamera(root=self, name='cam_sydgreet_begin', fov=15, farplane=5000)
        preserve_entity(obj_cam_sydgreet_begin, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_sydgreet_captapprove = StaticCamera(root=self, name='cam_sydgreet_captapprove', fov=15, farplane=5000)
        preserve_entity(obj_cam_sydgreet_captapprove, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_reveal = StaticCamera(root=self, name='cam_syd_reveal', fov=15, farplane=5000)
        preserve_entity(obj_cam_syd_reveal, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent = StaticCamera(root=self, name='cam_trent', fov=15, farplane=5000)
        preserve_entity(obj_cam_trent, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_trentside = StaticCamera(root=self, name='cam_syd_trentside', fov=15, farplane=5000)
        preserve_entity(obj_cam_syd_trentside, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_captain_sydanswer = StaticCamera(root=self, name='cam_captain_sydanswer', fov=15, farplane=5000)
        preserve_entity(obj_cam_captain_sydanswer, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_captside = StaticCamera(root=self, name='cam_syd_captside', fov=16, farplane=5000)
        preserve_entity(obj_cam_syd_captside, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 16, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_syd_clothesbox = StaticCamera(root=self, name='cam_syd_clothesbox', fov=15, farplane=5000)
        preserve_entity(obj_cam_syd_clothesbox, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_delta3 = StaticCamera(root=self, name='cam_delta3', fov=15, farplane=5000)
        preserve_entity(obj_cam_delta3, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_delta1 = StaticCamera(root=self, name='cam_delta1', fov=15, farplane=5000)
        preserve_entity(obj_cam_delta1, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_trent_finalword = StaticCamera(root=self, name='cam_trent_finalword', fov=15, farplane=5000)
        preserve_entity(obj_cam_trent_finalword, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 15, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_exit = StaticCamera(root=self, name='cam_exit', fov=20, farplane=5000)
        preserve_entity(obj_cam_exit, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 21, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_mask_trent', parent_name='Char_trent', duration=1000, target_hardpoint='hp_neck_connect', parent_hardpoint='hp_head_top_conn')
        # source event 22, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_mask_pris1', parent_name='Char_prisoner1', duration=1000, target_hardpoint='hp_neck_connect', parent_hardpoint='hp_head_top_conn')
        # source event 23, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_mask_pris2', parent_name='Char_prisoner2', duration=1000, target_hardpoint='hp_neck_connect', parent_hardpoint='hp_head_top_conn')
        # source event 24, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_mask_pris3', parent_name='Char_delta3', duration=1000, target_hardpoint='hp_neck_connect', parent_hardpoint='hp_head_top_conn')
        # source event 25, 0s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_mask_pris4', parent_name='Char_delta1', duration=1000, target_hardpoint='hp_neck_connect', parent_hardpoint='hp_head_top_conn')
        # source event 26, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_hall', duration=5000, start_time=0, loop=True)
        # source event 27, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_room', duration=5000, start_time=0, loop=True)
        # source event 86, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_outside')
        # source event 87, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start_outside', target_name='automarker_cam_start_outside_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 88, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_outside_focus', target_name='automarker_cam_start_outside_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 95, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_STRCH_YAWN_000LV_XA_06, duration=11, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 9.9
        # source event 28, 9.9s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_hall', duration=0.1, attenuation=-100)
        t += 0.1
        # source event 29, 10s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_room', duration=0.1, attenuation=0)
        # source event 89, 10s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start_inside')
        # source event 90, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start_inside', target_name='automarker_cam_start_inside_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 91, 10s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_inside_focus', target_name='automarker_cam_start_inside_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 98, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta3', anim=Male.Sc_MLBODY_CHRB_TWSTU_CCL_LESS_000LV_A_14, duration=20, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 99, 10s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_HEAD_HOLDR_000LV_XA_03, duration=20, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 4
        # source event 96, 14s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_LOOK_AROU_CASL_000LV_XA_04, duration=20, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 97, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_CHRB_IDLE_BIG_000LV_XA_05, duration=20, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 101, 16s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_CHRB_LOOK_AROU_CASL_000LV_XA_04, duration=20, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 100, 17s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_HOLD_HEAD_RLEASE_000LV_XA_03, duration=20, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 4
        # source event 102, 21s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_BEND_FOTR_SWNGARMS_000DN_XA_12, duration=11, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 0.9
        # source event 30, 21.9s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_hall', duration=0.1, attenuation=0)
        t += 0.1
        # source event 31, 22s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_room', duration=0.1, attenuation=-100)
        # source event 92, 22s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_appear')
        # source event 93, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd_appear', target_name='automarker_cam_syd_appear_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 94, 22s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_syd_appear_focus', target_name='automarker_cam_syd_appear_marker_pos2', duration=6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 103, 22s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=7.9999, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.7
        # source event 33, 22.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 47, 23s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=3, attenuation=-15)
        # source event 48, 23s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=3, attenuation=-15)
        # source event 49, 23s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=3, attenuation=-15)
        t += 0.4
        # source event 34, 23.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 104, 24s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', angle=-15, axis='Y_AXIS', duration=5.99, smooth=True)
        t += 0.1
        # source event 35, 24.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 36, 24.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 37, 25.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 38, 26.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 39, 26.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 40, 27.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 41, 27.9s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.1
        # source event 50, 28s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=3, attenuation=-30)
        # source event 51, 28s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=3, attenuation=-30)
        # source event 52, 28s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=3, attenuation=-30)
        # source event 108, 28s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_TURN_270LV_XA_04, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.6
        # source event 42, 28.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.65
        # source event 110, 29.25s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLHEAD_SURPRSE_000LV_XA_, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 0.05
        # source event 43, 29.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 44, 30s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        # source event 105, 30s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_order')
        # source event 106, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd_order', target_name='automarker_cam_syd_order_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 107, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_syd_order_focus', target_name='automarker_cam_syd_order_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 111, 30s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', target_name='automarker_point_syd_around_commander', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.01
        # source event 112, 30.01s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=6, time_scale=0.85, start_time=0, loop=False, trans_time=None)
        t += 0.69
        # source event 45, 30.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 109, 31s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_SALUT_000LV_XA_03, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 0.4
        # source event 46, 31.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        main_group.append_time(32)

        # Line 10: source 32s; allocated facial window 9.1s.
        t = 0
        # source event 32, 32s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_hall', duration=0.1, attenuation=-2)
        t += 1
        # source event 113, 33s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_GESTR_180LV_XA_02, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 2
        # source event 53, 35s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=3, attenuation=-20)
        # source event 54, 35s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=3, attenuation=-20)
        # source event 55, 35s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=3, attenuation=-20)
        t += 2
        # source event 114, 37s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=6, time_scale=0.54, start_time=0, loop=False, trans_time=1)
        t += 3.5
        # source event 115, 40.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_CONV_HNDS_CASL_000LV_xa_04, duration=3, time_scale=0.8, start_time=0, loop=False, trans_time=2)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_10', None)
        obj_Char_syd.facial(group=MAIN, index=10, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.1)

        # Line 20: source 41s; allocated facial window 4.5s.
        t = 0
        # source event 131, 41s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_salut')
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_20', None)
        obj_Char_commander.facial(group=MAIN, index=20, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.5)

        # Line 30: source 43s; allocated facial window 7.25s.
        t = 0
        # source event 135, 43s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_gives_order')
        t += 1
        # source event 117, 44s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_ATEASE_RLEASE_000LV_XA_01, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 116, 44.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_CONV_HNDSDN_TRNS_000LV_XA_01, duration=4, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 140, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_salut', target_name='automarker_cam_salut_pos2', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 142, 46s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_salut_focus', target_name='automarker_cam_salut_marker_pos2', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 124, 47s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=3, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 1
        # source event 118, 48s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_SALUT_000LV_XA_03, duration=5, time_scale=1.3, start_time=0, loop=False, trans_time=0.25)
        # source event 139, 48s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_salut')
        # source event 141, 48s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_salut', target_name='automarker_cam_salut_pos3', duration=12, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 143, 48s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_salut_focus', target_name='automarker_cam_salut_marker_pos3', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_30', None)
        obj_Char_syd.facial(group=MAIN, index=30, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.75)

        # Line 40: source 48.5s; allocated facial window 4s.
        t = 0
        t += 0.5
        # source event 322, 49s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_syd_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.0
        # source event 125, 50s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_1STEP_BKWD_PVOTL_270LV_XA_06, duration=6, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 121, 50.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', angle=-25, axis='Y_AXIS', duration=1, smooth=True)
        t += 0.2
        # source event 119, 50.7s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 0.8
        # source event 122, 51.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', angle=25, axis='Y_AXIS', duration=2, smooth=True)
        t += 0.2
        # source event 56, 51.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, start_time=0, loop=False)
        t += 0.05
        # source event 120, 51.75s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=55, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.65
        # source event 57, 52.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2_cmdr', duration=5, start_time=0, loop=False)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_40', None)
        obj_Char_commander.facial(group=MAIN, index=40, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.5
        # source event 70, 53s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, attenuation=-50)
        # source event 71, 53s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step2_cmdr', duration=5, attenuation=-50)
        # source event 72, 53s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, attenuation=-50)
        t += 0.1
        # source event 58, 53.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.4
        # source event 123, 53.5s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_guard', angle=90, axis='Y_AXIS', duration=2.5, smooth=True)
        t += 0.3
        # source event 59, 53.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2_cmdr', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 60, 54.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 61, 55.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 126, 55.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=5, time_scale=1, start_time=0, loop=False, trans_time=0.25)
        t += 0.2
        # source event 62, 55.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 63, 56.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2_cmdr', duration=5, start_time=0, loop=False)
        t += 0.25
        # source event 127, 56.55s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3.4499, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.15
        # source event 73, 56.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 64, 56.9s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 74, 57.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 65, 57.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1_cmdr', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 75, 58.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 66, 58.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 76, 58.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 67, 59s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2_cmdr', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 77, 59.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 68, 59.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 7, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_syd_opendoor', 'automarker_cam_syd_opendoor_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 8, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_syd_doorclosed', 'automarker_cam_syd_doorclosed_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 9, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_sydgreet_begin', 'automarker_cam_sydgreet_begin_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 10, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_sydgreet_captapprove', 'automarker_cam_sydgreet_captapprove_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 11, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_syd_reveal', 'automarker_cam_syd_reveal_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 12, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent', 'automarker_cam_trent_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 13, 60s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_syd_trentside', 'automarker_cam_syd_trentside_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 146, 60s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_opendoor')
        # source event 147, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd_opendoor', target_name='automarker_cam_syd_opendoor_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 148, 60s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', target_name='automarker_point_syd_walk_to_doors', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 149, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=3, time_scale=1, start_time=0.9, loop=True, trans_time=None)
        # source event 151, 60s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', angle=-45, axis='Y_AXIS', duration=1, smooth=True)
        # source event 162, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 163, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 164, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta3', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 165, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 166, 60s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=2, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.2
        # source event 78, 60.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 69, 60.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3_cmdr', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 79, 60.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 80, 61.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 81, 61.9s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 82, 62.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step1', duration=5, start_time=0, loop=False)
        t += 0.4
        # source event 150, 63s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 152, 63s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', angle=-45, axis='Y_AXIS', duration=2, smooth=True)
        t += 0.3
        # source event 83, 63.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 84, 64s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 85, 64.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='step3', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 153, 65.3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_WAVE_LHND_000LV_XA_02, duration=8, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 1.7
        # source event 159, 67s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_open_door', duration=10, start_time=0, loop=False)
        t += 0.2
        # source event 173, 67.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 0.1
        # source event 157, 67.3s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['doors'], animation='Sc_cv_prison_cell', duration=3.332, time_scale=1, weight=1, trans_scale=1)
        t += 0.2
        # source event 174, 67.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 0.3
        # source event 175, 67.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_270LV_XA_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=None)
        t += 0.2
        # source event 154, 68s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_WALK_TRNS_000LV_XA_01, duration=4, time_scale=1, start_time=0, loop=False, trans_time=1)
        # source event 167, 68s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner1', target_name='Char_syd', duration=6, transition_duration=3, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 171, 68s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner2', target_name='automarker_prisoner2_head_ik', duration=20, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 172, 68s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner2', target_name='automarker_prisoner2_eye_ik', duration=20, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 176, 68s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_270LV_XA_03, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=None)
        # source event 188, 68s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner2', target_name='automarker_prisoner2_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 169, 68.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_syd', duration=10, transition_duration=4, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 170, 68.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='Char_syd', duration=5, transition_duration=2.5, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 168, 69s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta3', target_name='Char_syd', duration=6, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.12
        # source event 155, 69.12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1.48
        # source event 158, 70.6s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['doors'], animation='Sc_cv_prison_cell', duration=3.332, start_time=3.332, time_scale=1, weight=1, trans_scale=1)
        # source event 160, 70.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_close_door', duration=10, start_time=0, loop=False)
        t += 0.9
        # source event 156, 71.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_LOOK_AROU_CASL_000LV_XA_08, duration=8, time_scale=1, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 161, 72s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_close_door', duration=0.1, attenuation=-2)
        # source event 178, 72s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_hall', duration=2, attenuation=-100)
        # source event 179, 72s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_room', duration=2, attenuation=0)
        # source event 180, 72s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_sydgreet_begin')
        # source event 181, 72s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_sydgreet_begin', target_name='automarker_cam_sydgreet_begin_pos2', duration=5.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 182, 72s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_sydgreet_begin_marker', target_name='automarker_cam_sydgreet_begin_marker_pos2', duration=5.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1.5
        # source event 183, 73.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_asf_captain_p2_near', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 184, 73.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_asf_captain', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.5
        # source event 177, 74s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_CHRB_TWSTS_FROM_270LV_XA_03, duration=2.5, time_scale=0.2, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 195, 75.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_CHRB_IDLE_BIG_000LV_XA_05, duration=2, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 0.5
        # source event 198, 76s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta3', anim=Male.Sc_MLBODY_CHRB_TWSTU_CCL_LESS_000LV_A_14, duration=8, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 196, 76.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_CHRB_SHRG_SHLDRS_SMALL_000LV_XA_03, duration=11, time_scale=0.4, start_time=0, loop=False, trans_time=1)
        t += 0.5
        # source event 187, 77s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner2', target_name='automarker_prisoner2_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 189, 77.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_sydgreet_captapprove')
        # source event 190, 77.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=1, time_scale=1, start_time=2, loop=False, trans_time=None)
        t += 0.5
        # source event 191, 78s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_YESS_000LV_A_01, duration=4, time_scale=0.6, start_time=0, loop=False, trans_time=0.25)
        t += 0.1
        # source event 192, 78.1s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=1, time_scale=0.3, start_time=0, loop=False, trans_time=0.25)
        main_group.append_time(27.5)

        # Line 50: source 80s; allocated facial window 8.6s.
        t = 0
        # source event 17, 80s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_delta3', 'automarker_cam_delta3_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 18, 80s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_delta1', 'automarker_cam_delta1_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 185, 80s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_asf_captain_p2_near', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 186, 80s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_asf_captain', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 193, 80s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        # source event 194, 80s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLHEAD_SURPRSE_QUZZCLLY_000LV_XA_, duration=1, time_scale=0.8, start_time=0, loop=False, trans_time=0.25)
        # source event 199, 80s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='Char_syd', duration=10, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 200, 80s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta3', target_name='Char_syd', duration=10, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 202, 80s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_head_ik', duration=11.8, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 203, 80s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_eye_ik', duration=11.8, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 206, 80s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_prisoner2', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 207, 80s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_prisoner2', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 223, 80s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['vfx_rtc_sydsmoke_3', 'prop_cigarette'], duration=110, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hp_cigarette_tip_smoke', target_type='HARDPOINT', flags='POSITION')
        # source event 224, 80s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['vfx_rtc_cigaretteglow_4', 'prop_cigarette'], duration=110, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='hp_cigarette_tip_smoke', target_type='HARDPOINT', flags='POSITION+ORIENTATION')
        # source event 225, 80s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_GESTR_NO_000LV_XA_02, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 0.5
        # source event 197, 80.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=1)
        # source event 201, 80.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner1', target_name='Char_syd', duration=10, transition_duration=2, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.5
        # source event 220, 82s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_reveal')
        # source event 221, 82s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd_reveal', target_name='automarker_cam_syd_reveal_pos2', duration=18, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 222, 82s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_syd_reveal_marker', target_name='automarker_cam_syd_reveal_marker_pos2', duration=18, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 208, 83s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 209, 83s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 226, 84s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_ATEASE_HSEC_RLEASE_000LV_XA_03, duration=5, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 210, 87s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_last_prisoner', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 211, 87s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_last_prisoner', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_50', None)
        obj_Char_syd.facial(group=MAIN, index=50, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-0.6)

        # Line 60: source 88s; allocated facial window 8.5s.
        t = 0
        t += 1
        # source event 212, 89s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_syd_front', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 213, 89s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_syd_front', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 227, 89s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_ATEASE_RLEASE_000LV_XA_01, duration=5, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        t += 2.8
        # source event 228, 91.8s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_GIVE_VEND_000LV_B_07, duration=5, time_scale=0.5, start_time=0, loop=False, trans_time=0.5)
        t += 1.2
        # source event 235, 93s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='vfx_rtc_cigaretteglow_4', duration=106)
        t += 0.5
        # source event 229, 93.5s
        ConnectHardpointEvent(root=self, group=MAIN, time_delay=t, target_name='prop_cigarette', parent_name='Char_syd', duration=500, target_hardpoint='hprightconnect_cigarette', parent_hardpoint='hprightconnect')
        # source event 230, 93.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHAND_HNEUT_POINT_RGHT_MILI_000LV_00, duration=3, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.9
        # source event 231, 94.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_SPCBODY_s002x_syd_XE_STND_000LV_11, duration=6, time_scale=1.5, start_time=1.3, loop=False, trans_time=2.5)
        t += 1.6
        # source event 236, 96s
        StartAlchemyEvent(root=self, group=MAIN, time_delay=t, object_name='vfx_rtc_sydsmoke_3', duration=106)
        t += 0.4
        # source event 232, 96.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_MOTION_BREATHE_HEAVY_000LV_XA_, duration=4.444, time_scale=0.9, start_time=0.5, loop=False, trans_time=0.5)
        # source event 233, 96.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=0.532, time_scale=0.1, start_time=0, loop=False, trans_time=None)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_60', None)
        obj_Char_syd.facial(group=MAIN, index=60, append=True, auto_lip=True, extra_delay=0)
        t = 0
        t += 0.9
        # source event 234, 97.4s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=4.444, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        main_group.append_time(2.5)

        # Line 65: source 99s; allocated facial window 10.25s.
        t = 0
        # source event 237, 99s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 0.2
        # source event 204, 99.2s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 205, 99.2s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.8
        # source event 214, 100s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_prisoner2_around', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 215, 100s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_prisoner2', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 251, 100s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_syd', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 252, 100s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_syd', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 238, 101s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHND_CASL_000LV_xa_01, duration=6, time_scale=0.75, start_time=0, loop=True, trans_time=1)
        t += 2
        # source event 216, 103s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_last_prisoner', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 217, 103s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_last_prisoner', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 239, 105s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        # source event 249, 105s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner2', target_name='automarker_prisoner2_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 250, 105s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_prisoner2', target_name='automarker_prisoner2_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 218, 105.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_syd_front', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 219, 105.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_syd_front', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_65', None)
        obj_Char_syd.facial(group=MAIN, index=65, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-2.25)

        # Line 70: source 107s; allocated facial window 0s.
        t = 0
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        voice_sound = self.lookup_single_sound(70)
        SoundEvent(root=self, group=MAIN, sound_name=voice_sound.get_nickname())
        t = 0
        # source event 253, 107s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_last_prisoner', duration=3, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 254, 107s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_last_prisoner', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 261, 107s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_delta3')
        # source event 262, 107s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_delta3_marker', target_name='automarker_cam_delta3_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 263, 107s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_CHRB_TWSTS_FROM_270LV_XA_03, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        # source event 266, 107s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.GENERIC_ANIM, duration=15, start_time=0, time_scale=1, trans_time=0.25)
        # source event 268, 107s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 3
        # source event 255, 110s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_prisoner3', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 256, 110s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_prisoner3', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 264, 110s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.Sc_MLBODY_CHRF_TALK_EMPH_000UP_A_18, duration=11, time_scale=0.8, start_time=0, loop=False, trans_time=1)
        t += 1.5
        # source event 267, 111.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', anim=Male.GENERIC_ANIM, duration=15, start_time=0, time_scale=0.8, trans_time=0.25)
        t += 1.5
        # source event 257, 113s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_last_prisoner', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 258, 113s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_last_prisoner', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 259, 116s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_head_ik', target_name='automarker_head_asf_captain', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 260, 116s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner2_eye_ik', target_name='automarker_head_prisoner3', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 269, 117s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner4_head_ik', target_name='automarker_head_prisoner2', duration=0.01, smooth=True, adjust_pos=True, adjust_orient=True)
        main_group.append_time(11)

        # Line 80: source 118s; allocated facial window 17s.
        t = 0
        # source event 270, 118s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='automarker_prisoner4_head_ik', duration=4, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 272, 118s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_delta1')
        # source event 273, 118s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_delta1', target_name='automarker_cam_delta1_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 274, 118s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_SHRG_SHLDRS_BIG_000LV_XA_03, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 14, 120s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_captain_sydanswer', 'automarker_cam_captain_sydanswer_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 15, 120s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_syd_captside', 'automarker_cam_syd_captside_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 16, 120s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_syd_clothesbox', 'automarker_cam_syd_clothesbox_marker'], duration=150, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 285, 120s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_asf_captain', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 286, 120s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_asf_captain', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 275, 122s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_GESTR_180LV_XA_03, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=0.5)
        t += 2
        # source event 271, 124s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='automarker_prisoner4_head_ik', duration=4, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 287, 124s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_head_ik', duration=100, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 288, 124s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='automarker_trent_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 280, 125s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', target_name='automarker_point_syd_inside', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 281, 125s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=1, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 282, 125s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 283, 125s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 279, 126s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        # source event 284, 126s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_270LV_XA_03, duration=5, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 289, 126s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_syd', duration=2.2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 290, 126s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_syd', duration=1.7, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_80', None)
        obj_Char_prisoner4.facial(group=MAIN, index=80, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-8)

        # Line 90: source 127s; allocated facial window 15s.
        t = 0
        t += 2.5
        # source event 293, 129.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_trentside')
        # source event 294, 129.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_trent_upper', duration=1.75, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 295, 129.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_trent', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_90', None)
        obj_Char_trent.facial(group=MAIN, index=90, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11.5)

        # Line 100: source 130.5s; allocated facial window 4.2s.
        t = 0
        t += 0.5
        # source event 302, 131s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_prisoner4_head_ik', target_name='automarker_head_syd', duration=0.01, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 303, 131s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_delta1', target_name='automarker_prisoner4_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_100', None)
        obj_Char_syd.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-1.7)

        # Line 110: source 133s; allocated facial window 15s.
        t = 0
        # source event 298, 133s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_SPCBODY_s002x_syd_XE_STND_000LV_11, duration=2, time_scale=1.5, start_time=2, loop=False, trans_time=1)
        # source event 304, 133s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_captain_sydanswer')
        # source event 305, 133s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02, duration=5, time_scale=1.1, start_time=0.5, loop=False, trans_time=None)
        t += 1
        # source event 299, 134s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_MOTION_BREATHE_HEAVY_000LV_XA_, duration=4.444, time_scale=0.9, start_time=0.5, loop=False, trans_time=0.5)
        # source event 300, 134s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_NEUT_BLINK_EYES_000LV_A_00, duration=0.532, time_scale=0.1, start_time=0, loop=False, trans_time=None)
        # source event 315, 134s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain_upper', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 316, 134s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=0.1, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 301, 135s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLHEAD_BASEPOSE_000LV_02_01, duration=4.444, time_scale=0.9, start_time=0, loop=False, trans_time=0.5)
        # source event 308, 135s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_captside')
        # source event 309, 135s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd_captside', target_name='automarker_cam_syd_captside_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 310, 135s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_SPCBODY_s002x_syd_XE_STND_000LV_11, duration=6, time_scale=1, start_time=6.5, loop=False, trans_time=None)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_110', None)
        obj_Char_prisoner4.facial(group=MAIN, index=110, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-12.5)

        # Line 120: source 135.5s; allocated facial window 17.5s.
        t = 0
        t += 1.5
        # source event 311, 137s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_TALK_EMPH_000DN_A_20, duration=4, time_scale=0.5, start_time=0, loop=True, trans_time=2)
        t += 2.0
        # source event 317, 139s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_trent_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 318, 139s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3.0
        # source event 312, 142s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 2.0
        # source event 313, 144s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        # source event 319, 144s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain_upper', duration=2, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 320, 144s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 4.0
        # source event 314, 148s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=4, time_scale=0.7, start_time=0, loop=True, trans_time=1)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_120', None)
        obj_Char_syd.facial(group=MAIN, index=120, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4.0)

        # Line 130: source 149s; allocated facial window 15s.
        t = 0
        # source event 321, 149s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_syd_front', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 327, 149s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_130', None)
        obj_Char_trent.facial(group=MAIN, index=130, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-12)

        # Line 140: source 152s; allocated facial window 9s.
        t = 0
        # source event 340, 152s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_clothesbox')
        # source event 341, 152s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_syd_clothesbox', target_name='automarker_cam_syd_clothesbox_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 342, 152s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_syd_clothesbox_marker', target_name='automarker_cam_syd_clothesbox_marker_pos2', duration=8, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 347, 152s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_GESTR_RGHT_000LV_XA_02, duration=8, time_scale=0.5, start_time=0, loop=False, trans_time=None)
        t += 2
        # source event 343, 154s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='panel1', target_name='automarker_panel1_pos_open', duration=5, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 344, 154s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='panel1', angle=-90, axis='Z_AXIS', duration=5, smooth=True)
        # source event 345, 154s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_close_door_clothesbox', duration=5, start_time=500, loop=False)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_140', None)
        obj_Char_syd.facial(group=MAIN, index=140, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-5)

        # Line 145: source 156s; allocated facial window 10s.
        t = 0
        # source event 346, 156s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_close_door_clothesbox', duration=3, attenuation=-100)
        t += 2
        # source event 330, 158s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 331, 158s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1
        # source event 332, 159s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_trent_upper', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 333, 159s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_trent', duration=1, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_145', None)
        obj_Char_syd.facial(group=MAIN, index=145, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 150: source 162s; allocated facial window 16s.
        t = 0
        # source event 355, 162s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_captside')
        t += 0.5
        # source event 334, 162.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 335, 162.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=1.6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2.5
        # source event 348, 165s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHNDUP_TRNS_000LV_XA_01, duration=7, time_scale=0.7, start_time=0, loop=False, trans_time=1)
        t += 1
        # source event 336, 166s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_trent_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 337, 166s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_trent', duration=1.6, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 349, 167s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CONV_RHNDDN_TRNS_000LV_XA_02, duration=3, time_scale=0.75, start_time=0, loop=False, trans_time=1)
        t += 3
        # source event 338, 170s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 339, 170s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=1.6, smooth=True, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_150', None)
        obj_Char_syd.facial(group=MAIN, index=150, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 160: source 174s; allocated facial window 18s.
        t = 0
        # source event 360, 174s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent')
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_160', None)
        obj_Char_trent.facial(group=MAIN, index=160, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-11)

        # Line 170: source 181s; allocated facial window 9s.
        t = 0
        # source event 364, 181s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_trent_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 365, 181s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_trent', duration=1.6, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 380, 181s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_syd_captside')
        t += 2
        # source event 366, 183s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_syd_front', duration=1.75, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 367, 183s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_syd_front', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 368, 183s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_SPCBODY_s002x_syd_XE_STND_000LV_11, duration=6, time_scale=1.5, start_time=1.3, loop=False, trans_time=2.5)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_170', None)
        obj_Char_syd.facial(group=MAIN, index=170, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-3)

        # Line 180: source 187s; allocated facial window 15s.
        t = 0
        t += 0.5
        # source event 372, 187.5s
        NeckIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_head_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        # source event 373, 187.5s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_syd', target_name='automarker_syd_eye_ik', duration=25, transition_duration=1, target_type='ROOT', target_part='', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 0.5
        # source event 374, 188s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain_upper', duration=1.75, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 375, 188s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=1.25, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 19, 190s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_trent_finalword', 'automarker_cam_trent_finalword_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 20, 190s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['cam_exit', 'automarker_cam_exit_marker'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='LOOK_AT')
        # source event 369, 190s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', anim=Male.Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06, duration=6, time_scale=0.6, start_time=0, loop=False, trans_time=1)
        # source event 376, 190s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_trent_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 377, 190s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_trent', duration=1.5, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 370, 192s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='vfx_rtc_cigaretteglow_4', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 371, 192s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='vfx_rtc_sydsmoke_3', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 378, 194s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_head_ik', target_name='automarker_head_asf_captain_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 379, 194s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_syd_eye_ik', target_name='automarker_head_asf_captain', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 3
        # source event 395, 197s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', target_name='automarker_point_prisoner4_stand', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 396, 197s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', target_name='automarker_point_prisoner1_stand', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_180', None)
        obj_Char_syd.facial(group=MAIN, index=180, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-4)

        # Line 190: source 198s; allocated facial window 15s.
        t = 0
        # source event 391, 198s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_finalword')
        # source event 392, 198s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_trent_finalword', target_name='automarker_cam_trent_finalword_pos2', duration=5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 397, 198s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=8, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 398, 198s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_STND_IDLE_000LV_xa_04, duration=8, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 1
        # source event 399, 199s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', anim=Male.Sc_MLBODY_STROLL_000LV_XA_01, duration=8, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 400, 199s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', anim=Male.Sc_MLBODY_STROLL_000LV_XA_01, duration=8, time_scale=1, start_time=0, loop=True, trans_time=None)
        t += 1
        # source event 386, 200s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_head_ik', target_name='automarker_head_trent_front_upper', duration=2.5, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 387, 200s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_trent_eye_ik', target_name='automarker_head_trent_front_upper', duration=1.4, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 390, 200s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_TWSTS_FROM_270LV_XA_03, duration=5, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 1.5
        # source event 388, 201.5s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_trent_head_ik', 'Char_prisoner1'], duration=4, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='Body_Head', target_type='PART', flags='POSITION+ORIENTATION')
        t += 2.5
        # source event 389, 204s
        EyeIkEvent(root=self, group=MAIN, time_delay=t, char_name='Char_trent', target_name='Char_prisoner1', duration=3, transition_duration=1, target_type='PART', target_part='Body_Head', up='NEG_Y_AXIS', front='Z_AXIS')
        t += 1.9
        # source event 411, 205.9s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_hall', duration=0.1, attenuation=0)
        t += 0.1
        # source event 412, 206s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='ambience_room', duration=0.1, attenuation=-100)
        # source event 413, 206s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_exit')
        # source event 414, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_exit', target_name='automarker_cam_exit_pos2', duration=12, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 415, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_exit_marker', target_name='automarker_cam_exit_marker_pos2', duration=12, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 420, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', target_name='automarker_point_trent_classic', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 421, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1b', target_name='automarker_point_prisoner1b', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 422, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', target_name='automarker_point_prisoner2b', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 423, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', target_name='automarker_point_prisoner3b', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 424, 206s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', target_name='automarker_point_prisoner4b', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 1
        # source event 405, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 406, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_syd', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 407, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 408, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 409, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta3', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 410, 207s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_delta1', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 402, 207.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='body1', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 403, 207.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='body2', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 404, 207.1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='body3', target_name='offscreen', duration=0.001, smooth=False, adjust_pos=True, adjust_orient=True)
        t += 0.1
        # source event 401, 207.2s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='panel1', target_name='automarker_panel1_init_pos', duration=0.001, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 0.8
        # source event 416, 208s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['doors'], animation='Sc_cv_prison_cell', duration=3.332, time_scale=1, weight=1, trans_scale=1)
        # source event 418, 208s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_open_door', duration=10, start_time=0, loop=False)
        # source event 425, 208s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1b', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=25, time_scale=1, start_time=0.5, loop=True, trans_time=None)
        # source event 426, 208s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', anim=Male.Sc_MLBODY_WLKG_000LV_XB_01, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 427, 208s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', anim=Male.Sc_MLBODY_WLKG_000LV_XB_01, duration=25, time_scale=1, start_time=0.5, loop=True, trans_time=None)
        # source event 428, 208s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=25, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 433, 208s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=5.6, time_scale=1, start_time=0.9, loop=True, trans_time=None)
        t += 4
        # source event 430, 212s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner3b', angle=90, axis='Y_AXIS', duration=4, smooth=True)
        select_dialogue(self, 6, 'Msn6Prison', 'm06_order_prison')
        self.groups.pop('motion_190', None)
        obj_Char_trent.facial(group=MAIN, index=190, append=True, auto_lip=True, extra_delay=0)
        t = 0
        # source event 429, 213s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner1b', angle=90, axis='Y_AXIS', duration=4, smooth=True)
        t += 0.6
        # source event 434, 213.6s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Male.Sc_MLBODY_WALK_STND_TRNS_000LV_XA_02, duration=4, time_scale=1, start_time=0, loop=False, trans_time=None)
        t += 0.4
        # source event 431, 214s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner2b', angle=90, axis='Y_AXIS', duration=4, smooth=True)
        # source event 432, 214s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_prisoner4b', angle=90, axis='Y_AXIS', duration=4, smooth=True)
        t += 2
        # source event 435, 216s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Male.Sc_MLBODY_STND_LOOK_AROU_000LV_XA_09, duration=10, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 0.5
        # source event 436, 216.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Trent.Sc_MLHEAD_HAPPY_SMILE_SNEER_TRENT_000LV_XA_, duration=10, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        t += 2.7
        # source event 437, 219.2s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Trent.Sc_MLHEAD_MOTION_EYES_OPENBG_TRENT_000LV_XA_, duration=10, time_scale=0.7, start_time=0, loop=False, trans_time=0.25)
        t += 5.8
        # source event 417, 225s
        SourceMotionEvent(root=self, group=MAIN, time_delay=t, targets=['doors'], animation='Sc_cv_prison_cell', duration=3.332, start_time=3.332, time_scale=1, weight=1, trans_scale=1)
        # source event 419, 225s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='snd_close_door', duration=10, start_time=0, loop=False)
        # source event 438, 225s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Male.Sc_MLBODY_STND_WALK_TRNS_270LV_XA_02, duration=10, time_scale=1, start_time=0, loop=False, trans_time=0.5)
        t += 2
        # source event 439, 227s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent_classic', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=10, time_scale=1, start_time=0, loop=True, trans_time=None)
        main_group.append_time(17.0)
        preserve_spatial(self.get_entity('body1'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('body2'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('body3'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('prop_mask_trent'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('prop_mask_pris1'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('prop_mask_pris2'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('prop_mask_pris3'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('prop_mask_pris4'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        preserve_spatial(self.get_entity('prop_mask_pris5'), source_basis=[[0, 0, 0.8], [0, 1, 0], [-1, 0, 0]], reference_orientation=[0.7071068286895752, 2.9802322387695312e-08, 0.7071068286895752, -2.9802322387695312e-08])
        restore_dialogue(self)
