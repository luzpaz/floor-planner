import sdl2, sys, unittest
sys.path.append("..\src")

from app import App
from entity_types import EntityType
from entities import Line, RectangularEntity, Door, Window, UserText
from model import Model

class ModelTests(unittest.TestCase):
    """Tests for the Model class (model.py)."""

    def test_add_exterior_wall(self):
        """Ensure add_line adds a new exterior wall.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))
        self.assertEqual(len(app.model.lines), 1)
        self.assertEqual(app.model.lines.pop().thickness,
                         Line.EXTERIOR_WALL)
        self.assertTrue(app.model.update_needed)

    def test_add_interior_wall(self):
        """Ensure add_line adds a new interior wall.
        """
        app = App()
        app.model.add_line(EntityType.INTERIOR_WALL, (0, 0), (3, 3))
        self.assertEqual(len(app.model.lines), 1)
        self.assertEqual(app.model.lines.pop().thickness,
                         Line.INTERIOR_WALL)
        self.assertTrue(app.model.update_needed)

    def test_add_vertices_from_line(self):
        """Ensure add_vertices_from_line adds line
        vertices after adding a new line.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (2, 6), (1, 3))
        self.assertEqual(len(app.model.lines), 1)

        self.assertTrue((2, 6) in app.model.vertices)
        self.assertTrue((1, 3) in app.model.vertices)
        
    def test_remove_line(self):
        """Ensure remove_entity removes a line and its vertices
        from the model.
        """
        app = App()
        app.model.vertices.clear()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (1, 8))
        for line in app.model.lines:
            if line.start == (0, 0) and line.end == (1, 8):
                break

        self.assertIsNotNone(line)
        self.assertEqual(len(app.model.lines), 1)
        self.assertEqual(len(app.model.vertices), 2)
        
        app.model.remove_entity(line)

        self.assertEqual(len(app.model.lines), 0)
        self.assertEqual(len(app.model.vertices), 0)
        self.assertTrue(app.model.update_needed)

    def test_base_get_vertex_within_range(self):
        """Ensure get_vertex_within_range returns the closest vertex when
        there is only one vertex.
        """
        app = App()
        app.model.vertices.add((0, 0))
        self.assertEqual(app.model.get_vertex_within_range((0, 0)),
                         (0, 0))
        app.model.vertices.clear()

        app.model.vertices.add((1, 2))
        self.assertEqual(app.model.get_vertex_within_range((0, 0)),
                         (1, 2))
        app.model.vertices.clear()

    def test_multiple_get_vertex_within_range(self):
        """Ensure get_vertex_within_range returns the closest vertex when
        there are multiple vertices.
        """
        app = App()
        app.model.vertices.add((0, 0))
        app.model.vertices.add((1, 3))
        app.model.vertices.add((5, 6))
        self.assertEqual(app.model.get_vertex_within_range((0, 2)),
                         (1, 3))
        app.model.vertices.clear()

    def test_none_get_vertex_within_range(self):
        """Ensure get_vertex_within_range returns None when no vertices
        are within the range
        """
        app = App()
        app.model.vertices.add((0, 0))
        app.model.vertices.add((1, 3))
        app.model.vertices.add((5, 6))
        self.assertIsNone(app.model.get_vertex_within_range((30, 2)))
        app.model.vertices.clear()

    def test_base_vertex_on_axis(self):
        """Ensure get_vertex_on_axis returns the closest axis when
        there is only one vertex.
        """
        app = App()
        app.model.vertices.add((0, 0))
        self.assertEqual(app.model.get_vertex_on_axis((0, 5), True),
                         (0, 0))
        app.model.vertices.clear()

        app.model.vertices.add((0, 0))
        self.assertEqual(app.model.get_vertex_on_axis((5, 0), False),
                         (0, 0))
        app.model.vertices.clear()

    def test_multiple_vertex_on_axis(self):
        """Ensure get_vertex_on_axis returns the closest axis when
        there are multiple vertices.
        """
        app = App()
        app.model.vertices.add((0, 0))
        app.model.vertices.add((0, 12))
        app.model.vertices.add((0, 15))
        self.assertEqual(app.model.get_vertex_on_axis((0, 5), True),
                         (0, 0))
        app.model.vertices.clear()

    def test_none_vertex_on_axis(self):
        """Ensure get_vertex_on_axis returns None when there are no axes
        that align with the origin.
        """
        app = App()
        app.model.vertices.add((0, 0))
        self.assertIsNone(app.model.get_vertex_on_axis((1, 5)))
        app.model.vertices.clear()

    def test_base_entity_on_location(self):
        """Ensure get_entity_on_location returns the line that the location
        collides with when the location is directly on the line.
        """
        app = App()
        app.model.add_line(EntityType.INTERIOR_WALL, (0, 0), (2, 2))
        
        for line in app.model.lines:
            if line.start == (0, 0) and line.end == (2, 2):
                break

        self.assertEqual(
            app.model.get_entity_on_location((1, 1)), line)
        
    def test_none_for_entity_on_location(self):
        """Ensure get_entity_on_location returns None when the location is not
        colliding with the line.
        """
        app = App()
        app.model.add_line(EntityType.INTERIOR_WALL, (0, 0), (2, 2))
        self.assertIsNone(app.model.get_entity_on_location((3, 1)))
        
    def test_empty_entity_on_location(self):
        """Ensure get_entity_on_location returns None when there are no
        entities to collide with.
        """
        app = App()
        self.assertIsNone(app.model.get_entity_on_location((0, 0)))

    def test_base_entities_in_rectangle(self):
        """Ensure get_entities_in_rectangle returns expected set of entities
        when rectangle collides with a single entity.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))

        text = UserText('Test Text', (3, 3))
        app.model.add_entity(text)
        
        for line in app.model.lines:
            break

        entities = set()
        entities.add(line)
        entities.add(text)

        self.assertEqual(app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(1, 1, 5, 5)), entities)
        
    def test_multiple_entities_in_rectangle(self):
        """Ensure get_entities_in_rectangle returns expected set of entities
        when rectangle collides with multiple entities.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))
        app.model.add_line(EntityType.EXTERIOR_WALL, (5, 5), (0, 0))
        app.model.add_line(EntityType.EXTERIOR_WALL, (2, 0), (2, 5))
        self.assertEqual(len(app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(0, 0, 5, 5))), 3)
        
    def test_entities_in_rectangle_for_rectangulars(self):
        """Ensure get_entities_in_rectangle returns expected set of entities
        when rectangle collides with multiple doors and windows.
        """
        app = App()
        app.model.add_window((0, 0))
        app.model.add_door((4, 2))
        self.assertEqual(len(app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(0, 0, 5, 5))), 2)

    def test_no_enitities_rectangle(self):
        """Ensure get_entities_in_rectangle returns empty set of entities
        when rectangle does not collide with any entities.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (2, 3), (6, 7))
        entities = set()
        self.assertEqual(app.model.get_entities_in_rectangle(
            sdl2.SDL_Rect(10, 1, 4, 4)), entities)
        
    def test_get_inventory(self):
        """Ensure get_inventory returns the expected output when adding
        exterior walls and interior walls of the same length.
        """
        app = App()
        self.assertEqual(app.model.get_inventory(), '')

        for i in range(2):
            app.model.add_line(EntityType.EXTERIOR_WALL,
                                      (0, 0), (0, 12))
        for i in range(4):
            app.model.add_line(EntityType.INTERIOR_WALL,
                                      (0, 0), (0, 24))

        inventory = 'Exterior wall: 2 x 1 ft 0 in\n'\
            + 'Interior wall: 4 x 2 ft 0 in\n'
        
        self.assertEqual(app.model.get_inventory(), inventory)
        
    def test_remove_doors_and_windows(self):
        """Ensure model can add and remove doors and windows.
        """
        app = App()
        window = app.model.add_window()
        door = app.model.add_door()

        self.assertEqual(len(app.model.windows), 1)
        self.assertEqual(len(app.model.doors), 1)

        app.model.remove_entity(window)
        app.model.remove_entity(door)

        self.assertEqual(len(app.model.windows), 0)
        self.assertEqual(len(app.model.doors), 0)

    def test_closing_gaps_between_walls(self):
        """Ensure the expected number of square vertices are added to close gaps
        after adding exterior walls that connect.
        """
        app = App()
        app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (5, 5))
        app.model.add_line(EntityType.EXTERIOR_WALL, (5, 5), (0, 0))
        self.assertEqual(len(app.model.square_vertices), 4)

    def test_add_door(self):
        """Ensure door is added to the model using the add_entity method.
        """
        model = Model()

        door = Door()
        model.add_entity(door)
        self.assertEqual(len(model.doors), 1)

        for first_door in model.doors:
            break
        self.assertEqual(first_door, door)

    def test_add_window(self):
        """Ensure window is added to the model using the add_entity method.
        """
        model = Model()

        window = Window()
        model.add_entity(window)
        self.assertEqual(len(model.windows), 1)

        for first_window in model.windows:
            break
        self.assertEqual(first_window, window)

if __name__ == '__main__':
    unittest.main()