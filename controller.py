import math, polling, sdl2, sdl2.ext

from ctypes import c_int, pointer
from entity_types import EntityType
from view import FontSize
from entities import Line
from tools import Tools, ExportCommand
from polling import PollingType

class Controller:
    """Handles user input on the model."""

    def __init__(self):
        """Initializes the user camera, UI text displayers, and UI panels."""

        # User camera
        self.camera = Camera()

        # User interface text displayers
        self.text_displayers = []
        self.center_text = CenterText()
        self.message_stack = MessageStack()
        self.fps_displayer = FPSDisplayer()
        self.text_displayers.append(self.center_text)
        self.text_displayers.append(self.message_stack)

        # FPS displayer only for debugging
        # self.text_displayers.append(self.fps_displayer)

        # User interface panels
        self.panels = []
        self.panels.append(CenterButtonPanel())
        self.panels.append(LeftButtonPanel())
        self.settings_panel = SettingsPanel()
        self.panels.append(self.settings_panel)

        self.layers_panel = RightButtonPanel()
        self.panels.append(self.layers_panel)

        # Polling event handlers
        self.handlers = [None] * PollingType.NUM_TYPES
        self.init_handlers()

        # Interval to snap the mouse (px)
        self.snap_interval = 6

        self.current_layer = 0

        # Whether a task is blocking the application
        self.loading = False

        # Whether to display the drawing grid
        self.display_grid = False

        # Whether to rasterize or vectorize graphics
        self.rasterize_graphics = True

        # Allow dragging and dropping files
        sdl2.SDL_EventState(sdl2.SDL_DROPFILE, sdl2.SDL_ENABLE)

        self.reset()

    def handle_input(self, model, screen_dimensions, commands = []):
        """Handles user mouse and keyboard input and operates on the model.
        :param model: The app model
        :type model: Model from 'model.py'
        :param screen_dimensions: The screen width and height.
        :type screen_dimensions: tuple(int, int)
        :param commands: List of commands to execute within the app loop,
        that require the view class.
        :type commands: list
        """

        # Retrieve keys currently being pressed
        keystate = sdl2.SDL_GetKeyboardState(None)

        for event in sdl2.ext.get_events():
            # User exited the app window or pressed ALT + F4
            if self.user_quit(event, keystate):
                return False

            try:
                # Retrieve mouse location
                self.get_mouse_location()
                
                # Handle text input
                self.reset_text()
                self.handle_text_input(event)

                # Update text diplayers
                self.update_bottom_right_text()
                self.update_bottom_center_text(model)

                # Zoom camera in/out
                if event.type == sdl2.SDL_MOUSEWHEEL:
                    self.handle_camera_zoom(event)

                # Resize the screen
                if event.type == sdl2.SDL_WINDOWEVENT:
                    model.update_needed = True

                # Find nearest vertex
                self.find_nearest_vertex(model)

                # Select a single entity
                if event.type == sdl2.SDL_MOUSEBUTTONDOWN\
                    and not self.using_selection:
                    self.handle_single_entity_selection(model)
                    self.last_selection = sdl2.SDL_GetTicks()
                    self.update_item_to_move()
                
                # Select multiple entities
                self.handle_mouse_drag(event)
                if self.mouse_selection.w != 0 and self.mouse_selection.h != 0\
                    and not self.using_selection:
                    self.handle_multiple_entity_selection(model)
                    self.last_selection = sdl2.SDL_GetTicks()
                    self.update_item_to_move()

                # Panning camera
                if keystate[sdl2.SDL_SCANCODE_LSHIFT]\
                    or keystate[sdl2.SDL_SCANCODE_RSHIFT]:
                    self.handle_camera_pan(event)

                # Place entity hotkeys
                if not self.place_two_points:
                    if keystate[sdl2.SDL_SCANCODE_KP_0]: # exterior wall
                        self.reset()
                        self.placement_type = EntityType.EXTERIOR_WALL
                        self.line_thickness = Line.EXTERIOR_WALL
                        self.place_two_points = True
                    elif keystate[sdl2.SDL_SCANCODE_KP_1]: # interior wall
                        self.reset()
                        self.placement_type = EntityType.INTERIOR_WALL
                        self.line_thickness = Line.INTERIOR_WALL
                        self.place_two_points = True

                # Place point based entity
                if self.place_one_point:
                    self.handle_one_point_placement(event, model)

                # Place line based entity
                if self.place_two_points:
                    self.handle_two_point_placement(event, keystate, model)

                self.handle_panel_input(event, screen_dimensions)
                     
                # User pressed the exit button
                if self.polling == PollingType.EXITING:
                    return False

                # Cancel any polling
                if keystate[sdl2.SDL_SCANCODE_ESCAPE]:
                    self.reset()

                # Delete selected entities
                if keystate[sdl2.SDL_SCANCODE_DELETE]:
                    for entity in self.selected_entities:
                        model.remove_entity(entity)
                    self.selected_entities.clear()
                    
                # Dragging and dropping files
                if self.polling == PollingType.LOADING\
                    and event.type == sdl2.SDL_DROPFILE:
                    self.load_filename = event.drop.file

                # Polling event
                if self.polling != PollingType.SELECTING:
                    self.handlers[self.polling].handle(
                        self, model, keystate, event,
                        screen_dimensions, commands)

                # Hotkeys for polling
                if keystate[sdl2.SDL_SCANCODE_LCTRL]\
                    or keystate[sdl2.SDL_SCANCODE_RCTRL]:
                    self.handle_ctrl_hotkeys(keystate)

                # + or - keys for camera zoom
                if keystate[sdl2.SDL_SCANCODE_KP_PLUS]:
                    # Create fake event to reuse camera zoom code
                    mock_event = sdl2.SDL_Event()
                    mock_event.wheel.y = 1
                    self.handle_camera_zoom(mock_event)
                if keystate[sdl2.SDL_SCANCODE_KP_MINUS]:
                    mock_event = sdl2.SDL_Event()
                    mock_event.wheel.y = -1
                    self.handle_camera_zoom(mock_event)

            # If any errors occur, reset the UI state
            except:
                self.reset()

        # Scroll camera using keyboard input
        # Do not scroll the camera if the user is typing text or if they
        # are pressing the CTRL key
        if self.polling != PollingType.ADDING_TEXT\
            and not keystate[sdl2.SDL_SCANCODE_LCTRL]:   
            self.camera.scroll(keystate)

        # Remove expired user interface messages and adjust positioning
        self.message_stack.update()
        
        # FPS displayer only for debugging
        # self.fps_displayer.update()

        return True

    def get_mouse_location(self):
        """Retrieves user's current mouse location on the screen from SDL.
        """
        mouse_x_ptr = pointer(c_int(0))
        mouse_y_ptr = pointer(c_int(0))
        sdl2.SDL_GetMouseState(mouse_x_ptr, mouse_y_ptr)

        self.mouse_x = mouse_x_ptr.contents.value
        self.mouse_y = mouse_y_ptr.contents.value

    def find_nearest_vertex(self, model):
        """Finds nearest vertex within range to the mouse position."""
        self.nearest_vertex = model.get_vertex_within_range((
            self.get_mouse_adjusted_to_camera_x(),
            self.get_mouse_adjusted_to_camera_y()))

    def user_quit(self, event, keystate):
        """Returns true if the user exited the application window or
        pressed ALT + F4 on the keyboard.
        """
        if event.type == sdl2.SDL_QUIT:
            return True

        if keystate[sdl2.SDL_SCANCODE_LALT] or keystate[sdl2.SDL_SCANCODE_RALT]:
            if keystate[sdl2.SDL_SCANCODE_F4]:
                return True

        return False

    def handle_ctrl_hotkeys(self, keystate):
        """Handles keyboard input if the user holds the CTRL key and pressed
        another key by setting the polling event accordingly.
        :param keystate: SDL keystate for checking if using is pressing SHIFT
        :type keystate: int[]
        """

        # Use erasing tool
        if keystate[sdl2.SDL_SCANCODE_E]:
            self.polling = PollingType.ERASING

        # Drawing a regular line
        if keystate[sdl2.SDL_SCANCODE_D]:
            self.polling = PollingType.DRAWING

        # Use moving tool...

        # Use measuring tool
        if keystate[sdl2.SDL_SCANCODE_M]:
            self.polling = PollingType.MEASURING

        # Adding user text
        if keystate[sdl2.SDL_SCANCODE_T]:
            self.polling = PollingType.ADDING_TEXT

        # Reset the camera position and scale
        if keystate[sdl2.SDL_SCANCODE_R]:
            self.camera.x = 0
            self.camera.y = 0
            self.camera.scale = 1.0

        # Display the drawing grid
        if keystate[sdl2.SDL_SCANCODE_G]:
            self.polling = PollingType.DISPLAY_GRID

        # Undo the last action
        if keystate[sdl2.SDL_SCANCODE_Z]:
            self.polling = PollingType.UNDOING

        # Redo the last undo
        if keystate[sdl2.SDL_SCANCODE_Y]:
            self.polling = PollingType.REDOING

        # Writing inventory to file
        if keystate[sdl2.SDL_SCANCODE_S]:
            self.polling = PollingType.SAVING

        # Writing inventory to file
        if keystate[sdl2.SDL_SCANCODE_I]:
            self.polling = PollingType.INVENTORY

        # Export drawing to png file
        if keystate[sdl2.SDL_SCANCODE_X]:
            self.polling = PollingType.EXPORTING

    def handle_text_input(self, event):
        """Updates the text the user is currently typing. Text can only
        consist of numbers if adding text is not the current polling event.
        """
        if event.type == sdl2.SDL_TEXTINPUT:
            if not self.polling == PollingType.ADDING_TEXT\
                and not str(event.text.text)[2:3].isdigit():
                self.text = ''
            else:
                self.text += str(event.text.text)[2:3]

    def update_bottom_right_text(self):
        """Updates text displayed on the bottom right of the screen to
        note the mouse's current x and y positions and the camera scale.
        If the user is pressing and dragging the mouse, it will also show
        the area of the rectangle.
        """
        adjusted_mouse_x = (self.mouse_x + self.camera.x) / self.camera.scale
        adjusted_mouse_y = (self.mouse_y + self.camera.y) / self.camera.scale

        if self.mouse_selection.w == 0 or self.mouse_selection.h == 0\
            or self.panning_camera:
            self.center_text.set_right_text('X: {} Y: {} - Zoom: {}'.format(
                int(adjusted_mouse_x), int(adjusted_mouse_y),
                round(self.camera.scale, 10)))
        else:
            width = self.mouse_selection.w
            height = self.mouse_selection.h
            area = width * height / 144.0
            self.center_text.set_right_text(
                'X: {} Y: {} - Zoom: {} - Area: {} ft^2'.format(
                int(adjusted_mouse_x), int(adjusted_mouse_y),
                round(self.camera.scale, 10), round(area)))

    def update_bottom_center_text(self, model):
        """Updates text displayed on the bottom middle of the screen to
        the entity type of the entity the user has their mouse hovered over.
        """
        entity = model.get_entity_on_location(self.get_adjusted_mouse(model))

        if entity == None:
            self.center_text.set_bottom_text()
        else:
            self.center_text.set_bottom_text(str(entity))

    def handle_single_entity_selection(self, model):
        """Selects a single entity that the user clicked on.
        :param model: The app model
        :type model: Model from 'model.py'
        """
        mouse = self.get_adjusted_mouse(model)
        x = mouse[0]
        y = mouse[1]

        # Call this function to reset selected field for all entities
        model.get_entities_in_rectangle()

        self.selected_entities.clear()
        result = model.get_entity_on_location((x, y))
        if result:
            self.selected_entities.add(result)

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
        :param event: SDL event for checking mouse clicks
        :type event: SDL_Event
        :param model: The app model
        :type model: Model from 'model.py'
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
            self.camera.x += 1930 * 0.030
            self.camera.y += 1080 * 0.030

        elif event.wheel.y < 0: # zooming out
            self.camera.scale -= 0.05
            self.camera.x -= 1930 * 0.030
            self.camera.y -= 1080 * 0.030

        # Keep camera scroll above 0
        if self.camera.scale <= 0.0:
            self.camera.scale = 0.05

    def handle_mouse_drag(self, event):
        """Handles user input for pressing and dragging the mouse.
        :param event: SDL event for checking mouse clicks
        :type event: SDL_Event
        """

        # User started pressing and dragging mouse
        if not self.mouse_down and event.type == sdl2.SDL_MOUSEBUTTONDOWN\
            and event.button.button == sdl2.SDL_BUTTON_LEFT:
            self.mouse_down = True

            # Mouse selection to select entities
            self.mouse_down_starting_x = int((self.mouse_x + self.camera.x)\
                / self.camera.scale)
            self.mouse_down_starting_y = int((self.mouse_y + self.camera.y)\
                / self.camera.scale)

            # Mouse selection to display
            self.displayed_selection_starting_x = self.mouse_x
            self.displayed_selection_starting_y = self.mouse_y

        # User finished pressing and dragging mouse
        if self.mouse_down and event.type == sdl2.SDL_MOUSEBUTTONUP:
            self.mouse_down = False

            # Reset rectangles
            self.mouse_selection.x = 0
            self.mouse_selection.y = 0
            self.mouse_selection.w = 0
            self.mouse_selection.h = 0
            
            self.displayed_selection.x = 0
            self.displayed_selection.y = 0
            self.displayed_selection.w = 0
            self.displayed_selection.h = 0

        # User is pressing and dragging mouse
        if self.mouse_down and event.type == sdl2.SDL_MOUSEMOTION:
            mouse_down_ending_x = int((self.mouse_x + self.camera.x)\
                / self.camera.scale)
            mouse_down_ending_y = int((self.mouse_y + self.camera.y)\
                / self.camera.scale)

            # Create rectangle for entity selection
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

            # Create rectangle to display
            if self.displayed_selection_starting_x < self.mouse_x:
                self.displayed_selection.x = self.displayed_selection_starting_x
            else:
                self.displayed_selection.x = self.mouse_x
            if self.displayed_selection_starting_y < self.mouse_y:
                self.displayed_selection.y = self.displayed_selection_starting_y
            else:
                self.displayed_selection.y = self.mouse_y

            self.displayed_selection.w = abs(
                self.displayed_selection_starting_x - self.mouse_x)
            self.displayed_selection.h = abs(
                self.displayed_selection_starting_y - self.mouse_y)

    def handle_one_point_placement(self, event, model):
        """Handles user input for placing an entity that only requires one
        point, e.g. window or door.
        :param event: SDL event for checking mouse clicks
        :type event: SDL_Event
        :param model: The app model
        :type model: Model from 'model.py'
        """

        adjusted_mouse = self.get_adjusted_mouse(model)
        adjusted_mouse_x = adjusted_mouse[0]
        adjusted_mouse_y = adjusted_mouse[1]

        # Exterior walls only for windows
        exterior_only = self.placement_type == EntityType.WINDOW

        result = model.get_nearest_wall(
            (adjusted_mouse_x, adjusted_mouse_y), exterior_only)

        # Display hint text
        if self.placement_type == EntityType.WINDOW:
            self.center_text.set_top_text(
                'Select center location for window on an exterior wall.')

        # No wall and user pressed
        if not result and event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            self.message_stack.insert(
                ('No exterior wall for window placement at that location.',))
            self.reset()
            return

        # No wall but user did not press. Continue to the next frame
        if not result:
            return

        self.nearest_line = result[0]
        self.nearest_vertex = result[1]
        
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if self.nearest_line.horizontal:
                if self.placement_type == EntityType.DOOR:
                    door = model.add_door(self.nearest_vertex, True,
                                   self.nearest_line.thickness)
                    door.layer = self.current_layer
                else:
                    window = model.add_window(self.nearest_vertex, True)
                    window.layer = self.current_layer
            elif self.nearest_line.vertical:
                if self.placement_type == EntityType.DOOR:
                    door = model.add_door(self.nearest_vertex, False,
                                   self.nearest_line.thickness)
                    door.layer = self.current_layer
                else:
                    window = model.add_window(self.nearest_vertex, False)
                    window.layer = self.current_layer

            self.reset()

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
            self.center_text.set_bottom_text(
                "Length: " + Tools.convert_to_unit_system(length))

        # Display hint text
        self.center_text.set_top_text(
            'Select starting and ending point. '
            + 'Press ESC to cancel placement. Hold SHIFT to align line to axis')

        # User placed the second point
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if self.horizontal_line:
                line = model.add_line(
                    self.placement_type,
                    (self.first_point_x, self.first_point_y),
                    (adjusted_mouse_x, self.first_point_y))
                line.layer = self.current_layer
            elif self.vertical_line:
                line = model.add_line(
                    self.placement_type,
                    (self.first_point_x, self.first_point_y),
                    (self.first_point_x, adjusted_mouse_y))
                line.layer = self.current_layer
            else:
                line = model.add_line(
                    self.placement_type,
                    (self.first_point_x, self.first_point_y),
                    (adjusted_mouse_x, adjusted_mouse_y))
                line.layer = self.current_layer

            self.reset()

    def handle_panel_input(self, event, screen_dimensions):
        """Handles user input on the user interface panels.
        Updates the polling event if the user presses a button on the top panel.
        :param model: The app model
        :type model: Model from 'model.py'
        :param screen_dimensions: The screen width and height.
        :type screen_dimensions: tuple(int, int)
        """
        for panel in self.panels:
            polling_event = []

            if panel.mouse_over(
                self.mouse_x, self.mouse_y, screen_dimensions):

                if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    panel.handle_mouse_click(self.mouse_x, self.mouse_y,
                                             self.center_text, polling_event)
                if event.type == sdl2.SDL_MOUSEMOTION:
                    panel.handle_mouse_hover(self.mouse_x, self.mouse_y,
                                             self.center_text)

            # Return if input on the panels created a polling event
            if len(polling_event) > 0:
                self.polling = polling_event[0]
                return

    def update_item_to_move(self):
        """Selects an entity from the selected to be the entity to move."""
        entity = None
        for entity in self.selected_entities:
            break
        self.item_to_move = entity

    def get_adjusted_mouse(self, model):
        """Returns the mouse's current position, adjusted to the snap interval
        or any nearby vertex or axis to snap to
        :param model: The app model
        :param type: Model from 'model.py'
        :return type: tuple(int, int)
        """

        # Snap to nearest vertex if nearby
        self.find_nearest_vertex(model)
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

    def get_two_point_placement(self, model):
        """Returns the first point the user placed and the projected second
        point, to be displayed as the user selects the second point.
        :param model: The app model
        :param type: Model from 'model.py'
        :return type: tuple(tuple(int, int), tuple(int, int))
        """
        if not (self.place_two_points and self.first_point_placed):
            return ((0, 0), (0, 0), 0)

        # TO DO: return the line created from the text input length

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
        return self.nearest_vertex

    def get_nearest_axis(self):
        """Returns nearest axis to snap to, if it exists.
        """
        if self.place_two_points:
            return self.nearest_vertex_axis
        return None

    def get_mouse_adjusted_to_camera_x(self):
        """Returns the mouse x-position adjusted to the camera offset and scale.
        """
        return int(self.mouse_x / self.camera.scale
                + self.camera.x / self.camera.scale)

    def get_mouse_adjusted_to_camera_y(self):
        """Returns the mouse y-position adjusted to the camera offset and scale.
        """
        return int(self.mouse_y / self.camera.scale
                + self.camera.y / self.camera.scale)

    def get_mouse_selection(self):
        """Returns the mouse selection to display if the user is not
        panning the camera."""
        if not self.panning_camera:
            return self.displayed_selection
        return None

    def reset(self):
        """Resets the controller's state.
        """
        self.polling = PollingType.SELECTING

        self.panning_camera = False
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.mouse_x = 0
        self.mouse_y = 0

        self.mouse_down = False
        self.mouse_selection = sdl2.SDL_Rect()
        self.displayed_selection = sdl2.SDL_Rect()

        self.place_one_point = False
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
        self.nearest_line = None
        self.placement_type = None

        self.mouse_down_starting_x = 0
        self.mouse_down_starting_y = 0
        self.displayed_selection_starting_x = 0
        self.displayed_selection_starting_y = 0

        self.text = ''

        self.load_filename = ''

        self.selected_entities = set()
        self.using_selection = False
        self.item_to_move = None
        self.last_selection = sdl2.SDL_GetTicks()

        self.use_start_vertex = True
        self.current_moving_vertex = None

        self.settings_panel.visible = False

        for panel in self.panels:
            panel.reset()

    def reset_text(self):
        """Resets the text being displayed on the user interface.
        """
        self.center_text.set_top_text('')
        self.center_text.set_bottom_text('')

    def init_handlers(self):
        """Initializes the poll event handlers.
        """
        # Top button panel
        self.handlers[PollingType.ERASING] = polling.Erasing()
        self.handlers[PollingType.DRAWING] = polling.Drawing()
        self.handlers[PollingType.MOVING] = polling.Moving()
        self.handlers[PollingType.MEASURING] = polling.Measuring()
        self.handlers[PollingType.ADDING_TEXT] = polling.AddingText()
        self.handlers[PollingType.PANNING] = polling.Panning()
        self.handlers[PollingType.ZOOMING] = polling.Zooming()
        self.handlers[PollingType.DISPLAY_GRID] = polling.DisplayGrid()
        self.handlers[PollingType.LAYERS] = polling.Layers()
        self.handlers[PollingType.SETTINGS] = polling.Settings()
        self.handlers[PollingType.UNDOING] = polling.Undoing()
        self.handlers[PollingType.REDOING] = polling.Redoing()
        self.handlers[PollingType.SAVING] = polling.Saving()
        self.handlers[PollingType.LOADING] = polling.Loading()
        self.handlers[PollingType.INVENTORY] = polling.WritingInventory()
        self.handlers[PollingType.EXPORTING] = polling.Exporting()

        # Left button panel
        self.handlers[PollingType.DRAW_EXTERIOR_WALL]\
            = polling.DrawExteriorWall()
        self.handlers[PollingType.DRAW_INTERIOR_WALL]\
            = polling.DrawInteriorWall()
        self.handlers[PollingType.DRAW_WINDOW]\
            = polling.DrawWindow()
        self.handlers[PollingType.DRAW_DOOR]\
            = polling.DrawDoor()

        # Right button panel
        self.handlers[PollingType.LAYER_0] = polling.SetLayer(0)
        self.handlers[PollingType.LAYER_1] = polling.SetLayer(1)
        self.handlers[PollingType.LAYER_2] = polling.SetLayer(2)
        self.handlers[PollingType.LAYER_3] = polling.SetLayer(3)

        # Settings panel
        self.handlers[PollingType.RASTERIZE] = polling.RasterizeGraphics()
        self.handlers[PollingType.VECTORIZE] = polling.VectorizeGraphics()

