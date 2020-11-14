import math
import sdl2
import sdl2.ext

from ctypes import c_int, pointer
from entity_types import EntityType
from view import FontSize
from entities import Line
from tools import Tools

class Controller:
    """The class responsible for handling user input on the model."""

    def __init__(self):
        """Initializes the user camera, UI text displayers, and UI panels."""
        self.reset()

        # User camera
        self.camera = Camera()

        # User interface text displayers
        self.text_displayers = []
        self.middle_text = CenterText()
        self.text_displayers.append(self.middle_text)

        # User interface panels
        self.panels = []
        self.panels.append(CenterButtonPanel())

        # Interval to snap the mouse (px)
        self.snap_interval = 6

        self.current_layer = 0

    def handle_input(self, model):
        """Handles user mouse and keyboard input and operates on the model.
        :param model: The app model
        :type model: Model from 'model.py'
        """

        # Retrive keys currently being pressed
        keystate = sdl2.SDL_GetKeyboardState(None)

        for event in sdl2.ext.get_events():
            # User exited the app window
            if event.type == sdl2.SDL_QUIT:
                return False

            try:
                # Retrive mouse location
                self.get_mouse_location()
                
                # Handle text input
                self.reset_text()
                self.handle_text_input(event)

                # Update text diplayers
                self.update_bottom_right_text()
                self.update_bottom_middle_text(model)

                # Zoom camera in/out
                if event.type == sdl2.SDL_MOUSEWHEEL:
                    self.handle_camera_zoom(event)

                # Resize the screen
                if event.type == sdl2.SDL_WINDOWEVENT:
                    model.update_needed = True

                # Select a single entity
                if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    self.handle_single_entity_selection(model)
                
                # Select multiple entities
                self.handle_mouse_drag(event)
                if self.mouse_selection.w != 0 and self.mouse_selection.h != 0:
                    self.handle_multiple_entity_selection(model)

                # Panning camera
                if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                    or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                    self.handle_camera_pan(event)

                # Reset the camera position and scale
                if keystate[sdl2.SDL_SCANCODE_Z]:
                    self.camera.x = 0
                    self.camera.y = 0
                    self.camera.scale = 1.0

                # Place entity
                if not self.place_two_points:
                    if keystate[sdl2.SDL_SCANCODE_KP_0]: # exterior wall
                        self.reset()
                        self.line_type = EntityType.EXTERIOR_WALL
                        self.line_thickness = Line.EXTERIOR_WALL
                        self.place_two_points = True
                    elif keystate[sdl2.SDL_SCANCODE_KP_1]: # interior wall
                        self.reset()
                        self.line_type = EntityType.INTERIOR_WALL
                        self.line_thickness = Line.INTERIOR_WALL
                        self.place_two_points = True
                    elif keystate[sdl2.SDL_SCANCODE_M]: # measurement
                        self.reset()
                        self.line_type = EntityType.NONE
                        self.line_thickness = 1
                        self.place_two_points = True

                # Place line based entity
                if self.place_two_points:
                    self.handle_two_point_placement(event, keystate, model)

                # Cancel any polling
                if keystate[sdl2.SDL_SCANCODE_ESCAPE]:
                    self.reset()

                # Delete selected entities
                if keystate[sdl2.SDL_SCANCODE_DELETE]:
                    for entity in self.selected_entities:
                        model.remove_entity(entity)
                    self.selected_entities.clear()

            # If any errors occur, reset the UI state
            except:
                self.reset()

        # Scroll camera using keyboard input
        self.camera.scroll(keystate)

        return True

    def get_mouse_location(self):
        """Retrieves user's current mouse location on the screen from SDL.
        """
        mouse_x_ptr = pointer(c_int(0))
        mouse_y_ptr = pointer(c_int(0))
        sdl2.SDL_GetMouseState(mouse_x_ptr, mouse_y_ptr)

        self.mouse_x = mouse_x_ptr.contents.value
        self.mouse_y = mouse_y_ptr.contents.value

    def handle_text_input(self, event):
        """Updates the text the user is currently typing. Text can only
        consist of numbers. Otherwise, it resets.
        """
        if event.type == sdl2.SDL_TEXTINPUT:
            if not str(event.text.text)[2:3].isdigit():
                self.text = ''
            else:
                self.text += str(event.text.text)[2:3]

    def update_bottom_right_text(self):
        """Updates text displayed on the bottom right of the screen to
        note the mouse's current x and y positions and the camera scale
        """
        adjusted_mouse_x = (self.mouse_x + self.camera.x) / self.camera.scale
        adjusted_mouse_y = (self.mouse_y + self.camera.y) / self.camera.scale

        self.middle_text.set_right_text('X: {} Y: {} Zoom: {}'.format(
            int(adjusted_mouse_x), int(adjusted_mouse_y),
            round(self.camera.scale, 10)))

    def update_bottom_middle_text(self, model):
        """Updates text displayed on the bottom middle of the screen to
        the entity type of the entity the user has their mouse hovered over
        """
        entity = model.get_entity_on_location(self.get_adjusted_mouse(model))

        if entity == None:
            self.middle_text.set_bottom_text()
        else:
            self.middle_text.set_bottom_text(str(entity))

    def handle_single_entity_selection(self, model):
        """Selects a single entity that the user clicked on.
        :param model: The app model
        :type model: Model from 'model.py'
        """
        mouse_x_on_camera = self.mouse_x + self.camera.x
        mouse_y_on_camera = self.mouse_y + self.camera.y

        # Call this function to reset selected field for all entities
        model.get_entities_in_rectangle()

        self.selected_entities.clear()
        self.selected_entities.add(model.get_entity_on_location(
            (mouse_x_on_camera, mouse_y_on_camera)))

    def handle_multiple_entity_selection(self, model):
        """Selects entities that collide with the user's mouse selection
        (press and drag input).
        :param model: The app model
        :type model: Model from 'model.py'
        """
        self.selected_entities.clear()
        result_set = model.get_entities_in_rectangle(self.mouse_selection)
        for entity in result_set:
            self.selected_entities.add(entity)

    def handle_camera_pan(self, event):
        """Handles user input for panning the camera. User can pan the camera
        by holding the SHIFT key and pressing and moving the mouse.
        """
        if not self.panning_camera and event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            self.panning_camera = True
            self.pan_start_x = self.mouse_x
            self.pan_start_y = self.mouse_y
        elif self.panning_camera and event.type == sdl2.SDL_MOUSEBUTTONUP:
            self.panning_camera = False

        if not self.panning_camera:
            return

        # Adjust camera to difference in pan locations
        x_difference = self.pan_start_x - self.mouse_x
        y_difference = self.pan_start_y - self.mouse_y

        self.pan_start_x = self.mouse_x
        self.pan_start_y = self.mouse_y

        self.camera.x += x_difference
        self.camera.y += y_difference

    def handle_camera_zoom(self, event):
        """Handles user input for scrolling the mouse wheel to adjust the
        camera's scale (zooming in and out).
        :param event: SDL event for checking mouse clicks
        :type event: SDL_Event
        """
        if event.wheel.y > 0: # zooming in
            self.camera.scale += 0.05
            self.camera.x += 1920 * 0.025
            self.camera.y += 1080 * 0.025

        elif event.wheel.y < 0: # zooming out
            self.camera.scale -= 0.05
            self.camera.x -= 1920 * 0.025
            self.camera.y -= 1080 * 0.025

        # Keep camera scroll above 0
        if self.camera.scale <= 0.0:
            self.camera.scale = 0.05

    def handle_mouse_drag(self, event):
        """Handles user input for pressing and dragging the mouse.
        :param event: SDL event for checking mouse clicks
        :type event: SDL_Event
        """
        if not self.mouse_down and event.type == sdl2.SDL_MOUSEBUTTONDOWN\
            and event.button.button == sdl2.SDL_BUTTON_LEFT:
            self.mouse_down = True
            self.mouse_down_starting_x = self.mouse_x + int(self.camera.x)
            self.mouse_down_starting_y = self.mouse_y + int(self.camera.y)
        if self.mouse_down and event.type == sdl2.SDL_MOUSEBUTTONUP:
            self.mouse_down = False
            self.mouse_selection = sdl2.SDL_Rect()
        if self.mouse_down and event.type == sdl2.SDL_MOUSEMOTION:
            mouse_down_ending_x = self.mouse_x + int(self.camera.x)
            mouse_down_ending_y = self.mouse_y + int(self.camera.y)

            if self.mouse_down_starting_x < mouse_down_ending_x:
                self.mouse_selection.x = self.mouse_down_starting_x
            else:
                self.mouse_selection.x = mouse_down_ending_x

            if self.mouse_down_starting_y < mouse_down_ending_y:
                self.mouse_selection.y = self.mouse_down_starting_y
            else:
                self.mouse_selection.y = mouse_down_ending_y

            self.mouse_selection.w = abs(
                self.mouse_down_starting_x - mouse_down_ending_x)
            self.mouse_selection.h = abs(
                self.mouse_down_starting_y - mouse_down_ending_y)

    def handle_two_point_placement(self, event, keystate, model):
        """Handles user input for placing two points for a line and adds the
        line to the model. Displays the line length while the user is selecting
        the second point. If the user holds shift while placing the second
        point, the line will snap to the nearest x or y-axis.
        :param event: SDL event for checking mouse clicks
        :type event: SDL_Event
        :param keystate: SDL keystate for checking if using is pressing SHIFT
        :type keystate: int[]
        :param model: The app model
        :type model: Model from 'model.py'
        """

        adjusted_mouse = self.get_adjusted_mouse(model)
        adjusted_mouse_x = adjusted_mouse[0]
        adjusted_mouse_y = adjusted_mouse[1]

        # User placed the first point
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN\
            and not self.first_point_placed:
            self.first_point_x = adjusted_mouse_x
            self.first_point_y = adjusted_mouse_y
            self.first_point_placed = True
            return

        self.horizontal_line = False
        self.vertical_line = False
        
        # User is holding shift, so snap line to either the x or y axis,
        # depending on its angle
        if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
            or keystate[sdl2.SDL_SCANCODE_RSHIFT]:

            if self.first_point_x - adjusted_mouse_x != 0:
                angle = math.atan(
                    (self.first_point_y - adjusted_mouse_y)
                    / (self.first_point_x - adjusted_mouse_x)) * 180.0 / math.pi

                if abs(angle) < 45:
                    self.horizontal_line = True
                else:
                    self.vertical_line = True

        # Display the length of the line the user is currently projecting
        if self.first_point_placed:
            if self.text and int(self.text) != 0:
                length = int(self.text)
            elif self.horizontal_line:
                length = abs(self.first_point_x - adjusted_mouse_x)
            elif self.vertical_line:
                length = abs(self.first_point_y - adjusted_mouse_y)
            else:
                length = math.sqrt(
                    (self.first_point_x - adjusted_mouse_x) ** 2
                    +  (self.first_point_y - adjusted_mouse_y) ** 2)
            self.middle_text.set_bottom_text(
                "Length: " + Tools.convert_to_unit_system(length))

        # Display hint text
        self.middle_text.set_top_text(
            'Select starting and ending point. '
            + 'Press ESC to cancel placement. Hold SHIFT to align line to axis')

        # User placed the second point
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if self.horizontal_line:
                model.add_line(
                    self.line_type,
                    (self.first_point_x, self.first_point_y),
                    (adjusted_mouse_x, self.first_point_y))
            elif self.vertical_line:
                model.add_line(
                    self.line_type,
                    (self.first_point_x, self.first_point_y),
                    (self.first_point_x, adjusted_mouse_y))
            else:
                model.add_line(
                    self.line_type,
                    (self.first_point_x, self.first_point_y),
                    (adjusted_mouse_x, adjusted_mouse_y))

            self.reset()

    def get_adjusted_mouse(self, model):
        """Returns the mouse's current position, adjusted to the snap interval
        or any nearby vertex or axis to snap to
        :param model: The app model
        :param type: Model from 'model.py'
        :return type: tuple(int, int)
        """

        # Snap to nearest vertex if nearby
        self.nearest_vertex = model.get_vertex_within_range((
            self.mouse_x - int(self.camera.x),
            self.mouse_y - int(self.camera.y)))

        if self.nearest_vertex:
            return (self.nearest_vertex[0], self.nearest_vertex[1])

        # Snap to same axis as nearest vertex if possible
        if self.place_two_points:
            self.nearest_vertex_axis = model.get_vertex_on_axis((
                self.mouse_x - int(self.camera.x),
                self.mouse_y - int(self.camera.y)), self.horizontal_line)
            if self.nearest_vertex_axis and self.horizontal_line:
                return (self.snap_interval
                        * round(self.nearest_vertex_axis[0]\
                        / self.snap_interval), self.snap_interval
                        * round((self.mouse_y + self.camera.y)
                        / self.snap_interval))
            elif self.nearest_vertex_axis:
                return (self.snap_interval
                        * round((self.mouse_x + self.camera.x)\
                        / self.snap_interval), self.snap_interval
                        * round(self.nearest_vertex_axis[1]
                        / self.snap_interval))

        return (self.snap_interval * round((self.mouse_x + self.camera.x)\
            / self.snap_interval / self.camera.scale), self.snap_interval
            * round((self.mouse_y + self.camera.y) / self.snap_interval
            / self.camera.scale))

    def get_mouse_selection(self):
        """Returns the user's current mouse selection (press and drag input)
        """
        return sdl2.SDL_Rect(
            self.mouse_selection.x - int(self.camera.x),
            self.mouse_selection.y - int(self.camera.y),
            self.mouse_selection.w,
            self.mouse_selection.h)

    def get_two_point_placement(self, model):
        """Returns the first point the user placed and the projected second
        point, to be displayed as the user selects the second point.
        :param model: The app model
        :param type: Model from 'model.py'
        :return type: tuple(tuple(int, int), tuple(int, int))
        """
        if not (self.place_two_points and self.first_point_placed):
            return ((0, 0), (0, 0), 0)

        if self.text and int(self.text) != 0:
            return ((self.first_point_x, self.first_point_y),
                (self.second_point_x, self.second_point_y), self.line_thickness)

        adjusted_mouse = self.get_adjusted_mouse(model)
        adjusted_mouse_x = adjusted_mouse[0]
        adjusted_mouse_y = adjusted_mouse[1]

        if self.horizontal_line:
            self.second_point_x = adjusted_mouse_x
            self.second_point_y = self.first_point_y
        elif self.vertical_line:
            self.second_point_x = self.first_point_x
            self.second_point_y = adjusted_mouse_y
        else:
            self.second_point_x = adjusted_mouse_x
            self.second_point_y = adjusted_mouse_y

        return ((self.first_point_x, self.first_point_y),
                (self.second_point_x, self.second_point_y), self.line_thickness)

    def get_nearest_vertex(self):
        """Returns nearest vertex to snap to, if it exists.
        """
        if self.place_two_points:
            return self.nearest_vertex
        return None

    def get_nearest_axis(self):
        """Returns nearest axis to snap to, if it exists.
        """
        if self.place_two_points:
            return self.nearest_vertex_axis
        return None

    def reset(self):
        """Resets the controller's state.
        """
        self.panning_camera = False
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.mouse_x = 0
        self.mouse_y = 0

        self.mouse_down = False
        self.mouse_selection = sdl2.SDL_Rect()

        self.place_two_points = False
        self.first_point_placed = False
        self.first_point_x = 0
        self.first_point_y = 0
        self.second_point_x = 0
        self.second_point_y = 0
        self.horizontal_line = False
        self.vertical_line = False
        self.line_thickness = 0
        self.nearest_vertex = None
        self.nearest_vertex_axis = None
        self.line_type = None

        self.text = ''

        self.selected_entities = set()

    def reset_text(self):
        """Resets the text being displayed on the user interface.
        """
        self.middle_text.set_top_text('')
        self.middle_text.set_bottom_text('')

