"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_order_camera4'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(10.0)
        obj_Shot06_Camera_0 = LookAtCamera(root=self, name='Shot06_Camera_0', fov=35, farplane=100000, look_duration=1)
        preserve_entity(obj_Shot06_Camera_0, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Shot06_Camera_0')
        restore_dialogue(self)