class Camera:
    # Regular camera scrolling speed (in/s)
    REGULAR_SCROLL_SPEED = 500

    # Fast camera scrolling (in/s)
    FAST_SCROLL_SPEED = 3000

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

class TimeStampedMessage(Text):
    """A text object with a time stamp (when the text was created)."""

    def __init__(self, text, relative_x = 0, relative_y = 0,
                 font = FontSize.SMALL, color = (0, 0, 0)):
        """Initializes the text."""
        Text.__init__(self, relative_x, relative_y, font, color)
        self.text = text
        self.time = sdl2.SDL_GetTicks()

    def __repr__(self):
        """Returns the text string for debugging."""
        return self.text

class TextDisplayer:
    """Base class for a user interface object that displays text."""

    def __init__(self):
        """Initializes the text displayer."""
        self.text = []

class CenterText(TextDisplayer):
    """Text displayer responsible for displaying text on the top center,
    bottom center, and bottom right of the application window."""

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

class MessageStack(TextDisplayer):
    """Text displayer responsible for displaying stacking messages to the user
    on the bottom left of the screen. Messages stay on the screen for the
    duration and stack as more messages appear."""

    # Time the message stays in the stack (ms)
    DURATION = 5000
    
    # Relative positions
    RELATIVE_X = 0.05
    RELATIVE_Y = 0.95

    # Spacing between texts
    SPACING = 0.03

    def update(self):
        """Removes expired messages and adjusts the positions of the messages
        so that they stack.
        """
        index = 0
        for message in self.text:
            message.relative_y = MessageStack.RELATIVE_Y\
                - MessageStack.SPACING * index
            index += 1

            if MessageStack.DURATION < sdl2.SDL_GetTicks() - message.time:
                self.text.remove(message)
                return

    def insert(self, list):
        """Inserts the messages from the list into the stack.
        :param list: List of messages to insert
        :type list: list
        """
        for message in list:
            self.text.append(TimeStampedMessage(
                message, MessageStack.RELATIVE_X))