class Camera:
    # Regular camera scrolling speed (in/s)
    REGULAR_SCROLL_SPEED = 500

    # Fast camera scrolling (in/s)
    FAST_SCROLL_SPEED = 2000

    def __init__(self):
        """Initializes the camera class."""
        self.x = 0.0
        self.y = 0.0
        self.scale = 1.0

        self.last_scrolled = 0

    def scroll(self, keystate):
        """Scrolls the camera up, down, left, or right at normal or fast speed
        depending on the user's keyboard input.
        :param keystate: SDL keystate for checking if using is pressing SHIFT
        :type keystate: int[]
        """
        time_elapsed = (sdl2.SDL_GetTicks() - self.last_scrolled) / 1000.0
        self.last_scrolled = sdl2.SDL_GetTicks()

        if keystate[sdl2.SDL_SCANCODE_W] or keystate[sdl2.SDL_SCANCODE_UP]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.y -= Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.y -= Camera.REGULAR_SCROLL_SPEED * time_elapsed

        if keystate[sdl2.SDL_SCANCODE_S] or keystate[sdl2.SDL_SCANCODE_DOWN]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.y += Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.y += Camera.REGULAR_SCROLL_SPEED * time_elapsed

        if keystate[sdl2.SDL_SCANCODE_A] or keystate[sdl2.SDL_SCANCODE_LEFT]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.x -= Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.x -= Camera.REGULAR_SCROLL_SPEED * time_elapsed

        if keystate[sdl2.SDL_SCANCODE_D] or keystate[sdl2.SDL_SCANCODE_RIGHT]:
            if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                self.x += Camera.FAST_SCROLL_SPEED * time_elapsed
            else:
                self.x += Camera.REGULAR_SCROLL_SPEED * time_elapsed


