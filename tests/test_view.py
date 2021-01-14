import sdl2, sys, unittest
sys.path.append("..\src")

from app import App
from ctypes import c_int, pointer
from entities import UserText
from entity_types import EntityType
from text import Text
from textures import Textures
from view import View, FontSize

class TexturesTests(unittest.TestCase):
    """Tests for the Texture class (view.py)."""

    def test_create_and_get(self):
        """Ensure textures can create and get a test texture.
        """
        app = App()
        app.view.textures.textures[0]\
            = app.view.textures.create(
            app.view.renderer, b'../res/textures/test.png')

        texture = app.view.textures.get(0)
        self.assertIsNotNone(texture)

        # Ensure texture has expected size (matches png file).
        width = pointer(c_int(0))
        height = pointer(c_int(0))
        sdl2.SDL_QueryTexture(texture, None, None, width, height)
        width = width.contents.value
        height = height.contents.value
        self.assertEqual(width, 500)
        self.assertEqual(height, 500)

    def test_destructor(self):
        """Ensure textures and layers are cleared after calling unload.
        """
        app = App()
        app.view.textures.unload()
        self.assertEqual(len(app.view.textures.textures), 0)
        self.assertEqual(len(app.view.textures.layers), 0)

class ViewTests(unittest.TestCase):
    """Tests for the View class (view.py)."""

    def test_initialization(self):
        """Ensure the view constructor initializes the SDL
        components and textures.
        """
        app = App()
        self.assertIsNotNone(app.view.window)
        self.assertIsNotNone(app.view.renderer)
        self.assertIsInstance(app.view.textures, Textures)

    def test_camera_values(self):
        """Ensure view takes in the UI camera's position and scale.
        """
        app = App()
        app.controller.camera.x = 500
        app.controller.camera.y = 1000
        app.controller.camera.scale = 0.75

        app.view.update(app.model, app.controller)
        self.assertEqual(int(app.view.camera_x), 500)
        self.assertEqual(int(app.view.camera_y), 1000)
        self.assertEqual(app.view.camera_scale, 0.75)

    def test_empty_update_layers(self):
        """Ensure no entities are rendered onto the layer if entities are empty.
        """
        app = App()
        self.assertEqual(app.view.update_layer(
            app.model, app.controller), 0)

    def test_base_update_layers(self):
        """Ensure expected number of entities are rendered onto the layer.
        """
        app = App()
        for i in range(5):
            app.model.add_line(EntityType.EXTERIOR_WALL)

        for i in range(3):
            app.model.add_window()

        for i in range(2):
            app.model.add_door()

        self.assertEqual(app.view.update_layer(
            app.model, app.controller), 50)

        app.model.lines.clear()
        app.model.windows.clear()
        app.model.doors.clear()
        app.model.square_vertices.clear()

    def test_render_ui_text(self):
        """Ensure expected number of text displayers are rendered from the UI.
        """
        app = App()
        app.model.add_user_text('text')
        self.assertEqual(app.view.render_ui_text(
            app.controller), 3)

    def test_empty_render_text(self):
        """Ensure render text returns None if the text is None or if the text
        string is empty.
        """
        app = App()
        self.assertIsNone(app.view.render_relative_text(None))
        self.assertIsNone(app.view.render_relative_text(Text()))

    def test_render_text(self):
        """Ensure render_text completes rendering of a non-empty text.
        """
        app = App()
        text = Text()
        text.text = 'Non empty text'

        self.assertTrue(app.view.render_relative_text(text))

        text.font = FontSize.MEDIUM
        self.assertTrue(app.view.render_relative_text(text))

        text.font = FontSize.LARGE
        self.assertTrue(app.view.render_relative_text(text))

    def test_center_text(self):
        """Ensures center_text returns the expected values for base cases.
        """
        app = App()
        app.view.screen_width = 1920
        app.view.screen_height = 1080
        self.assertEqual(app.view.center_text(250), 835)
        self.assertEqual(app.view.center_text(0), 960)

    def test_rendering_no_exceptions(self):
        """Ensure that functions that only render do not throw exceptions.
        These functions must be tested interactively.
        """
        app = App()
        self.assertTrue(app.view.render_two_point_placement(
            app.controller, app.model))
        
        line = ((0, 0), (5, 5), 1)
        self.assertTrue(app.view.render_line_placement(line))

        self.assertTrue(app.view.render_mouse_selection(
            app.controller))

        self.assertTrue(app.view.render_user_text(
            UserText('text')))

    def test_switching_between_layers(self):
        """Ensure update layer renders only the number of entities there are
        in each layer when switching between layers.
        """
        app = App()

        for i in range(4):
            line = app.model.add_line(EntityType.EXTERIOR_WALL)
            line.layer = 0

        for i in range(2):
            line = app.model.add_line(EntityType.EXTERIOR_WALL)
            line.layer = 1

        self.assertTrue(app.view.update_layer(app.model, app.controller), 4)

        app.controller.current_layer = 1
        self.assertTrue(app.view.update_layer(app.model, app.controller), 2)
        
    def test_destructor(self):
        """Ensures destructor clears textures and sets SDL components to None.
        """
        view = View()
        view.exit()
        self.assertIsNone(view.window)
        self.assertIsNone(view.renderer)
        self.assertEqual(len(view.textures.textures), 0)

if __name__ == '__main__':
    unittest.main()