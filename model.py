import math
import sdl2
import sys
import threading

from entities import Line, Rectangle, UserText
from entity_types import EntityType, ModelMutex
from threading import Lock

class Model:
    """The class responsible for containing entities and
    performing queries on them."""

    def __init__(self):
        """Initializes entity containers.
        """
        self.lines = set()
        self.vertices = set()
        self.rectangles = set()

        self.user_text = set()

        # Whether the renderer must update the layers
        self.update_needed = False

        self.update_background = threading.Condition()

        # Mutexes for accessing the sets
        self.mutexes = {}
        self.mutexes[ModelMutex.LINES] = Lock()
        self.mutexes[ModelMutex.VERTICES] = Lock()
        self.mutexes[ModelMutex.RECTANGLES] = Lock()

    def add_line(self, type, start = (0, 0), end = (0, 0), color = (0, 0, 0)):
        """Adds a line and its vertices to the model.
        :param start: The starting vertex of the line
        :param end: The ending vertex of the line
        :type start, end: tuple(int, int)
        :param color: The r, g, b values for the line's rendering color
        :type color: tuple(int, int, int)
        """
        line = None

        # TO DO: use abstract factory
        if type == EntityType.EXTERIOR_WALL:
            with self.mutexes[ModelMutex.LINES]:
                line = Line(start, end, Line.EXTERIOR_WALL, color)
                self.lines.add(line)
                self.update_verticies()
        elif type == EntityType.INTERIOR_WALL:
            with self.mutexes[ModelMutex.LINES]:
                line = Line(start, end, Line.INTERIOR_WALL, color)
                self.lines.add(line)
                self.update_verticies()
        elif type == EntityType.REGULAR_LINE:
            with self.mutexes[ModelMutex.LINES]:
                line = Line(start, end, Line.REGULAR_LINE, color)
                self.lines.add(line)
                self.update_verticies()

        self.update_needed = True

        with self.update_background:
            self.update_background.notify_all()

        return line

    def add_vertices_from_line(self, line):
        """Adds starting and ending vertices of the line to the model.
        :param line: The line to add vertices for
        :type line: Line from 'entities.py'
        """

        self.vertices.add((line.start[0], line.start[1]))
        self.vertices.add((line.end[0], line.end[1]))

    def add_user_text(self, text = '', position = (0, 0)):
        """Adds user text to the absolute position.
        :param text: Text to add
        :type text: str
        :param position: Absolute position of the text
        :type position: tuple(int, int)
        """
        self.user_text.add(UserText(text, position))
        self.update_needed = True

    def remove_entity(self, entity):
        """Removes entity from the model.
        :param entity: The entity to remove
        :type entity: Any entity type stored by the model
        """

        if isinstance(entity, Line):
            with self.mutexes[ModelMutex.LINES]:
                start = entity.start
                end = entity.end
                self.lines.remove(entity)
                self.update_verticies()

        self.update_needed = True

        with self.update_background:
            self.update_background.notify_all()

    def update_verticies(self):
        """Clears current vertices and re-adds them for each line.
        """
        with self.mutexes[ModelMutex.VERTICES]:
            self.vertices = set()

            for line in self.lines:
                self.add_vertices_from_line(line)

    def get_vertex_within_range(self, origin = (0, 0), range = 12):
        """Returns nearest vertex from the origin that is within the range
        :param origin: Position to search for closest vertex
        :type origin: tuple(int, int)
        :param range: Amount of distance to search for closest vertex
        :type range: int
        """

        nearest_vertex = None
        nearest_vertex_distance = sys.maxsize
        
        for vertex in self.vertices:
            distance = Line.distance(vertex, origin)

            if distance > range:
                continue

            if distance < nearest_vertex_distance:
                nearest_vertex = vertex
                nearest_vertex_distance = distance

        return nearest_vertex

    def get_vertex_on_axis(self, origin = (0, 0), horizontal = True):
        """Returns nearest vertex that is on the same horizontal or vertical
        axis as the origin vertex
        :param origin: Location to search axis for
        :type origin: tuple(int, int)
        :param horizontal: Whether the origin line is horizontal or vertical
        :type horizontal: boolean
        """

        nearest_vertex = None
        nearest_vertex_distance = sys.maxsize
        
        for vertex in self.vertices:
            if horizontal:
                axis_distance = abs(vertex[0] - origin[0])
            else:
                axis_distance = abs(vertex[1] - origin[1])

            if axis_distance != 0:
                continue

            distance = Line.distance(vertex, origin)

            if distance < nearest_vertex_distance:
                nearest_vertex = vertex
                nearest_vertex_distance = distance

        return nearest_vertex

    def get_entity_on_location(self, location = (0, 0)):
        """Returns single entity that collides with the location
        :param location: Position coordinates to check collision against
        :type location: tuple(int, int)
        """

        for line in self.lines:
            if line.check_point_collision(location):
                return line
        return None

    def get_entities_in_rectangle(self, rectangle = sdl2.SDL_Rect()):
        """Returns set of entities that collide with the rectangle
        :param rectangle: Rectangle to check collision against
        (x = top-left x-position, y = top-left y-position,
        w = width, h = height)
        :type rectangle: SDL_Rect
        """

        entities = set()
        for line in self.lines:
            line.selected = False
            if line.check_rectangle_collision(rectangle):
                entities.add(line)
                line.selected = True
        
        self.update_needed = True
        return entities