class Text:
    """Wrapper class around text to be displayed. Contains the relative
    position and size to the application screen size (%), the font,
    and the text color."""

    def __init__(self, relative_x = 0, relative_y = 0,
                 font = FontSize.SMALL, color = (0, 0, 0)):
        """Initializes the text."""
        self.relative_x = relative_x
        self.relative_y = relative_y
        self.font = font
        self.color = sdl2.SDL_Color(color[0], color[1], color[2])
        self.text = ''

class TextDisplayer:
    """Base class for a user interface object that displays text."""

    def __init__(self):
        """Initializes the text displayer."""
        self.text = []

class CenterText(TextDisplayer):
    """Text displayer responsible for displaying text on the top center,
    bottom center, and bottom right of the application window.
    """

    # Indices in text list for each text
    TOP_CENTER_TEXT = 0
    BOTTOM_CENTER_TEXT = 1
    BOTTOM_RIGHT_TEXT = 2

    # Relative positions
    TOP_CENTER_RELATIVE_Y = 0.06
    BOTTOM_CENTER_RELATIVE_Y = 0.99

    # Relative positions
    BOTTOM_RIGHT_RELATIVE_X = 0.99
    BOTTOM_RIGHT_RELATIVE_Y = 0.99

    def __init__(self):
        """Initializes the center text displayers."""
        TextDisplayer.__init__(self)
        self.text.append(Text(0.50, CenterText.TOP_CENTER_RELATIVE_Y,
                         FontSize.SMALL))
        self.text.append(Text(0.50, CenterText.BOTTOM_CENTER_RELATIVE_Y,
                         FontSize.MEDIUM))
        self.text.append(Text(CenterText.BOTTOM_RIGHT_RELATIVE_X,
                         CenterText.BOTTOM_RIGHT_RELATIVE_Y, FontSize.MEDIUM))

    def set_top_text(self, top_text = ''):
        """Sets the text displayed at the top center of the screen.
        :param top_text: The text to display
        :type top_text: str
        """
        self.text[CenterText.TOP_CENTER_TEXT].text = top_text

    def set_bottom_text(self, bottom_text = ''):
        """Sets the text displayed at the bottom center of the screen.
        :param bottom_text: The text to display
        :type bottom_text: str
        """
        self.text[CenterText.BOTTOM_CENTER_TEXT].text = bottom_text

    def set_right_text(self, right_text = ''):
        """Sets the text displayed at the bottom right of the screen.
        :param right_text: The text to display
        :type right_text: str
        """
        self.text[CenterText.BOTTOM_RIGHT_TEXT].text = right_text

