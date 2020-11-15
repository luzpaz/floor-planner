import ctypes
import polling
import sdl2
import threading
import unittest
import os.path

from app import App
from controller import Controller, Camera, Text, CenterText, Button, Panel,\
    MessageStack
from ctypes import c_int, pointer
from entities import Line
from entity_types import EntityType
from model import Model
from polling import PollingType
from tools import Tools, ExportCommand
from view import View, Textures, FontSize

class LineTests(unittest.TestCase):
    """Tests for the Line class (entities.py)."""

    horizontal_line = Line((0, 0), (5, 0))
    vertical_line = Line((0, 0), (0, 5))
    diagonal_line = Line((0, 0), (5, 5))

    def test_base_point_collision(self):
        """Ensures check_point_collision properly catches a point collision
        where the location is colliding with the line.
        """
        self.assertTrue(
            LineTests.horizontal_line.check_point_collision((0, 0)))
        self.assertTrue(
            LineTests.horizontal_line.check_point_collision((2, 0)))
        self.assertTrue(
            LineTests.horizontal_line.check_point_collision((5, 0)))

    def test_no_point_collision(self):
        """Ensures check_point_collision properly ignores a point collision
        where the location is not colliding with the line.
        """
        self.assertFalse(
            LineTests.horizontal_line.check_point_collision((0, 100)))
        self.assertFalse(
            LineTests.horizontal_line.check_point_collision((0, -1)))
        self.assertFalse(
            LineTests.horizontal_line.check_point_collision((6, 0)))

    def test_base_rectangle_collision(self):
        """Ensures check_rectangle_collision properly catches a rectangle
        collision where the rectangle is overlapping with the line.
        """

        # Complete overlap
        self.assertTrue(LineTests.horizontal_line.check_rectangle_collision(
                        sdl2.SDL_Rect(2, 0, 5, 5)))
        
        # Partial overlap right side
        self.assertTrue(LineTests.diagonal_line.check_rectangle_collision(
                        sdl2.SDL_Rect(2, 0, 2, 7)))
        
        # Partial overlap bottom side
        self.assertTrue(LineTests.vertical_line.check_rectangle_collision(
                        sdl2.SDL_Rect(-2, 0, 5, 5)))

        # Edge overlap only
        self.assertTrue(LineTests.horizontal_line.check_rectangle_collision(
                        sdl2.SDL_Rect(5, 0, 5, 5)))

    def test_no_rectangle_collision(self):
        """Ensures check_rectangle_collision properly ignores a rectangle
        collision where the rectangle is not overlapping with the line.
        """
        self.assertFalse(LineTests.horizontal_line.check_rectangle_collision(
                        sdl2.SDL_Rect(-6, 0, 5, 5)))
        self.assertFalse(LineTests.diagonal_line.check_rectangle_collision(
                        sdl2.SDL_Rect(6, 3, 2, 2)))

    def test_zero_distance(self):
        """Ensure distance returns 0 if the two vertices are the same.
        """
        self.assertEqual(Line.distance((10, 15), (10, 15)), 0.0)

    def test_base_distance(self):
        """Ensure distance returns correct answer for a base case.
        """
        self.assertEqual(Line.distance((0, 5), (5, 5)), 5.0)

    def test_large_distance(self):
        """Ensure distance works with large integers.
        """
        self.assertEqual(Line.distance((1E20, 5E30), (1E15, 3E6)), 5E30)

    def test_base_intersection(self):
        """Ensure intersect properly detects lines intersecting.
        """
        # Diagonal and horizontal
        self.assertTrue(Line.intersect((0, 0), (5, 5), (0, 2), (5, 2)))

        # Two diagonals
        self.assertTrue(Line.intersect((0, 0), (25, 25), (25, 0), (0, 25)))

    def test_no_intersection(self):
        """Ensure intersect properly ignores non-intersecting lines.
        """
        # Parallel
        self.assertFalse(Line.intersect((0, 0), (5, 0), (0, 2), (5, 2)))

        # Overlap only
        self.assertFalse(Line.intersect((0, 0), (5, 5), (0, 0), (5, 5)))

