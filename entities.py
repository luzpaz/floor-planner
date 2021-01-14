import math, sdl2

from tools import Tools

class Entity:
    """The base class for objects displayed onto the screen.
    The user can select these objects and assign them to layers.
    Child classes define how the object's position is determined."""

    def __init__(self, layer = 0):
        # Whether the entity is selected by the user
        self.selected = False

        # Layer the object is assigned to
        self.layer = layer

class Line(Entity):
    """Represents a line segment created by the user.
    Contains the starting and ending coordinates, and the thickness and color.
    """

    # Exterior wall thickness (inch)
    EXTERIOR_WALL = 6

    # Interior wall thickness (inch)
    INTERIOR_WALL = 4

    # Regular line thickness (inch)
    REGULAR_LINE = 1

    def __init__(self, start = (0, 0), end = (0, 0),
                 thickness = 1, color = (0, 0, 0)):
        """ Initializes the line.
        :param start: line segment starting vertex
        :param end: line segment ending vertex
        :type start, end: tuple(int, int)
        :param thickness: line thickness (in)
        :type thickness: int
        :param color: line display color in r, g, b values
        :type color: tuple(int, int, int)
        """
        Entity.__init__(self)

        self.start = start
        self.end = end
        self.thickness = thickness
        self.color = color
        self.length = int(Line.distance(start, end))

        # Whether the line is a horizontal line
        self.horizontal = start[1] == end[1]

        # Whether the line is a vertical line
        self.vertical = start[0] == end[0]

        # Whether the line is positive on the x/y axes
        self.positive_x = end[0] > start[0]
        self.positive_y = end[1] > start[1]

    def check_point_collision(self, location = (0, 0)):
        """Returns whether the location coordinates collide with this line.
        :param location: the location coordinates to check collision against
        :type location: tuple(int, int)
        """
        return int(Line.distance(self.start, location))\
               + int(Line.distance(self.end, location))\
               == int(Line.distance(self.start, self.end))

    def check_rectangle_collision(self, rectangle = sdl2.SDL_Rect()):
        """Returns whether the rectangle collides with this line.
        :param rectangle: the rectangle containing the top-left x and y position
        and the width and height
        :type rectangle: SDL_Rect
        """

        # Rectangle vertices
        top_left = (rectangle.x, rectangle.y)
        top_right = (rectangle.x + rectangle.w, rectangle.y)
        bottom_left = (rectangle.x, rectangle.y + rectangle.h)
        bottom_right = (rectangle.x + rectangle.w, rectangle.y + rectangle.h)

        # Check for intersection between rectangle edges
        left = Line.intersect(top_left, bottom_left, self.start, self.end)
        right = Line.intersect(top_right, bottom_right, self.start, self.end)
        top = Line.intersect(top_left, top_right, self.start, self.end)
        bottom = Line.intersect(bottom_left, bottom_right, self.start, self.end)

        # Return whether line collides with any of the rectangle edges
        return left or right or top or bottom

    def distance(start, end):
        """Returns the distance between two vertices.
        :param start: starting vertex
        :param end: ending vertex
        :type start end: tuple(int, int)
        """
        return math.sqrt((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2)

    def ccw(first, second, third):
        """Returns whether the vertices are listed in a counterclockwide order,
        used for determining whether two lines interset.
        :param first, second, third: the three vertices to check, respectively
        :type first, second, third: tuple(int, int)
        """
        return (third[1] - first[1]) * (second[0] - first[0])\
               > (second[1] - first[1]) * (third[0] - first[0])

    def intersect(first_start, first_end, second_start, second_end):
        """Returns whether the two line segments intersect (not overlap).
        :param first_start: first line starting vertex
        :param first_end: first line ending vertex
        :param second_start: second line starting vertex
        :param second_end: second line ending vertex
        :type first_start, first_end, second_start, second_end: tuple(int, int)
        """
        return Line.ccw(first_start, second_start, second_end)\
               != Line.ccw(first_end, second_start, second_end)\
               and Line.ccw(first_start, first_end, second_start)\
               != Line.ccw(first_start, second_start, second_end)

    def intersection(first_start, first_end, second_start, second_end):
        """Returns the intersection point between two line segments.
        :param first_start: first line starting vertex
        :param first_end: first line ending vertex
        :param second_start: second line starting vertex
        :param second_end: second line ending vertex
        :type first_start, first_end, second_start, second_end: tuple(int, int)
        """
        a1 = first_end[1] - first_start[1]
        b1 = first_start[0] - first_end[0]
        c1 = a1 * first_start[0] + b1 * first_start[1]

        a2 = second_end[1] - second_start[1]
        b2 = second_start[0] - second_end[0]
        c2 = a2 * second_start[0] + b2 * second_start[1]

        determinant = a1 * b2 - a2 * b1

        if determinant == 0:
            return None

        return ((b2 * c1 - b1 * c2) / determinant,\
            (a1 * c2 - a2 * c1) / determinant)
    
    def add_to_model(self, model):
        """Adds the line to the model."""
        model.lines.add(self)
        model.update_vertices()

    def remove_from_model(self, model):
        """Removes the line from the model."""
        model.lines.remove(self)
        model.update_vertices()

    def adjust(self, model, move_location = (0, 0)):
        """Additional adjustment after a move: none needed."""
        pass

    def move(self, x, y, start_vertex = True):
        """Moves the line to the new location with respect to either the
        start or end vertex.
        :param x, y: new x and y positions to move to
        :type x, y: int
        :param start_vertex: Whether to use the start vertex (or the end vertex)
        :type start_vertex: boolean
        """
        if start_vertex:
            x_distance = x - self.start[0]
            y_distance = y - self.start[1]

            self.start = (x, y)

            self.end = (self.end[0] + x_distance,
                        self.end[1] + y_distance)
        else:
            x_distance = x - self.end[0]
            y_distance = y - self.end[1]

            self.end = (x, y)

            self.start = (self.start[0] + x_distance,
                        self.start[1] + y_distance)

    def get_moving_vertex(self, start_vertex = True):
        """Returns the vertex being moved: either the starting or ending vertex.
        """
        if start_vertex:
            return self.start
        else:
            return self.end

    def get_color(self):
        """Returns line's color if it is not selected. Otherwise, returns
        color denoting selection.
        """
        if not self.selected:
            return self.color
        else:
            return (34, 139, 34) # green

    def get_type_str(self):
        """Returns the string for the type of the line.
        """
        if self.thickness == Line.EXTERIOR_WALL:
            return 'Exterior Wall'
        elif self.thickness == Line.INTERIOR_WALL:
            return 'Interior Wall'
        else:
            return 'Line'

    def __str__(self):
        """Returns line type string based on the thickness and the length.
        """
        type = self.get_type_str()
        return type + ' (' + Tools.convert_to_unit_system(self.length) + ')'

    def __repr__(self):
        """Returns info needed for debugging."""
        return 'Line'

    def __deepcopy__(self, memodict = {}):
        """Copy constructor for line.
        """
        return Line(self.start, self.end, self.thickness, self.color)

class RectangularEntity(Entity):
    """Base class for an entity that can be rendered as a rectangle.
    """

    def __init__(self, rectangle = sdl2.SDL_Rect(0, 0, 0, 0)):
        """Initializes the top left x and y coordinates and the width and height
        of the rectangle.
        """
        Entity.__init__(self)

        self.x = rectangle.x
        self.y = rectangle.y
        self.width = rectangle.w
        self.height = rectangle.h
        self.horizontal = self.width >= self.height

    def check_collision(self, other = sdl2.SDL_Rect(0, 0, 0, 0)):
        """Returns true if a rectangular collision occurs with this rectangle
        and the other.
        :param other: The other rectangle to check a collision against
        :type other: SDL_Rect
        """
        collision = True

        if self.y + self.height <= other.y:
            collision = False
        if self.y >= other.y + other.h:
            collision = False
        if self.x + self.width <= other.x:
            collision = False
        if self.x >= other.x + other.w:
            collision = False

        return collision

    def move(self, x, y, left_top_vertex = True):
        """Moves the rectangle to the new location with respect to either the
        left/top or right/bottom vertex.
        :param x, y: new x and y positions to move to
        :type x, y: int
        :param left_top_vertex: Whether to use the left/top vertex
        : or the right/bottom vertex
        :type left_top_vertex: boolean
        """
        if left_top_vertex:
            # Left/top vertex
            self.x = x
            self.y = y
        else:
            # Right/bottom vertex
            self.x = x - self.width
            self.y = y - self.height

    def get_moving_vertex(self, start_vertex = True):
        """Returns the vertex being moved: either the starting or ending vertex.
        """
        if start_vertex:
            if self.horizontal:
                return (self.x, int(self.y + self.height / 2))
            else:
                return (int(self.x + self.width / 2), self.y)
        else:
            if self.horizontal:
                return (int(self.x + self.width),
                        int(self.y + self.height / 2))
            else:
                return (int(self.x + self.width / 2),
                        int(self.y + self.height))

    def adjust(self, model, move_location = (0, 0)):
        """Additional adjustment after a move: defined by child classes."""
        pass

    def __deepcopy__(self, memodict = {}):
        """Copy constructor for rectangle.
        """
        return RectangularEntity(sdl2.SDL_Rect(
            self.x, self.y, self.width, self.height))

class Window(RectangularEntity):
    """Represents a window that can be placed on an exterior wall.
    """
    
    # Default length (px)
    LENGTH = 36

    # Default width (px)
    WIDTH = 6

    # Maximum distance an exterior wall can be from the user's mouse positions
    # for the window to snap onto it (px)
    MAX_DISTANCE = 100

    def __init__(self, rectangle = sdl2.SDL_Rect(0, 0, 0, 0)):
        """Initializes the window as a rectangular entity.
        """
        RectangularEntity.__init__(self, rectangle)
        
    def add_to_model(self, model):
        """Adds the window to the model."""
        model.windows.add(self)

    def remove_from_model(self, model):
        """Removes the window from the model."""
        model.windows.remove(self)

    def adjust(self, model, move_location = (0, 0)):
        """Snaps the entity to the nearest exterior wall that has
        the same orientation.
        """
        result = model.get_nearest_wall(move_location, True)

        # No exterior wall nearby, keep as is
        if not result:
            return
        center_vertex = result[1]

        # Attach window to the wall
        if self.horizontal:
            self.x = int(center_vertex[0] - Window.LENGTH / 2)
            self.y = int(center_vertex[1] - Window.WIDTH / 2)
        else:
            self.x = int(center_vertex[0] - Window.WIDTH / 2)
            self.y = int(center_vertex[1] - Window.LENGTH / 2)

    def __str__(self):
        """Returns window type string and its length.
        """
        return 'Window' + ' ('\
            + Tools.convert_to_unit_system(Window.LENGTH) + ')'

    def __repr__(self):
        """Returns info needed for debugging."""
        return 'Window'

class Door(RectangularEntity):
    """Represents a door that can be placed on a wall.
    """
    
    # Default length (px)
    LENGTH = 36

    def __init__(self, rectangle = sdl2.SDL_Rect(0, 0, 0, 0)):
        """Initializes the door as a rectangular entity.
        """
        RectangularEntity.__init__(self, rectangle)
        
    def add_to_model(self, model):
        """Adds the door to the model."""
        model.doors.add(self)

    def remove_from_model(self, model):
        """Removes the door from the model."""
        model.doors.remove(self)

    def adjust(self, model, move_location = (0, 0)):
        """Snaps the entity to the nearest wall that has the same orientation.
        """
        result = model.get_nearest_wall(move_location, False)

        # No wall nearby, keep as is
        if not result:
            return
        center_vertex = result[1]

        # Attach door to the wall
        if self.horizontal:
            self.x = int(center_vertex[0] - Door.LENGTH / 2)
            self.y = int(center_vertex[1] - self.height / 2)
        else:
            self.x = int(center_vertex[0] - self.width / 2)
            self.y = int(center_vertex[1] - Door.LENGTH / 2)

    def __str__(self):
        """Returns door type string and its length.
        """
        return 'Door' + ' ('\
            + Tools.convert_to_unit_system(Door.LENGTH) + ')'

    def __repr__(self):
        """Returns info needed for debugging."""
        return 'Door'

class UserText(RectangularEntity):
    """Represents text that the user can place on the drawing.
    """

    def __init__(self, text = '', position = (0, 0)):
        """Initializes the text and its location.
        """
        self.text = text
        self.position = position
        self.selected = False

        RectangularEntity.__init__(self, sdl2.SDL_Rect(
            self.position[0], self.position[1], len(self.text), len(self.text)))
        
    def add_to_model(self, model):
        """Adds the text to the model."""
        model.user_text.add(self)

    def remove_from_model(self, model):
        """Removes the text from the model."""
        model.user_text.remove(self)

    def adjust(self, model, move_location = (0, 0)):
        """Additional adjustment after a move: none needed."""
        pass
