import sdl2, sys, unittest
sys.path.append("..\src")

from entities import Line, RectangularEntity, Door, Window
from entity_types import EntityType
from model import Model

class LineTests(unittest.TestCase):
    """Tests for the Line class (entities.py)."""

    horizontal_line = Line((0, 0), (5, 0))
    vertical_line = Line((0, 0), (0, 5))
    diagonal_line = Line((0, 0), (5, 5))

    def test_base_point_collision(self):
        """Ensures check_point_collision catches a point collision
        where the location is colliding with the line.
        """
        self.assertTrue(
            LineTests.horizontal_line.check_point_collision((0, 0)))
        self.assertTrue(
            LineTests.horizontal_line.check_point_collision((2, 0)))
        self.assertTrue(
            LineTests.horizontal_line.check_point_collision((5, 0)))

    def test_no_point_collision(self):
        """Ensures check_point_collision ignores a point collision
        where the location is not colliding with the line.
        """
        self.assertFalse(
            LineTests.horizontal_line.check_point_collision((0, 100)))
        self.assertFalse(
            LineTests.horizontal_line.check_point_collision((0, -1)))
        self.assertFalse(
            LineTests.horizontal_line.check_point_collision((6, 0)))

    def test_base_rectangle_collision(self):
        """Ensures check_rectangle_collision catches a rectangle
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
        """Ensures check_rectangle_collision ignores a rectangle
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
        """Ensure distance returns expected answer for a base case.
        """
        self.assertEqual(Line.distance((0, 5), (5, 5)), 5.0)

    def test_base_intersection(self):
        """Ensure intersect detects lines intersecting.
        """
        # Diagonal and horizontal
        self.assertTrue(Line.intersect((0, 0), (5, 5), (0, 2), (5, 2)))

        # Two diagonals
        self.assertTrue(Line.intersect((0, 0), (25, 25), (25, 0), (0, 25)))

    def test_no_intersection(self):
        """Ensure intersect ignores non-intersecting lines.
        """
        # Parallel
        self.assertFalse(Line.intersect((0, 0), (5, 0), (0, 2), (5, 2)))

        # Overlap only
        self.assertFalse(Line.intersect((0, 0), (5, 5), (0, 0), (5, 5)))

    def test_point_intersection(self):
        """Ensure intersection returns the intersecting point between two lines.
        """
        self.assertEqual(Line.intersection((0, 0), (5, 0), (2, -1), (2, 4)),
                         (2, 0))

    def test_move_start_vertex(self):
        """Ensure moving a line with the start vertex as the reference
        adjusts the start and end vertices accurately.
        """
        line = Line((0, 0), (10, 0))
        line.move(10, 0, True)
        self.assertEqual(line.start, (10, 0))
        self.assertEqual(line.end, (20, 0))

    def test_move_end_vertex_same_location(self):
        """Ensure moving a line with the end vertex to the same position does
        not affect the start and end veritices of the line.
        """
        line = Line((0, 0), (10, 0))
        line.move(10, 0, False)
        self.assertEqual(line.start, (0, 0))
        self.assertEqual(line.end, (10, 0))

class RectangularTests(unittest.TestCase):
    """Tests for the RectangularEntity class (entities.py)."""
    rectangle = RectangularEntity(sdl2.SDL_Rect(0, 0, 5, 5))

    def test_no_collision(self):
        """Ensure check_collision returns false if the two rectangles
        are not colliding.
        """
        self.assertFalse(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(-10, -10, 5, 5)))

        # Touching on the edge but no overlap
        self.assertFalse(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(-5, -5, 5, 5)))

    def test_base_collision(self):
        """Ensure check_collision returns true if the two rectangles
        are colliding on one side.
        """
        self.assertTrue(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(2, 0, 5, 5)))
        self.assertTrue(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(-2, 0, 5, 5)))
        self.assertTrue(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(0, 3, 5, 5)))
        self.assertTrue(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(0, -3, 5, 5)))

    def test_overlap_collision(self):
        """Ensure check_collision returns true if the two rectangles
        completely overlap.
        """
        self.assertTrue(RectangularTests.rectangle.check_collision(
            sdl2.SDL_Rect(0, 0, 5, 5)))

    def test_move(self):
        """Ensure moving the rectangle from either vertex adjusts the 
        rectangle's x and y positions accurately.
        """
        rectangle = RectangularEntity(sdl2.SDL_Rect(0, 0, 10, 10))
        
        rectangle.move(10, 10, True)
        self.assertEqual(rectangle.x, 10)
        self.assertEqual(rectangle.y, 10)

        rectangle.move(0, 0, False)
        self.assertEqual(rectangle.x, -10)
        self.assertEqual(rectangle.y, -10)

    def test_get_moving_vertex_start(self):
        """Ensure get_moving_vertex returns the start vertex for a horizontal
        and vertical rectangle.
        """

        # Horizontal rectangle
        rectangle = RectangularEntity(sdl2.SDL_Rect(10, 10, 20, 10))
        self.assertEqual(rectangle.get_moving_vertex(True), (10, 15))

        # Vertical rectangle
        rectangle = RectangularEntity(sdl2.SDL_Rect(0, 0, 6, 30))
        self.assertEqual(rectangle.get_moving_vertex(True), (3, 0))

        # Square should be considered horizontal
        square = RectangularEntity(sdl2.SDL_Rect(3, 4, 50, 50))
        self.assertEqual(square.get_moving_vertex(True), (3, 29))

    def test_get_moving_vertex_end(self):
        """Ensure get_moving_vertex returns the end vertex for a horizontal
        and vertical rectangle.
        """

        # Horizontal rectangle
        rectangle = RectangularEntity(sdl2.SDL_Rect(25, 25, 10, 5))
        self.assertEqual(rectangle.get_moving_vertex(False), (35, 27))

        # Vertical rectangle
        rectangle = RectangularEntity(sdl2.SDL_Rect(0, 10, 10, 50))
        self.assertEqual(rectangle.get_moving_vertex(False), (5, 60))
        
    def test_adjusting_window_to_wall(self):
        """Ensure window is snapped to the nearest exterior wall when
        an exterior wall exists.
        """
        model = Model()
        model.add_line(EntityType.EXTERIOR_WALL, (0, 3), (360, 3))

        window = Window(sdl2.SDL_Rect(0, 0, 36, 6))
        window.adjust(model, (180 + Window.LENGTH / 2, Window.WIDTH))

        self.assertEqual(window.x, 180)
        self.assertEqual(window.y, 0)

    def test_adjusting_window_to_no_wall(self):
        """Ensure window does not snap to anything when there is no wall.
        """
        model = Model()

        window = Window(sdl2.SDL_Rect(0, 0, 36, 6))
        window.adjust(model, (150, 150))

        self.assertEqual(window.x, 0)
        self.assertEqual(window.y, 0)

    def test_adjusting_door(self):
        """Ensure door is snapped to the nearest wall when a wall exists.
        """
        model = Model()
        model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (0, 180))

        door = Door(sdl2.SDL_Rect(0, 0, Line.EXTERIOR_WALL, Door.LENGTH))
        door.adjust(model, (0, 90 + Door.LENGTH / 2))

        self.assertEqual(door.x, -3)
        self.assertEqual(door.y, 90)

if __name__ == '__main__':
    unittest.main()