class ControllerTests(unittest.TestCase):
    """Tests for the Controller class (controller.py)."""

    def test_handle_text_input(self):
        """Ensure user typing (from the keyboard) is properly captured. Ensure
        only digits are accepted as input. If the user enters something that is
        not a digit, ensure the text is cleared.
        """
        controller = Controller()
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_TEXTINPUT

        event.text.text = b'1'
        controller.handle_text_input(event)
        self.assertEqual(controller.text, '1');

        event.text.text = b'0'
        controller.handle_text_input(event)
        self.assertEqual(controller.text, '10');

        event.text.text = b'a'
        controller.handle_text_input(event)
        self.assertEqual(controller.text, '');

    def test_update_bottom_right_text(self):
        """Ensure the bottom right text displays the current mouse coordinates
        and camera scale.
        """
        controller = Controller()
        controller.mouse_x = 500
        controller.mouse_y = 0

        controller.update_bottom_right_text()
        self.assertEqual(controller.center_text.text[
            CenterText.BOTTOM_RIGHT_TEXT].text, 'X: 500 Y: 0 Zoom: 1.0')

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
        """Ensure multiple selected entites are captured when the mouse
        selection is colliding with all of them.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (10, 10))
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 30), (10, 2))
        app.controller.mouse_selection = sdl2.SDL_Rect(0, 0, 500, 500)
        app.controller.handle_multiple_entity_selection(app.model)
        self.assertEqual(len(app.controller.selected_entities), 2)

    def test_camera_pan(self):
        """Ensure handle_camera_pan correctly adjusts the camera position
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
        """Ensure handle_mouse_drag properly captures the starting point
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
        """Ensure handle_mouse_drag properly updates the mouse_selection
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

    def test_get_mouse_location(self):
        """Ensure get_mouse_location gets called with no error.
        This functionality is better tested with other methods
        and interactive testing.
        """
        controller = Controller()
        controller.get_mouse_location()
        self.assertEqual(controller.mouse_x, 0)
        self.assertEqual(controller.mouse_y, 0)

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
        handle_two_point_placement properly sets the class values.
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
        app.controller.line_type = EntityType.EXTERIOR_WALL

        # Horizontal line
        app.controller.horizontal_line = True
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(len(app.model.lines), 1)
        
        # Vertical line
        app.controller.first_point_placed = True
        app.controller.horizontal_line = False
        app.controller.vertical_line = True
        app.controller.line_type = EntityType.EXTERIOR_WALL
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(len(app.model.lines), 2)
        
        # Diagonal line
        app.controller.first_point_placed = True
        app.controller.vertical_line = False
        app.controller.line_type = EntityType.EXTERIOR_WALL
        app.controller.handle_two_point_placement(event, keystate, app.model)
        self.assertEqual(len(app.model.lines), 3)

    def test_two_point_placement_text(self):
        """Ensure the correct length text is displayed when the user is
        placing the second point.
        """
        app = App()
        event = sdl2.SDL_Event()
        keystate = sdl2.SDL_GetKeyboardState(None)
        app.controller.first_point_placed = True
        app.controller.line_type = EntityType.EXTERIOR_WALL
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

    def test_mouse_selection(self):
        """Ensure get_mouse_selection returns the mouse selection adjusted
        to the user camera's position.
        """
        controller = Controller()

        self.assertEqual(controller.get_mouse_selection(),
                         sdl2.SDL_Rect(0, 0, 0, 0))

        controller.mouse_selection = sdl2.SDL_Rect(500, 500, 50, 50)

        controller.camera.x = 500
        controller.camera.y = 500

        expected = sdl2.SDL_Rect(0, 0, 50, 50)
        self.assertEqual(controller.get_mouse_selection(), expected)

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