class FPSDisplayer(TextDisplayer):
    """Text displayer responsible for displaying the average FPS every second
    on the top right corner of the screen."""

    # Relative positions
    RELATIVE_X = 0.99
    RELATIVE_Y = 0.06

    def __init__(self):
        """Initializes the FPS displayer."""
        TextDisplayer.__init__(self)
        self.text.append(Text(FPSDisplayer.RELATIVE_X, FPSDisplayer.RELATIVE_Y))

        self.last_fps = sdl2.SDL_GetTicks()
        self.frames = 0

    def update(self):
        """Updates the average frames per second of the controller thread.
        """
        self.frames += 1
        if 1000 < sdl2.SDL_GetTicks() - self.last_fps:
            self.text[0].text = 'FPS: ' + str(self.frames)
            self.last_fps = sdl2.SDL_GetTicks()
            self.frames = 0

class Button:
    """Button that the user can click in the application window."""

    def __init__(self, id, texture, relative_x = 0, relative_y = 0,
                 relative_width = 0, relative_height = 0):
        """Initializes the button."""
        self.id = id
        self.texture = texture
        self.relative_x = relative_x
        self.relative_y = relative_y
        self.relative_width = relative_width
        self.relative_height = relative_height

        # Whether the button is currently selected by the user
        self.selected = False

    def mouse_over(self, mouse_x, mouse_y, screen_dimensions):
        """Returns true if the mouse positions collide with the button.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        :param screen_dimensions: Screen width and height
        :type screen_dimensions: tuple(int, int)
        """

        # Screen dimensions
        screen_width = screen_dimensions[0]
        screen_height = screen_dimensions[1]

        location = sdl2.SDL_Rect(
            int(self.relative_x * screen_width),
            int(self.relative_y * screen_height),
            int(self.relative_width * screen_width),
            int(self.relative_height * screen_height))

        if mouse_x > location.x + location.w: return False
        if mouse_x < location.x: return False
        if mouse_y > location.y + location.h: return False
        if mouse_y < location.y: return False
        return True

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

        # The button the user currently has their mouse over
        self.button_over = None

        # Whether this panel is visible to the user
        self.visible = True

        # Set of buttons the panel houses
        self.buttons = set()

        # Whether the panel has a special rendering function
        # If so, the renderer will skip it when iterating the normal panels
        self.special_rendering = False

    def mouse_over(self, mouse_x, mouse_y, screen_dimensions):
        """Returns true if mouse positions collide with any of the buttons
        in the panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        if not self.visible:
            return False

        for button in self.buttons:
            if button.mouse_over(mouse_x, mouse_y, screen_dimensions):
                self.button_over = button.id
                return True
            self.button_over = None
        return False

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Sets the selected button and adds a polling event.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        for button in self.buttons:
            if button.id == self.button_over:
                button.selected = True
            else:
                button.selected = False

        polling_event.append(self.button_over)

    def handle_mouse_hover(self, mouse_x, mouse_y, center_text):
        """Sets the center bottom text to the button the user is hovering over.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        center_text.set_bottom_text(self.button_labels[self.button_over])

    def reset(self):
        """Resets the selected attribute of all buttons."""
        for button in self.buttons:
            button.selected = False