class Button:
    """Button that the user can click in the application window."""

    def __init__(self, texture, relative_x = 0, relative_y = 0,
                 relative_width = 0, relative_height = 0):
        """Initializes the button."""
        self.texture = texture
        self.location = (relative_x, relative_y,
                         relative_width, relative_height)

class Panel:
    """Base class for a user interface button panel."""

    def __init__(self, texture, relative_x = 0, relative_y = 0,
                 relative_width = 0, relative_height = 0):
        "Initializes the panel."
        self.texture = texture
        self.relative_x = relative_x
        self.relative_y = relative_y
        self.relative_width = relative_width
        self.relative_height = relative_height

        self.buttons = set()

    def mouse_over(self, mouse_x, mouse_y):
        """Returns true if mouse positions collide with any of the buttons
        in the panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        for button in self.buttons:
            if mouse_over(mouse_x, mouse_y, button.location):
                return True
        return False

    def mouse_over_on_button(mouse_x, mouse_y, location):
        """Returns true if the mouse positions collide with the button
         at the location.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        :param location: Location to check mouse collision against
        :type location: SDL_Rect
        """
        if mouse_x > location.x + location.w: return False
        if mouse_x < location.x: return False
        if mouse_y > location.y + location.h: return False
        if mouse_y < location.y: return False
        return True

    def handle_mouse_click(self, mouse_x, mouse_y):
        """Abstract method for the logic that occurs if the user presses the
        mouse on this panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        pass

    def handle_mouse_hover(self, mouse_x, mouse_y):
        """Abstract method for the logic that occurs if the user hovers their
        mouse on this panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        pass

class CenterButtonPanel(Panel):
    """The main user interface panel appearing at the top center of the screen
    which contains the following buttons.
    """

    SELECT = 0
    DELETE = 1
    DRAW = 2
    MOVE = 3
    MEASURE = 4
    ADD_TEXT = 5
    PAN = 6
    ZOOM = 7
    LAYERS = 8
    SETTINGS = 9
    UNDO = 10
    REDO = 11
    SAVE = 12

    RELATIVE_X = 0.0
    RELATIVE_Y = 0.0
    RELATIVE_WIDTH = 1.0
    RELATIVE_HEIGHT = 0.05

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL,
                        CenterButtonPanel.RELATIVE_X,
                        CenterButtonPanel.RELATIVE_Y,
                        CenterButtonPanel.RELATIVE_WIDTH,
                        CenterButtonPanel.RELATIVE_HEIGHT)

        self.buttons.add(Button(EntityType.SELECT_BUTTON))
        self.buttons.add(Button(EntityType.DELETE_BUTTON))
        self.buttons.add(Button(EntityType.DRAW_BUTTON))
        self.buttons.add(Button(EntityType.MOVE_BUTTON))
        self.buttons.add(Button(EntityType.MEASURE_BUTTON))
        self.buttons.add(Button(EntityType.ADD_TEXT_BUTTON))
        self.buttons.add(Button(EntityType.PAN_BUTTON))
        self.buttons.add(Button(EntityType.ZOOM_BUTTON))
        self.buttons.add(Button(EntityType.LAYERS_BUTTON))
        self.buttons.add(Button(EntityType.SETTINGS_BUTTON))
        self.buttons.add(Button(EntityType.UNDO_BUTTON))
        self.buttons.add(Button(EntityType.REDO_BUTTON))
        self.buttons.add(Button(EntityType.SAVE_BUTTON))
