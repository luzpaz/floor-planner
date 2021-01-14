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
    app = App()

    def test_create_and_get(self):
        """Ensure textures can create and get a test texture.
        """
        TexturesTests.app.view.textures.textures[0]\
            = TexturesTests.app.view.textures.create(
            TexturesTests.app.view.renderer, b'../res/textures/test.png')

        texture = TexturesTests.app.view.textures.get(0)
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
        TexturesTests.app.view.textures.unload()
        self.assertEqual(len(TexturesTests.app.view.textures.textures), 0)
        self.assertEqual(len(TexturesTests.app.view.textures.layers), 0)

class ViewTests(unittest.TestCase):
    """Tests for the View class (view.py)."""
    app = App()

    def test_initialization(self):
        """Ensure the view constructor initializes the SDL
        components and textures.
        """
        self.assertIsNotNone(ViewTests.app.view.window)
        self.assertIsNotNone(ViewTests.app.view.renderer)
        self.assertIsInstance(ViewTests.app.view.textures, Textures)

    def test_camera_values(self):
        """Ensure view takes in the UI camera's position and scale.
        """
        ViewTests.app.controller.camera.x = 500
        ViewTests.app.controller.camera.y = 1000
        ViewTests.app.controller.camera.scale = 0.75

        ViewTests.app.view.update(ViewTests.app.model, ViewTests.app.controller)
        self.assertEqual(int(ViewTests.app.view.camera_x), 500)
        self.assertEqual(int(ViewTests.app.view.camera_y), 1000)
        self.assertEqual(ViewTests.app.view.camera_scale, 0.75)

    def test_empty_update_layers(self):
        """Ensure no entities are rendered onto the layer if entities are empty.
        """
        self.assertEqual(ViewTests.app.view.update_layer(
            ViewTests.app.model, ViewTests.app.controller), 0)

    def test_base_update_layers(self):
        """Ensure expected number of entities are rendered onto the layer.
        """
        for i in range(5):
            ViewTests.app.model.add_line(EntityType.EXTERIOR_WALL)

        for i in range(3):
            ViewTests.app.model.add_window()

        for i in range(2):
            ViewTests.app.model.add_door()

        self.assertEqual(ViewTests.app.view.update_layer(
            ViewTests.app.model, ViewTests.app.controller), 50)

        ViewTests.app.model.lines.clear()
        ViewTests.app.model.windows.clear()
        ViewTests.app.model.doors.clear()
        ViewTests.app.model.square_vertices.clear()

    def test_render_ui_text(self):
        """Ensure expected number of text displayers are rendered from the UI.
        """
        ViewTests.app.model.add_user_text('text')
        self.assertEqual(ViewTests.app.view.render_ui_text(
            ViewTests.app.controller), 3)

    def test_empty_render_text(self):
        """Ensure render text returns None if the text is None or if the text
        string is empty.
        """
        self.assertIsNone(ViewTests.app.view.render_relative_text(None))
        self.assertIsNone(ViewTests.app.view.render_relative_text(Text()))

    def test_render_text(self):
        """Ensure render_text completes rendering of a non-empty text.
        """
        text = Text()
        text.text = 'Non empty text'

        self.assertTrue(ViewTests.app.view.render_relative_text(text))

        text.font = FontSize.MEDIUM
        self.assertTrue(ViewTests.app.view.render_relative_text(text))

        text.font = FontSize.LARGE
        self.assertTrue(ViewTests.app.view.render_relative_text(text))

    def test_center_text(self):
        """Ensures center_text returns the expected values for base cases.
        """
        ViewTests.app.view.screen_width = 1920
        ViewTests.app.view.screen_height = 1080
        self.assertEqual(ViewTests.app.view.center_text(250), 835)
        self.assertEqual(ViewTests.app.view.center_text(0), 960)

    def test_rendering_no_exceptions(self):
        """Ensure that functions that only render do not throw exceptions.
        These functions must be tested interactively.
        """
        self.assertTrue(ViewTests.app.view.render_two_point_placement(
            ViewTests.app.controller, ViewTests.app.model))
        
        line = ((0, 0), (5, 5), 1)
        self.assertTrue(ViewTests.app.view.render_line_placement(line))

        self.assertTrue(ViewTests.app.view.render_mouse_selection(
            ViewTests.app.controller))

        self.assertTrue(ViewTests.app.view.render_user_text(
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