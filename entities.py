import math
import sdl2

from tools import Tools

class Line:
    """The class representing a line segment created by the user.
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
        """ Initalizes the line class.
        :param start: line segment starting vertex
        :param end: line segment ending vertex
        :type start, end: tuple(int, int)
        :param thickness: line thickness (in)
        :type thickness: int
        :param color: line display color in r, g, b values
        :type color: tuple(int, int, int)
        """
        self.start = start
        self.end = end
        self.thickness = thickness
        self.color = color
        self.length = int(Line.distance(start, end))

        # Whether the line is currently selected by the user
        self.selected = False

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
        :type rectange: SDL_Rect
        """

        # Rectangle vertices
        top_left = (rectangle.x, rectangle.y)
        top_right = (rectangle.x + rectangle.w, rectangle.y)
        bottom_left = (rectangle.x, rectangle.y + rectangle.h)
        bottom_right = (rectangle.x + rectangle.w, rectangle.y + rectangle.h)

        # Check for interesection between rectangle edges
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

    def get_color(self):
        """Returns line's color if it is not selected. Otherwise, returns
        color denoting selection.
        """
        if not self.selected:
            return self.color
        else:
            return (34, 139, 34) # green

    def __str__(self):
        """Returns line type string based on the thickness and the length.
        """
        if self.thickness == Line.EXTERIOR_WALL:
            type = 'Exterior Wall'
        elif self.thickness == Line.INTERIOR_WALL:
            type = 'Interior Wall'
        else:
            type = 'Line'
        return type + ' (' + Tools.convert_to_unit_system(self.length) + ')'

    def __repr__(self):
        """Returns the starting and ending verticies.
        """
        return str(self.start) + ' - ' + str(self.end)

    def __deepcopy__(self, memodict = {}):
        """Copy constructor for line.
        """
        return Line(self.start, self.end, self.thickness, self.color)

class Rectangle:
    def __init__(self, rectangle = (0, 0, 0, 0)):
        pass

class UserText:
    def __init__(self, text = '', position = (0, 0)):
        self.text = text
        self.position = position
