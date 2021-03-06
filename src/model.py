import math, sdl2, sys, threading

from actions import AddAction, DeleteAction
from collections import deque
from entities import Line, Window, Door, UserText, RectangularEntity
from entity_types import EntityType, ModelMutex
from threading import Lock
from tools import Tools

class Model:
    """Contains the application entities and provides queries on them."""

    def __init__(self):
        """Initializes the entity containers, factories, and mutexes.
        """
        self.lines = set()
        self.vertices = set()
        self.windows = set()
        self.doors = set()

        self.user_text = set()

        self.square_vertices = set()

        self.actions = deque()
        self.undos = deque()

        self.update_background = threading.Condition()

        self.line_factory = AbstractLineFactory()

        self.init_mutexes()

        # Whether the renderer must update the layers
        self.update_needed = False

    def add_line(self, type, start = (0, 0), end = (0, 0), color = (0, 0, 0)):
        """Adds a line and its vertices to the model.
        :param start: The starting vertex of the line
        :param end: The ending vertex of the line
        :type start, end: tuple(int, int)
        :param color: The r, g, b values for the line's rendering color
        :type color: tuple(int, int, int)
        """
        line = self.line_factory.create(type, start, end, color)

        if not line:
            return None

        with self.mutexes[ModelMutex.LINES]:
            self.lines.add(line)

        self.update_vertices()
        self.update_needed = True

        with self.update_background:
            self.update_background.notify_all()

        if line:
            self.actions.append(AddAction(line))

        return line

    def add_window(self, location = (0, 0), horizontal = True):
        """Adds a window to the model at the center location.
        :param location: Center location position coordinates for the window
        :type location: tuple(int, int)
        :param horizontal: Whether the window is horizontal or vertical
        :type horizontal: bool
        """

        window = None
        if horizontal:
            window = Window(sdl2.SDL_Rect(
                int(location[0] - Window.LENGTH / 2),
                int(location[1] - Window.WIDTH / 2),
                Window.LENGTH,
                Window.WIDTH))
        else:
            window = Window(sdl2.SDL_Rect(
                int(location[0] - Window.WIDTH / 2),
                int(location[1] - Window.LENGTH / 2),
                Window.WIDTH,
                Window.LENGTH))
            
        with self.mutexes[ModelMutex.WINDOWS]:
            self.windows.add(window)

        self.update_needed = True

        if window:
            self.actions.append(AddAction(window))

        return window
    
    def add_door(self, location = (0, 0), horizontal = True, thickness = 0):
        """Adds a door to the model at the center location.
        :param location: Center location position coordinates for the door
        :type location: tuple(int, int)
        :param horizontal: Whether the door is horizontal or vertical
        :type horizontal: bool
        :param thickness: Thickness of the door
        :type thickness: int
        """

        door = None
        if horizontal:
            door = Door(sdl2.SDL_Rect(
                int(location[0] - Door.LENGTH / 2),
                int(location[1] - thickness / 2),
                Door.LENGTH, thickness))
        else:
            door = Door(sdl2.SDL_Rect(
                int(location[0] - thickness / 2),
                int(location[1] - Door.LENGTH / 2),
                thickness, Door.LENGTH))
            
        with self.mutexes[ModelMutex.DOORS]:
            self.doors.add(door)

        self.update_needed = True

        if door:
            self.actions.append(AddAction(door))

        return door

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
        text = UserText(text, position)

        with self.mutexes[ModelMutex.TEXT]:
            self.user_text.add(text)

        self.update_needed = True
        self.actions.append(AddAction(text))
        return text

    def add_entity(self, entity):
        """Adds the already created entity into the model.
        :param entity: The entity to add
        :type entity: Any entity type stored by the model
        """
        entity.add_to_model(self)

        self.update_needed = True
        with self.update_background:
            self.update_background.notify_all()

    def remove_entity(self, entity, action = True):
        """Removes entity from the model.
        :param entity: The entity to remove
        :type entity: Any entity type stored by the model
        :param action: Whether the user did this removal explicitly.
        :type action: boolean
        """
        if not entity:
            return

        entity.remove_from_model(self)

        self.update_needed = True
        with self.update_background:
            self.update_background.notify_all()

        if action:
            self.actions.append(DeleteAction(entity))

    def update_vertices(self):
        """Clears current vertices and re-adds them for each line.
        """
        with self.mutexes[ModelMutex.VERTICES]:
            self.vertices = set()

            for line in self.lines:
                self.add_vertices_from_line(line)

            self.square_vertices = set()

            for line in self.lines:
                self.close_gaps_between_walls(line)

    def get_vertex_within_range(self, origin = (0, 0), range = 6):
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

    def get_nearest_wall(self, location = (0, 0), exterior_only = False):
        """Returns the nearest horizontal or vertical wall to the
        location and the closest point on that wall,
        for window or door placement.
        :param location: Position coordinates to find nearest wall for
        :type location: tuple(int, int)
        """

        closest_line = None
        closest_point = None
        closest_point_distance = sys.maxsize

        for line in self.lines:
            # Exterior walls only for windows
            if (exterior_only and line.thickness != Line.EXTERIOR_WALL)\
                or (not exterior_only and line.thickness == Line.REGULAR_LINE):
                continue

            # Horizontal or vertical walls only
            if line.horizontal:
                point = (location[0], line.start[1])
            elif line.vertical:
                point = (line.start[0], location[1])
            else:
                continue

            # Find closest point
            distance = Line.distance(point, location)

            if distance < closest_point_distance:
                closest_line = line
                closest_point = point
                closest_point_distance = distance

        # No walls found near the location
        if closest_line == None or closest_point == None\
            or closest_point_distance > Window.MAX_DISTANCE:
            return None

        return (closest_line, closest_point)

    def get_entity_on_location(self, location = (0, 0)):
        """Returns single entity that collides with the location
        :param location: Position coordinates to check collision against
        :type location: tuple(int, int)
        """

        for door in self.doors:
            door.selected = False
            if door.check_collision(
                sdl2.SDL_Rect(int(location[0]), int(location[1]), 0, 0)):
                door.selected = True
                return door

        for window in self.windows:
            window.selected = False
            if window.check_collision(
                sdl2.SDL_Rect(int(location[0]), int(location[1]), 0, 0)):
                window.selected = True
                return window

        for line in self.lines:
            line.selected = False
            if line.check_point_collision(location):
                line.selected = True
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

        for door in self.doors:
            door.selected = False
            if door.check_collision(rectangle):
                entities.add(door)
                door.selected = True

        for window in self.windows:
            window.selected = False
            if window.check_collision(rectangle):
                entities.add(window)
                window.selected = True

        for line in self.lines:
            line.selected = False
            if line.check_rectangle_collision(rectangle):
                entities.add(line)
                line.selected = True

        for text in self.user_text:
            text.selected = False
            if text.check_collision(rectangle):
                entities.add(text)
                text.selected = True

        self.update_needed = True
        return entities

    def get_inventory(self):
        """Returns a string of entities grouped by type and lengths.
        For instance:
        - 4 x 8' exterior wall
        - 2 x 8' interior wall
        """
        inventory = ''

        exterior_walls = {}
        interior_walls = {}

        # Tally up quantities for each wall length
        for line in self.lines:
            if line.thickness == Line.EXTERIOR_WALL:
                if line.length in exterior_walls:
                    exterior_walls[line.length] += 1
                else:
                    exterior_walls[line.length] = 1
            elif line.thickness == Line.INTERIOR_WALL:
                if line.length in interior_walls:
                    interior_walls[line.length] += 1
                else:
                    interior_walls[line.length] = 1

        # Add to inventory string
        for wall in exterior_walls:
            inventory += 'Exterior wall: '\
                + str(exterior_walls[wall]) + ' x '\
                + Tools.convert_to_unit_system(wall) + '\n'

        for wall in interior_walls:
            inventory += 'Interior wall: '\
                + str(interior_walls[wall]) + ' x '\
                + Tools.convert_to_unit_system(wall) + '\n'

        return inventory

    def close_gaps_between_walls(self, line):
        """Adds a square vertex to close gaps between two connecting
        walls for rendering.
        """

        for other in self.lines:
            # Exterior and interior walls only
            if line.thickness == Line.REGULAR_LINE:
                continue

            # Do not compare against the same line
            if line is other:
                continue

            if line.start == other.start or line.start == other.end:
                vertex = RectangularEntity(sdl2.SDL_Rect(
                    int(line.start[0] - line.thickness / 2),
                    int(line.start[1] - line.thickness / 2),
                    line.thickness, line.thickness))
                vertex.layer = line.layer
                self.square_vertices.add(vertex)

            if line.end == other.end or line.end == other.start:
                vertex = RectangularEntity(sdl2.SDL_Rect(
                    int(line.end[0] - line.thickness / 2),
                    int(line.end[1] - line.thickness / 2),
                    line.thickness, line.thickness))
                vertex.layer = line.layer
                self.square_vertices.add(vertex)

    def init_mutexes(self):
        """Initializes the model mutexes for synchronization
        of accessing the entity containers.
        """
        self.mutexes = {}
        self.mutexes[ModelMutex.LINES] = Lock()
        self.mutexes[ModelMutex.VERTICES] = Lock()
        self.mutexes[ModelMutex.WINDOWS] = Lock()
        self.mutexes[ModelMutex.DOORS] = Lock()
        self.mutexes[ModelMutex.TEXT] = Lock()
        self.mutexes[ModelMutex.SQUARE_VERTICES] = Lock()