class CenterButtonPanel(Panel):
    """The main user interface panel appearing at the top center of the screen.
    """

    NUM_BUTTONS = 18

    RELATIVE_X = 0.0
    RELATIVE_Y = 0.0
    RELATIVE_WIDTH = 1.0
    RELATIVE_HEIGHT = 0.05

    BUTTON_RELATIVE_SIZE = 0.03
    BUTTONS_TOTAL_WIDTH = 0.60
    BUTTONS_X_BUFFER = (RELATIVE_WIDTH - BUTTONS_TOTAL_WIDTH) / 2
    BUTTONS_Y_BUFFER = 0.01

    def get_relative_x(self):
        """Returns the relative x-position of the button based on the
        number of buttons already added."""
        return len(self.buttons) / CenterButtonPanel.NUM_BUTTONS\
            * CenterButtonPanel.BUTTONS_TOTAL_WIDTH\
            + CenterButtonPanel.BUTTONS_X_BUFFER;

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL,
                        CenterButtonPanel.RELATIVE_X,
                        CenterButtonPanel.RELATIVE_Y,
                        CenterButtonPanel.RELATIVE_WIDTH,
                        CenterButtonPanel.RELATIVE_HEIGHT)

        # TO DO: put these in a loop:
        self.buttons.add(Button(len(self.buttons), EntityType.SELECT_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.ERASE_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.DRAW_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.MOVE_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.MEASURE_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.ADD_TEXT_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.PAN_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.ZOOM_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.GRID_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.LAYERS_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.SETTINGS_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.UNDO_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.REDO_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.SAVE_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.LOAD_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.EXPORT_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.INVENTORY_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons), EntityType.EXIT_BUTTON,
            self.get_relative_x(),
            CenterButtonPanel.RELATIVE_Y + CenterButtonPanel.BUTTONS_Y_BUFFER,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE,
            CenterButtonPanel.BUTTON_RELATIVE_SIZE))

        self.button_labels =\
            [
                'Select',
                'Eraser Tool (CTRL + E)',
                'Draw Line (CTRL + D)',
                'Move',
                'Measure Distance (CTRL + M)',
                'Add Text (CTRL + T)',
                'Pan Camera',
                'Zoom Camera',
                'Display Drawing Grid (CTRL + G)',
                'Open Layers',
                'Application Settings',
                'Undo (CTRL + Z)',
                'Redo (CTRL + Y)',
                'Save Drawing (CTRL + S)',
                'Load Drawing',
                'Export to PNG (CTRL + E)',
                'List All Entities to File (CTRL + I)',
                'Exit Application (ALT + F4)',
            ]