class ModelTests(unittest.TestCase):
    """Tests for the Model class (model.py)."""
    app = App()

    def test_add_exterior_wall(self):
        """Ensure add_line properly adds a new exterior wall.
        """
        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))
        self.assertEqual(len(ModelTests.app.model.lines), 1)
        self.assertEqual(ModelTests.app.model.lines.pop().thickness,
                         Line.EXTERIOR_WALL)
        self.assertTrue(ModelTests.app.model.update_needed)

    def test_add_interior_wall(self):
        """Ensure add_line properly adds a new interior wall.
        """
        ModelTests.app.model.add_line(EntityType.INTERIOR_WALL, (0, 0), (3, 3))
        self.assertEqual(len(ModelTests.app.model.lines), 1)
        self.assertEqual(ModelTests.app.model.lines.pop().thickness,
                         Line.INTERIOR_WALL)
        self.assertTrue(ModelTests.app.model.update_needed)

    def test_add_vertices_from_line(self):
        """Ensure add_vertices_from_line properly adds line
        vertices after adding a new line.
        """
        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (2, 6), (1, 3))
        self.assertEqual(len(ModelTests.app.model.lines), 1)

        self.assertTrue((2, 6) in ModelTests.app.model.vertices)
        self.assertTrue((1, 3) in ModelTests.app.model.vertices)
        
        ModelTests.clear_lines_and_verticies()

    def test_remove_line(self):
        """Ensure remove_entity properly removes a line and its vertices
        from the model.
        """
        ModelTests.app.model.vertices.clear()
        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (1, 8))
        for line in ModelTests.app.model.lines:
            if line.start == (0, 0) and line.end == (1, 8):
                break

        self.assertIsNotNone(line)
        self.assertEqual(len(ModelTests.app.model.lines), 1)
        self.assertEqual(len(ModelTests.app.model.vertices), 2)
        
        ModelTests.app.model.remove_entity(line)

        self.assertEqual(len(ModelTests.app.model.lines), 0)
        self.assertEqual(len(ModelTests.app.model.vertices), 0)
        self.assertTrue(ModelTests.app.model.update_needed)

    def test_base_get_vertex_within_range(self):
        """Ensure get_vertex_within_range returns the closest vertex when
        there is only one vertex.
        """
        ModelTests.app.model.vertices.add((0, 0))
        self.assertEqual(ModelTests.app.model.get_vertex_within_range((0, 0)),
                         (0, 0))
        ModelTests.app.model.vertices.clear()

        ModelTests.app.model.vertices.add((1, 2))
        self.assertEqual(ModelTests.app.model.get_vertex_within_range((0, 0)),
                         (1, 2))
        ModelTests.app.model.vertices.clear()

    def test_multiple_get_vertex_within_range(self):
        """Ensure get_vertex_within_range returns the closest vertex when
        there are multiple vertices.
        """
        ModelTests.app.model.vertices.add((0, 0))
        ModelTests.app.model.vertices.add((1, 3))
        ModelTests.app.model.vertices.add((5, 6))
        self.assertEqual(ModelTests.app.model.get_vertex_within_range((0, 2)),
                         (1, 3))
        ModelTests.app.model.vertices.clear()

    def test_none_get_vertex_within_range(self):
        """Ensure get_vertex_within_range returns None when no vertices
        are within the range
        """
        ModelTests.app.model.vertices.add((0, 0))
        ModelTests.app.model.vertices.add((1, 3))
        ModelTests.app.model.vertices.add((5, 6))
        self.assertIsNone(ModelTests.app.model.get_vertex_within_range((30, 2)))
        ModelTests.app.model.vertices.clear()

    def test_base_vertex_on_axis(self):
        """Ensure get_vertex_on_axis returns the closest axis when
        there is only one vertex.
        """
        ModelTests.app.model.vertices.add((0, 0))
        self.assertEqual(ModelTests.app.model.get_vertex_on_axis((0, 5), True),
                         (0, 0))
        ModelTests.app.model.vertices.clear()

        ModelTests.app.model.vertices.add((0, 0))
        self.assertEqual(ModelTests.app.model.get_vertex_on_axis((5, 0), False),
                         (0, 0))
        ModelTests.app.model.vertices.clear()

    def test_multiple_vertex_on_axis(self):
        """Ensure get_vertex_on_axis returns the closest axis when
        there are multiple vertices.
        """
        ModelTests.app.model.vertices.add((0, 0))
        ModelTests.app.model.vertices.add((0, 12))
        ModelTests.app.model.vertices.add((0, 15))
        self.assertEqual(ModelTests.app.model.get_vertex_on_axis((0, 5), True),
                         (0, 0))
        ModelTests.app.model.vertices.clear()

    def test_none_vertex_on_axis(self):
        """Ensure get_vertex_on_axis returns None when there are no axises
        that align with the origin
        """
        ModelTests.app.model.vertices.add((0, 0))
        self.assertIsNone(ModelTests.app.model.get_vertex_on_axis((1, 5)))
        ModelTests.app.model.vertices.clear()

    def test_base_entity_on_location(self):
        """Ensure get_entity_on_location returns the line that the location
        collidies with when the location is directly on the line
        """
        ModelTests.app.model.add_line(EntityType.INTERIOR_WALL, (0, 0), (2, 2))
        
        for line in ModelTests.app.model.lines:
            if line.start == (0, 0) and line.end == (2, 2):
                break

        self.assertEqual(
            ModelTests.app.model.get_entity_on_location((1, 1)), line)
        ModelTests.clear_lines_and_verticies()

    def test_none_for_entity_on_location(self):
        """Ensure get_entity_on_location returns None when the location is not
        colliding with the line
        """
        ModelTests.app.model.add_line(EntityType.INTERIOR_WALL, (0, 0), (2, 2))
        self.assertIsNone(ModelTests.app.model.get_entity_on_location((3, 1)))
        ModelTests.clear_lines_and_verticies()

    def test_empty_entity_on_location(self):
        """Ensure get_entity_on_location returns None when there are no
        entities to collide with
        """
        self.assertIsNone(ModelTests.app.model.get_entity_on_location((0, 0)))

    def test_base_entities_in_rectangle(self):
        """Ensure get_entities_in_rectangle returns correct set of entities
        when rectangle collides with a single entity
        """

        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))
        
        for line in ModelTests.app.model.lines:
            if line.start == (0, 0) and line.end == (5, 5):
                break

        entities = set()
        entities.add(line)

        self.assertEqual(ModelTests.app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(1, 1, 5, 5)), entities)
        ModelTests.clear_lines_and_verticies()

    def test_multiple_entities_in_rectangle(self):
        """Ensure get_entities_in_rectangle returns correct set of entities
        when rectangle collides with multiple entities
        """

        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))
        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (5, 5), (0, 0))
        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (2, 0), (2, 5))
        self.assertEqual(len(ModelTests.app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(0, 0, 5, 5))), 3)
        ModelTests.clear_lines_and_verticies()

    def test_no_enitities_rectangle(self):
        """Ensure get_entities_in_rectangle returns empty set of entities
        when rectangle does not collide with any entities
        """

        ModelTests.app.model.add_line(EntityType.EXTERIOR_WALL, (2, 3), (6, 7))
        entities = set()
        self.assertEqual(ModelTests.app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(10, 1, 4, 4)), entities)
        ModelTests.clear_lines_and_verticies()

    def clear_lines_and_verticies():
        """Removes lines and vertices from the model.
        """
        ModelTests.app.model.lines.clear()
        ModelTests.app.model.vertices.clear()

