"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm04_jumphole'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(8.0)
        obj_Shot06_Camera_1 = LookAtCamera(root=self, name='Shot06_Camera_1', fov=35, farplane=100000, look_duration=30)
        preserve_entity(obj_Shot06_Camera_1, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Camera_1 = StaticCamera(root=self, name='Camera_1', fov=45, farplane=100000)
        preserve_entity(obj_Camera_1, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 45, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        preserve_entity(self.get_entity('automarker_Shot06_Camera_1_focus'), userprops={'main_object': 'main_object'})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Shot06_Camera_1')
        # source event 2, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Shot06_Camera_1', 'automarker_Shot06_Camera_1_focus'], duration=30, offset=[0, 250, 250], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ENTITY_RELATIVE')
        restore_dialogue(self)