class LeftButtonPanel(Panel):
    """The user interface panel appearing at the left side of the screen.
    """

    NUM_BUTTONS = 4

    BUTTON_RELATIVE_SIZE = 0.03
    BUTTONS_TOTAL_HEIGHT = 0.14
    BUTTONS_X_BUFFER = 0.005
    BUTTONS_Y_BUFFER = 0.01

    RELATIVE_X = 0.0
    RELATIVE_WIDTH = 0.04
    RELATIVE_HEIGHT = BUTTONS_TOTAL_HEIGHT + 1.5 * BUTTONS_Y_BUFFER
    RELATIVE_Y = (1.0 - RELATIVE_HEIGHT) / 2

    BUTTONS_Y_BUFFER = RELATIVE_Y + BUTTONS_Y_BUFFER

    def get_relative_y(self):
        """Returns the relative y-position of the button based on the
        number of buttons already added."""
        return len(self.buttons) / LeftButtonPanel.NUM_BUTTONS\
            * LeftButtonPanel.BUTTONS_TOTAL_HEIGHT\
            + LeftButtonPanel.BUTTONS_Y_BUFFER

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL,
                        LeftButtonPanel.RELATIVE_X,
                        LeftButtonPanel.RELATIVE_Y,
                        LeftButtonPanel.RELATIVE_WIDTH,
                        LeftButtonPanel.RELATIVE_HEIGHT)

        self.buttons.add(Button(len(self.buttons),
            EntityType.EXTERIOR_WALL_BUTTON,
            LeftButtonPanel.RELATIVE_X + LeftButtonPanel.BUTTONS_X_BUFFER,
            self.get_relative_y(),
            LeftButtonPanel.BUTTON_RELATIVE_SIZE,
            LeftButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons),
            EntityType.INTERIOR_WALL_BUTTON,
            LeftButtonPanel.RELATIVE_X + LeftButtonPanel.BUTTONS_X_BUFFER,
            self.get_relative_y(),
            LeftButtonPanel.BUTTON_RELATIVE_SIZE,
            LeftButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons),
            EntityType.WINDOW_BUTTON,
            LeftButtonPanel.RELATIVE_X + LeftButtonPanel.BUTTONS_X_BUFFER,
            self.get_relative_y(),
            LeftButtonPanel.BUTTON_RELATIVE_SIZE,
            LeftButtonPanel.BUTTON_RELATIVE_SIZE))
        self.buttons.add(Button(len(self.buttons),
            EntityType.DOOR_BUTTON,
            LeftButtonPanel.RELATIVE_X + LeftButtonPanel.BUTTONS_X_BUFFER,
            self.get_relative_y(),
            LeftButtonPanel.BUTTON_RELATIVE_SIZE,
            LeftButtonPanel.BUTTON_RELATIVE_SIZE))

        self.button_labels =\
            [
                'Draw Exterior Wall',
                'Draw Interior Wall',
                'Draw Window',
                'Draw Door',
            ]

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Same as Panel.handle_mouse_click but adjusts the polling event
        to account for the number of buttons in the central button panel.
        """
        Panel.handle_mouse_click(self, mouse_x, mouse_y,
                                 center_text, polling_event)
        polling_event[0] += CenterButtonPanel.NUM_BUTTONS

class RightButtonPanel(Panel):
    """The user interface panel appearing at the right side of the screen.
    """

    NUM_BUTTONS = 4

    BUTTON_RELATIVE_SIZE = 0.03
    BUTTONS_TOTAL_HEIGHT = 0.14
    BUTTONS_X_BUFFER = 0.005
    BUTTONS_Y_BUFFER = 0.01

    RELATIVE_X = 0.961
    RELATIVE_WIDTH = 0.04
    RELATIVE_HEIGHT = BUTTONS_TOTAL_HEIGHT + 1.5 * BUTTONS_Y_BUFFER
    RELATIVE_Y = (1.0 - RELATIVE_HEIGHT) / 2

    BUTTONS_Y_BUFFER = RELATIVE_Y + BUTTONS_Y_BUFFER

    def get_relative_y(self):
        """Returns the relative y-position of the button based on the
        number of buttons already added."""
        return len(self.buttons) / RightButtonPanel.NUM_BUTTONS\
            * RightButtonPanel.BUTTONS_TOTAL_HEIGHT\
            + RightButtonPanel.BUTTONS_Y_BUFFER

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL,
                        RightButtonPanel.RELATIVE_X,
                        RightButtonPanel.RELATIVE_Y,
                        RightButtonPanel.RELATIVE_WIDTH,
                        RightButtonPanel.RELATIVE_HEIGHT)

        for button in range(RightButtonPanel.NUM_BUTTONS):
            self.buttons.add(Button(len(self.buttons),
                EntityType.LAYER,
                RightButtonPanel.RELATIVE_X + RightButtonPanel.BUTTONS_X_BUFFER,
                self.get_relative_y(),
                RightButtonPanel.BUTTON_RELATIVE_SIZE,
                RightButtonPanel.BUTTON_RELATIVE_SIZE))

        self.button_labels =\
            [
                'Layer 1',
                'Layer 2',
                'Layer 3',
                'Layer 4',
            ]

        # Not visible by default
        self.visible = False

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Same as Panel.handle_mouse_click but adjusts the polling event
        to account for the number of buttons in the previous panel.
        """
        Panel.handle_mouse_click(self, mouse_x, mouse_y,
                                 center_text, polling_event)
        polling_event[0] += CenterButtonPanel.NUM_BUTTONS\
            + LeftButtonPanel.NUM_BUTTONS