class ExteriorWallFactory:
    """Factory for exterior wall."""
    def create(self, start = (0, 0), end = (0, 0), color = (0, 0, 0)):
        """Creates and returns an exterior wall line.
        :param start: The starting vertex of the line
        :param end: The ending vertex of the line
        :type start, end: tuple(int, int)
        :param color: The r, g, b values for the line's rendering color
        :type color: tuple(int, int, int)"""
        return Line(start, end, Line.EXTERIOR_WALL, color)

class InteriorWallFactory:
    """Factory for interior wall."""
    def create(self, start = (0, 0), end = (0, 0), color = (0, 0, 0)):
        """Creates and returns an interior wall line.
        :param start: The starting vertex of the line
        :param end: The ending vertex of the line
        :type start, end: tuple(int, int)
        :param color: The r, g, b values for the line's rendering color
        :type color: tuple(int, int, int)"""
        return Line(start, end, Line.INTERIOR_WALL, color)

class RegularLineFactory:
    """Factory for regular line."""
    def create(self, start = (0, 0), end = (0, 0), color = (0, 0, 0)):
        """Creates and returns an regular line.
        :param start: The starting vertex of the line
        :param end: The ending vertex of the line
        :type start, end: tuple(int, int)
        :param color: The r, g, b values for the line's rendering color
        :type color: tuple(int, int, int)"""
        return Line(start, end, Line.REGULAR_LINE, color)

class AbstractLineFactory:
    """Abstract factory for creating lines."""

    def __init__(self):
        """Initializes the line factories."""
        self.factories = {}
        self.factories[EntityType.EXTERIOR_WALL] = ExteriorWallFactory()
        self.factories[EntityType.INTERIOR_WALL] = InteriorWallFactory()
        self.factories[EntityType.REGULAR_LINE] = RegularLineFactory()

    def create(self, type, start = (0, 0), end = (0, 0), color = (0, 0, 0)):
        """Creates and returns the line of type.
        :param type: The type of line to create.
        :type type: EntityType
        :param start: The starting vertex of the line
        :param end: The ending vertex of the line
        :type start, end: tuple(int, int)
        :param color: The r, g, b values for the line's rendering color
        :type color: tuple(int, int, int)"""

        if type in self.factories:
            return self.factories[type].create(start, end, color)
        return None