class AppTests(unittest.TestCase):
    """Tests for the App class (app.py)."""

    def test_initialization(self):
        """Ensure the app constructor properly initializes the components.
        """
        app = App()
        self.assertIsInstance(app.model, Model)
        self.assertIsInstance(app.controller, Controller)
        self.assertIsInstance(app.view, View)

    def test_app_loop(self):
        """TO DO: Ensure the app loop runs and exits.
        """
        pass

class ViewTests(unittest.TestCase):
    """Tests for the View class (view.py)."""
    app = App()

    def test_initialization(self):
        """Ensure the view constructor properly initializes the SDL
        components and textures.
        """
        self.assertIsNotNone(ViewTests.app.view.window)
        self.assertIsNotNone(ViewTests.app.view.renderer)
        self.assertIsInstance(ViewTests.app.view.textures, Textures)

    def test_camera_values(self):
        """Ensure view properly takes in the UI camera's position and scale.
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
        """Ensure correct number of entities are rendered onto the layer.
        """
        for i in range(5):
            ViewTests.app.model.add_line(EntityType.EXTERIOR_WALL)

        self.assertEqual(ViewTests.app.view.update_layer(
            ViewTests.app.model, ViewTests.app.controller), 5)

        ViewTests.app.model.lines.clear()

    def test_render_ui_text(self):
        """Ensure correct number of text displayers are rendered from the UI.
        """
        self.assertEqual(ViewTests.app.view.render_ui_text(
            ViewTests.app.controller), 3)

    def test_empty_render_text(self):
        """Ensure render text returns None if the text is None or if the text
        string is empty.
        """
        self.assertIsNone(ViewTests.app.view.render_text(None))
        self.assertIsNone(ViewTests.app.view.render_text(Text()))

    def test_render_text(self):
        """Ensure render_text completes rendering of a non-empty text.
        """
        text = Text()
        text.text = 'Non empty text'

        self.assertTrue(ViewTests.app.view.render_text(text))

        text.font = FontSize.MEDIUM
        self.assertTrue(ViewTests.app.view.render_text(text))

        text.font = FontSize.LARGE
        self.assertTrue(ViewTests.app.view.render_text(text))

    def test_center_text(self):
        """Ensures center_text returns the correct values for base cases.
        """
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

    def test_destructor(self):
        """Ensures destructor clears textures and sets SDL components to None.
        """
        view = View()
        view.exit()
        self.assertIsNone(view.window)
        self.assertIsNone(view.renderer)
        self.assertEqual(len(view.textures.textures), 0)
        
class TexturesTests(unittest.TestCase):
    """Tests for the Texture class (view.py)."""
    app = App()

    def test_create_and_get(self):
        """Ensure textures can create and get a test texture.
        """
        TexturesTests.app.view.textures.textures[0]\
            = TexturesTests.app.view.textures.create(
            TexturesTests.app.view.renderer, b'textures/test.png')

        texture = TexturesTests.app.view.textures.get(0)
        self.assertIsNotNone(texture)

        # Ensure texture has correct size (matches png file).
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
        """Ensure that mouse_over properly detects the user placing their
        mouse over a button.
        """
        panel = Panel(1)
        panel.buttons.add(Button(1, 1, 0, 0, 0.1, 0.1))
        panel.buttons.add(Button(2, 1, 0.2, 0, 0.1, 0.1))

        self.assertFalse(panel.mouse_over(500, 500, [1920, 1080]))
        self.assertTrue(panel.mouse_over(0, 0, [1920, 1080]))
        self.assertEqual(panel.button_over, 1)

class PollingTests(unittest.TestCase):
    """Tests for classes in the polling.py module."""

    def test_erasing(self):
        """Ensure the erasing poll event handler clears the selected entities.
        """
        app = App()
        line = app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (0, 0))

        app.controller.selected_entities.add(line)
        app.controller.polling = PollingType.ERASING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(len(app.model.lines), 0)

    def test_drawing(self):
        """Ensure the drawing poll event handler begins two point placement.
        """
        app = App()
        app.controller.polling = PollingType.DRAWING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)

class ToolsTests(unittest.TestCase):
    """Tests for classes in the tools.py module."""

    def test_base_convert_to_unit_system(self):
        """Ensure converting to ft and inches returns the expected values.
        """
        self.assertEqual(Tools.convert_to_unit_system(12), '1 ft 0 in')
        self.assertEqual(Tools.convert_to_unit_system(15), '1 ft 3 in')
        self.assertEqual(Tools.convert_to_unit_system(50), '4 ft 2 in')
        self.assertEqual(Tools.convert_to_unit_system(-5), '0 ft 5 in')
        self.assertEqual(Tools.convert_to_unit_system(0, ''), '')

    def test_export_command(self):
        """Ensure the export command creates an export.png file, signaling
        that it has successfully exported the texture.
        """
        app = App()
        app.commands.append(ExportCommand())
        app.execute_commands()
        self.assertTrue(os.path.isfile('export.png'))

if __name__ == '__main__':
    unittest.main()