class SettingsPanel(Panel):
    """The settings panel appearing on the center of the screen when
    the user toggles it by pressing the settings button."""

    RELATIVE_WIDTH = 0.20
    RELATIVE_HEIGHT = 0.20
    RELATIVE_X = (1.0 - RELATIVE_WIDTH) / 2.0
    RELATIVE_Y = (1.0 - RELATIVE_HEIGHT) / 2.0

    def __init__(self):
        """Initializes the settings buttons in the panel."""

        Panel.__init__(self, EntityType.BUTTON_PANEL,
                       SettingsPanel.RELATIVE_X,
                       SettingsPanel.RELATIVE_Y,
                       SettingsPanel.RELATIVE_WIDTH,
                       SettingsPanel.RELATIVE_HEIGHT)

        self.buttons = set()
        self.buttons.add(GraphicsButton())

        self.visible = False

        self.special_rendering = True

        self.button_labels =\
            [
                'Rasterize graphics - default setting',
                'Vectorize graphics - requires higher performance CPU/GPU',
            ]

    def mouse_over(self, mouse_x, mouse_y, screen_dimensions):
        """Returns true if mouse positions collide with any of the buttons
        in the panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        if not self.visible:
            return False

        for settings in self.buttons:
            for button in settings.buttons:
                if button.mouse_over(mouse_x, mouse_y, screen_dimensions):
                    self.button_over = button.id
                    return True
                self.button_over = None
        return False

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Sets the selected button and adds a polling event.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        for settings in self.buttons:
            for button in settings.buttons:
                if button.id == self.button_over:
                    # Currently, do not allow the user
                    # to select vectorized graphics
                    if button.id != 1:
                        button.selected = True
                    else:
                        settings.buttons[0].selected = True
                else:
                    button.selected = False

        polling_event.append(self.button_over + CenterButtonPanel.NUM_BUTTONS\
            + LeftButtonPanel.NUM_BUTTONS + RightButtonPanel.NUM_BUTTONS)

class SettingsButton:
    """A mini-panel on the settings that has a top and bottom text and
    at least two buttons."""

    TEXT_BUFFER = SettingsPanel.RELATIVE_HEIGHT * 0.15

    def __init__(self, button_relative_y = 0, top_text = '', bottom_text = '',
                 num_buttons = 0):
        """Initializes the top/bottom texts and buttons at the
        relative location."""
        self.top_text = Text(
            SettingsPanel.RELATIVE_X + SettingsPanel.RELATIVE_WIDTH / 2,
            button_relative_y - SettingsButton.TEXT_BUFFER, FontSize.LARGE,
            (127, 127, 127))
        self.top_text.text = top_text

        self.bottom_text = Text(
            SettingsPanel.RELATIVE_X + SettingsPanel.RELATIVE_WIDTH / 2,
            button_relative_y, FontSize.SMALL, (127, 127, 127))
        self.bottom_text.text = bottom_text

        self.num_buttons = num_buttons

        self.buttons = []
        self.selected_button = None

class GraphicsButton(SettingsButton):
    """The settings button for changing between using vectorized or
    rasterized graphics."""

    BUTTON_SIZE = 0.05
    RELATIVE_Y = SettingsPanel.RELATIVE_Y\
        + (SettingsPanel.RELATIVE_HEIGHT * 0.50)
    TEXT_RELATIVE_Y = RELATIVE_Y - (SettingsPanel.RELATIVE_HEIGHT * 0.15)

    BUTTON_BUFFER = 0.05

    def __init__(self):
        """Initializes the rasterize and vectorize button and top/bottom text.
        """
        SettingsButton.__init__(self, GraphicsButton.TEXT_RELATIVE_Y,
                                'Vectorize Graphics:',
                                'OFF / ON', 2)

        self.buttons.append(Button(0, EntityType.RASTERIZE,
                                   SettingsPanel.RELATIVE_X
                                   + GraphicsButton.BUTTON_BUFFER,
                                   GraphicsButton.RELATIVE_Y,
                                   GraphicsButton.BUTTON_SIZE,
                                   GraphicsButton.BUTTON_SIZE))
        self.buttons.append(Button(1, EntityType.VECTORIZE,
                                   SettingsPanel.RELATIVE_X
                                   + 2.0 * GraphicsButton.BUTTON_BUFFER,
                                   GraphicsButton.RELATIVE_Y,
                                   GraphicsButton.BUTTON_SIZE,
                                   GraphicsButton.BUTTON_SIZE))

        self.selected_button = self.buttons[0]
        self.buttons[0].selected = True