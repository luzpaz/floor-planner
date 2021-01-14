import ctypes, sdl2, sys, threading, unittest, os.path
sys.path.append("..\src")

from app import App
from camera import Camera
from controller import Controller
from entities import Line
from entity_types import EntityType
from model import Model
from panels import Button, Panel
from polling import PollingType
from text import Text, CenterText, MessageStack, FPSDisplayer
from tools import ExportCommand
from view import View, FontSize

class ControllerTests(unittest.TestCase):
    """Tests for the Controller class (controller.py)."""

    def test_handle_text_input(self):
        """Ensure user typing (from the keyboard) is captured. Ensure
        only digits are accepted as input. If the user enters something that is
        not a digit, ensure the text is cleared.
        """
        controller = Controller()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_TEXTINPUT

        event.text.text = b'1'
        controller.handle_text_input(event)
        self.assertEqual(controller.text, '1')

        event.text.text = b'0'
        controller.handle_text_input(event)
        self.assertEqual(controller.text, '10')

        event.text.text = b'a'
        controller.handle_text_input(event)
        self.assertEqual(controller.text, '')

    def test_update_bottom_right_text(self):
        """Ensure the bottom right text displays the current mouse coordinates
        and camera scale.
        """
        controller = Controller()
        controller.mouse_x = 500
        controller.mouse_y = 0

        controller.update_bottom_right_text()
        self.assertEqual(controller.center_text.text[
            CenterText.BOTTOM_RIGHT_TEXT].text, 'X: 500 Y: 0 - Zoom: 1.0')

    def test_update_bottom_text(self):
        """Ensure the line the user has their mouse hovered over has its
        type and length displayed.
        """
        app = App()
        line = app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (12, 0))
        app.controller.mouse_x = 1
        app.controller.mouse_y = 0
        app.controller.update_bottom_center_text(app.model)
        self.assertEqual(app.controller.center_text.text[
            CenterText.BOTTOM_CENTER_TEXT].text, 'Exterior Wall (1 ft 0 in)')

    def test_single_entity_selection(self):
        """Ensure that user can select a single entity.
        """
        app = App()
        line = app.model.add_line(EntityType.EXTERIOR_WALL, (3, 3), (10, 10))
        app.controller.mouse_x = 5
        app.controller.mouse_y = 5
        app.controller.handle_single_entity_selection(app.model)
        self.assertTrue(line in app.controller.selected_entities)

    def test_handle_multiple_entity_selection(self):
        """Ensure multiple selected entities are captured when the mouse
        selection is colliding with all of them.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (10, 10))
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 30), (10, 2))
        app.controller.mouse_selection = sdl2.SDL_Rect(0, 0, 500, 500)
        app.controller.handle_multiple_entity_selection(app.model)
        self.assertEqual(len(app.controller.selected_entities), 2)

    def test_camera_pan(self):
        """Ensure handle_camera_pan expectedly adjusts the camera position
        when the user moves the mouse.
        """
        controller = Controller()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN

        controller.handle_camera_pan(event)
        self.assertTrue(controller.panning_camera)
        self.assertEqual(controller.pan_start_x, 0)
        self.assertEqual(controller.pan_start_y, 0)

        controller.mouse_x = 500
        controller.mouse_y = 500

        controller.handle_camera_pan(event)
        self.assertEqual(int(controller.camera.x), -500)
        self.assertEqual(int(controller.camera.y), -500)

    def test_camera_zoom(self):
        """Ensure user scrolling the mouse wheel zooms the camera in and out.
        """
        controller = Controller()
        event = sdl2.SDL_Event()

        event.wheel.y = 1
        controller.handle_camera_zoom(event)
        self.assertEqual(controller.camera.scale, 1.05)

        event.wheel.y = -1
        controller.handle_camera_zoom(event)
        self.assertEqual(controller.camera.scale, 1.0)

    def test_min_camera_zoom(self):
        """Ensure user cannot exceed the minimum camera scale by zooming too
        far out (camera.scale cannot be less than or equal to 0).
        """
        controller = Controller()
        event = sdl2.SDL_Event()

        event.wheel.y = -1
        controller.camera.scale = 0.0
        controller.handle_camera_zoom(event)
        self.assertEqual(controller.camera.scale, 0.05)

    def test_mouse_drag_start(self):
        """Ensure handle_mouse_drag captures the starting point
        of the user's mouse drag input.
        """
        controller = Controller()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        event.button.button = sdl2.SDL_BUTTON_LEFT
        controller.mouse_down = False

        controller.mouse_x = 2500
        controller.mouse_y = 500
        controller.camera.y = 500

        controller.handle_mouse_drag(event)
        self.assertTrue(controller.mouse_down)
        self.assertEqual(controller.mouse_down_starting_x, 2500)
        self.assertEqual(controller.mouse_down_starting_y, 1000)

    def test_mouse_drag(self):
        """Ensure handle_mouse_drag updates the mouse_selection
        rectangle as the user presses and drags the mouse.
        """
        controller = Controller()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEMOTION
        controller.mouse_down = True

        controller.mouse_down_starting_x = 0
        controller.mouse_down_starting_y = 0

        controller.mouse_x = 1500
        controller.mouse_y = 500
        
        controller.handle_mouse_drag(event)
        self.assertEqual(controller.mouse_selection,
                         sdl2.SDL_Rect(0, 0, 1500, 500))

    def test_mouse_drag_reset(self):
        """Ensure handle_mouse_drag resets the mouse_selection rectangle
        when the user releases the mouse.
        """
        controller = Controller()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONUP
        controller.mouse_down = True

        controller.handle_mouse_drag(event)
        self.assertFalse(controller.mouse_down)
        self.assertEqual(controller.mouse_selection, sdl2.SDL_Rect())

    def test_loop(self):
        """Ensure handle_input runs and returns True on a base case.
        The functionality is better tested with other methods and
        interactive testing.
        """
        app = App()
        self.assertTrue(app.controller.handle_input(app.model, (1920, 1080)))

    def test_two_point_placement_horizontal(self):
        """Ensure user holding Shift and creating a line with less than a 45
        degree angle creates a horizontal line.
        """
        app = App()
        event = sdl2.SDL_Event()
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_LSHIFT] = 1
        app.controller.first_point_placed = True
        app.controller.first_point_x = 0
        app.controller.first_point_y = 0
        app.controller.mouse_x = 50
        app.controller.mouse_y = 5
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertTrue(app.controller.horizontal_line)

    def test_two_point_placement_vertical(self):
        """Ensure user holding Shift and creating a line with greater than a 45
        degree angle creates a vertical line.
        """
        app = App()
        event = sdl2.SDL_Event()
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_LSHIFT] = 1

        app.controller.first_point_placed = True
        app.controller.first_point_x = 0
        app.controller.first_point_y = 0

        app.controller.mouse_x = 5
        app.controller.mouse_y = 50

        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertTrue(app.controller.vertical_line)

    def test_two_point_placement_first_point(self):
        """Ensure that if user is placing the first point,
        handle_two_point_placement sets the class values.
        """
        app = App()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        keystate = sdl2.SDL_GetKeyboardState(None)
        app.controller.first_point_placed = False

        app.controller.mouse_x = 500
        app.controller.mouse_y = 1000
        
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(app.controller.first_point_x, 498)
        self.assertEqual(app.controller.first_point_y, 1002)
        self.assertTrue(app.controller.first_point_placed)

    def test_two_point_placement_second_point(self):
        """Ensure that if user is placing the second point,
        the line is created and added to the model.
        """
        app = App()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        keystate = sdl2.SDL_GetKeyboardState(None)
        app.controller.first_point_placed = True
        app.controller.placement_type = EntityType.EXTERIOR_WALL

        # Horizontal line
        app.controller.horizontal_line = True
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(len(app.model.lines), 1)
        
        # Vertical line
        app.controller.first_point_placed = True
        app.controller.horizontal_line = False
        app.controller.vertical_line = True
        app.controller.placement_type = EntityType.EXTERIOR_WALL
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(len(app.model.lines), 2)
        
        # Diagonal line
        app.controller.first_point_placed = True
        app.controller.vertical_line = False
        app.controller.placement_type = EntityType.EXTERIOR_WALL
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(len(app.model.lines), 3)

    def test_two_point_placement_text(self):
        """Ensure the expected length text is displayed when the user is
        placing the second point.
        """
        app = App()
        event = sdl2.SDL_Event()
        keystate = sdl2.SDL_GetKeyboardState(None)
        app.controller.first_point_placed = True
        app.controller.placement_type = EntityType.EXTERIOR_WALL
        app.controller.first_point_x = 0
        app.controller.first_point_y = 0
        app.controller.mouse_x = 8*12
        app.controller.mouse_y = 6*12

        expected_message = "Length: 10 ft 0 in"
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(app.controller.center_text.text[
            CenterText.BOTTOM_CENTER_TEXT].text, expected_message)
        self.assertTrue(app.controller.center_text.text[
            CenterText.TOP_CENTER_TEXT].text != '')

    def test_horizontal_window_placement(self):
        """Ensure handle_one_point_placement for a window on a horizontal wall
        adds the window to the model.
        """
        app = App()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 0))

        app.controller.mouse_x = 2
        app.controller.mouse_y = 0
        app.controller.placement_type = EntityType.WINDOW
        app.controller.place_one_point = True
        app.controller.handle_one_point_placement(event, app.model)
        self.assertEqual(len(app.model.windows), 1)

    def test_vertical_door_placement(self):
        """Ensure handle_one_point_placement for a door on a horizontal wall
        adds the door to the model.
        """
        app = App()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (0, 5))

        app.controller.mouse_x = 0
        app.controller.mouse_y = 2
        app.controller.placement_type = EntityType.DOOR
        app.controller.place_one_point = True
        app.controller.handle_one_point_placement(event, app.model)
        self.assertEqual(len(app.model.doors), 1)

    def test_empty_window_placement(self):
        """Ensure placing window when there are no exterior walls causes
        the message stack to display the error message.
        """
        app = App()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN

        app.controller.placement_type = EntityType.WINDOW
        app.controller.place_one_point = True
        app.controller.handle_one_point_placement(event, app.model)
        self.assertEqual(len(app.model.windows), 0)
        self.assertEqual(app.controller.message_stack.text[0].text,
                         'No exterior wall for window placement'\
                          + ' at that location.')

    def test_empty_window_placement(self):
        """Ensure placing window when an exterior wall is too far causes
        the message stack to display the error message.
        """
        app = App()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN
        
        app.model.add_line(EntityType.EXTERIOR_WALL, (250, 250), (300, 300))

        app.controller.placement_type = EntityType.WINDOW
        app.controller.place_one_point = True
        app.controller.handle_one_point_placement(event, app.model)
        self.assertEqual(len(app.model.windows), 0)
        self.assertEqual(app.controller.message_stack.text[0].text,
                         'No exterior wall for window placement'\
                          + ' at that location.')

    def test_base_adjusted_mouse(self):
        """Ensure get_adjusted_mouse returns the mouse location rounded
        to the nearest snap interval when there is no nearby vertex or
        axis to snap to.
        """
        app = App()
        self.assertEqual((0, 0), app.controller.get_adjusted_mouse(app.model))

        app.controller.mouse_x = 34
        app.controller.mouse_y = 29
        self.assertEqual((36, 30), app.controller.get_adjusted_mouse(app.model))

    def test_vertex_adjusted_mouse(self):
        """Ensure get_adjusted_mouse returns the nearest vertex to snap to
        when there are multiple vertices in range.
        """
        app = App()
        app.controller.mouse_x = 0
        app.controller.mouse_y = 10
        app.model.vertices.add((0, 9))
        app.model.vertices.add((0, 12))
        app.model.vertices.add((5, 2))
        self.assertEqual((0, 9), app.controller.get_adjusted_mouse(app.model))

    def test_axis_adjusted_mouse(self):
        """Ensure get_adjusted_mouse returns the nearest axis to snap to
        when there are multiple axis in range.
        """
        app = App()
        app.controller.place_two_points = True
        app.model.vertices.add((0, 10))
        app.model.vertices.add((50, 10))
        app.controller.mouse_x = 20
        app.controller.mouse_y = 10
        self.assertEqual(app.controller.get_adjusted_mouse(app.model), (18, 12))
        self.assertEqual(app.controller.nearest_vertex_axis, (0, 10))

    def test_get_two_point_placement(self):
        """Ensure get_two_point_placement returns the expected line starting
        and ending vertices for diagonal, vertical, and horizontal lines."""

        app = App()
        app.controller.place_two_points = True
        app.controller.first_point_placed = True
        
        app.controller.line_thickness = 1
        app.controller.mouse_x = 48
        app.controller.mouse_y = 48

        self.assertEqual(app.controller.get_two_point_placement(app.model),
                         ((0, 0), (48, 48), 1))

        app.controller.horizontal_line = True
        self.assertEqual(app.controller.get_two_point_placement(app.model),
                         ((0, 0), (48, 0), 1))

        app.controller.horizontal_line = False
        app.controller.vertical_line = True
        self.assertEqual(app.controller.get_two_point_placement(app.model),
                         ((0, 0), (0, 48), 1))

    def test_fps_displayer(self):
        """Ensure the FPS displayer expectedly counts the FPS each frame
        and updates the text to display FPS: #
        """
        fps_displayer = FPSDisplayer()
        for i in range(50):
            fps_displayer.update()
        fps_displayer.last_fps = -5000
        fps_displayer.update()
        self.assertEqual(fps_displayer.text[0].text, 'FPS: 51')

    def test_message_stack(self):
        """Ensure that the message stack removes expired messages.
        """
        MessageStack.DURATION = 10
        message_stack = MessageStack()
        message_stack.insert(['message 1', 'message 2', 'message 3'])
        self.assertEqual(len(message_stack.text), 3)
        sdl2.SDL_Delay(MessageStack.DURATION * 2)
        for i in range(3):
            message_stack.update()
        self.assertEqual(len(message_stack.text), 0)

    def test_update_item_to_move(self):
        """Ensure that update_item_to_move selects a single entity from
        the selected entities when selected entities is not empty.
        """
        controller = Controller()
        
        # Empty selected entities
        controller.update_item_to_move()
        self.assertIsNone(controller.item_to_move)

        line = Line()
        controller.selected_entities.add(line)
        controller.update_item_to_move()
        self.assertEqual(controller.item_to_move, line)

    def test_ctrl_hotkeys(self):
        """Ensure user pressing CTRL and a hotkey sets the expected poll event.
        """
        controller = Controller()
        keystate = sdl2.SDL_GetKeyboardState(None)

        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.SELECTING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_E] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.ERASING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_D] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.DRAWING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_M] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.MEASURING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_T] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.ADDING_TEXT)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_G] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.DISPLAY_GRID)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_Z] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.UNDOING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_Y] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.REDOING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_S] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.SAVING)

        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_O] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.LOADING)
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_X] = 1
        controller.handle_ctrl_hotkeys(keystate)
        self.assertEqual(controller.polling, PollingType.EXPORTING)

    def test_entity_hotkey_for_exterior_wall(self):
        """Ensure user pressing 0 begins exterior wall placement.
        """
        app = App()
        keystate = sdl2.SDL_GetKeyboardState(None)        
        keystate[sdl2.SDL_SCANCODE_0] = 1
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)
        self.assertEqual(app.controller.placement_type,
                         EntityType.EXTERIOR_WALL)
        self.assertEqual(app.controller.line_thickness,
                         Line.EXTERIOR_WALL)
        
    def test_entity_hotkey_for_interior_wall(self):
        """Ensure user pressing 1 begins interior wall placement.
        """
        app = App()
        keystate = sdl2.SDL_GetKeyboardState(None)        
        keystate[sdl2.SDL_SCANCODE_KP_1] = 1
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)
        self.assertEqual(app.controller.placement_type,
                         EntityType.INTERIOR_WALL)
        self.assertEqual(app.controller.line_thickness,
                         Line.INTERIOR_WALL)
        
    def test_entity_hotkey_for_window(self):
        """Ensure user pressing 2 begins window placement.
        """
        app = App()
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_2] = 1
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_one_point)
        self.assertEqual(app.controller.placement_type, EntityType.WINDOW)
        
    def test_entity_hotkey_for_door(self):
        """Ensure user pressing 3 begins door placement.
        """
        app = App()
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_KP_3] = 1
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_one_point)
        self.assertEqual(app.controller.placement_type, EntityType.DOOR)
        
class CameraTests(unittest.TestCase):
    """Tests for the Camera class (controller.py)."""

    def test_up_and_down_scrolling(self):
        """Ensure user can scroll the camera up and down.
        """
        camera = Camera()
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_W] = 1
        camera.last_scrolled = -1000
        camera.scroll(keystate)
        self.assertTrue(camera.y < 0)
        
        keystate[sdl2.SDL_SCANCODE_W] = 0
        keystate[sdl2.SDL_SCANCODE_DOWN] = 1
        keystate[sdl2.SDL_SCANCODE_LSHIFT] = 1
        camera.last_scrolled = -1000
        camera.scroll(keystate)
        self.assertTrue(camera.y >= 0)

    def test_left_and_right_scrolling(self):
        """Ensure user can scroll the camera left and right.
        """
        camera = Camera()
        
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_A] = 1
        camera.last_scrolled = -1000
        camera.scroll(keystate)
        self.assertTrue(camera.x < 0)
        
        keystate[sdl2.SDL_SCANCODE_A] = 0
        keystate[sdl2.SDL_SCANCODE_RIGHT] = 1
        keystate[sdl2.SDL_SCANCODE_RSHIFT] = 1
        camera.last_scrolled = -1000
        camera.scroll(keystate)
        self.assertTrue(camera.x >= 0)

class PanelTests(unittest.TestCase):
    """Tests for the Panel class (controller.py)."""

    def test_mouse_over(self):
        """Ensure that mouse_over detects the user placing their
        mouse over a button.
        """
        panel = Panel(1)
        panel.buttons.add(Button(1, 1, 0, 0, 0.1, 0.1))
        panel.buttons.add(Button(2, 1, 0.2, 0, 0.1, 0.1))

        self.assertFalse(panel.mouse_over(500, 500, [1920, 1080]))
        self.assertTrue(panel.mouse_over(0, 0, [1920, 1080]))
        self.assertEqual(panel.button_over, 1)

if __name__ == '__main__':
    unittest.main()