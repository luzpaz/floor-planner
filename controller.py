import math, panels, polling, sdl2, sdl2.ext, text

from camera import Camera
from ctypes import c_int, pointer
from entity_types import EntityType
from entities import Line
from tools import Tools, ExportCommand
from polling import PollingType

class Controller:
    """Handles user input on the model."""

    def __init__(self):
        """Initializes the user camera, UI text displayers, and UI panels."""

        self.camera = Camera()
        self.init_text_displayers()
        self.init_panels()
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
        
        # Entities moved by the user that need additional adjustments
        # (entity that was moved : entity, new location : tuple(int, int))
        self.moved_entities = set()

        self.allow_drag_and_drop()

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
                if keystate[sdl2.SDL_SCANCODE_KP_0]\
                    or keystate[sdl2.SDL_SCANCODE_0]: # exterior wall
                    self.reset()
                    self.placement_type = EntityType.EXTERIOR_WALL
                    self.line_thickness = Line.EXTERIOR_WALL
                    self.place_two_points = True
                elif keystate[sdl2.SDL_SCANCODE_KP_1]\
                    or keystate[sdl2.SDL_SCANCODE_1]: # interior wall
                    self.reset()
                    self.placement_type = EntityType.INTERIOR_WALL
                    self.line_thickness = Line.INTERIOR_WALL
                    self.place_two_points = True
                elif keystate[sdl2.SDL_SCANCODE_KP_2]\
                    or keystate[sdl2.SDL_SCANCODE_2]: # window
                    self.polling = PollingType.DRAW_WINDOW
                elif keystate[sdl2.SDL_SCANCODE_KP_3]\
                    or keystate[sdl2.SDL_SCANCODE_3]: # door
                    self.polling = PollingType.DRAW_DOOR

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
                        try:
                            model.remove_entity(entity)
                        except:
                            pass
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

                # Adjust moved entities if necessary
                self.adjust_moved_entities(model)

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

        # Save to file
        if keystate[sdl2.SDL_SCANCODE_S]:
            self.polling = PollingType.SAVING

        # Load file
        if keystate[sdl2.SDL_SCANCODE_O]:
            self.polling = PollingType.LOADING

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
        elif self.placement_type == EntityType.DOOR:
            self.center_text.set_top_text(
                'Select center location for door on a wall.')

        # No wall and user pressed
        if not result and event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if self.placement_type == EntityType.WINDOW:
                self.message_stack.insert(
                ('No exterior wall for window placement at that location.',))
            elif self.placement_type == EntityType.DOOR:
                self.message_stack.insert(
                ('No wall for door placement at that location.',))
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
            if self.horizontal_line:
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

    def adjust_moved_entities(self, model):
        """Makes adjustments if necessary to entities moved by the user.
        For example, snaps doors or windows to the nearest wall if the user
        moved them to a new location.
        :param model: The app model
        :type model: Model from 'model.py'
        """
        for moved in self.moved_entities:
            moved[0].adjust(model, moved[1])
        self.moved_entities.clear()

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
    
    def allow_drag_and_drop(self):
        """Allows dragging and dropping files onto the application window.
        """
        sdl2.SDL_EventState(sdl2.SDL_DROPFILE, sdl2.SDL_ENABLE)

    def reset(self):
        """Resets the controller's state.
        """

        # Current poll event
        self.polling = PollingType.SELECTING

        # Whether the user is panning the camera
        self.panning_camera = False

        # Camera pan start positions
        self.pan_start_x = 0
        self.pan_start_y = 0

        # Current frame absolute mouse position (on the window)
        self.mouse_x = 0
        self.mouse_y = 0

        # Whether the user is holding down the mouse
        self.mouse_down = False

        # Mouse press and drag selection rectangle, relative to the camera
        self.mouse_selection = sdl2.SDL_Rect()

        # Mouse press and drag selection rectangle, absolute to the window
        self.displayed_selection = sdl2.SDL_Rect()

        # Mouse press and drag starting positions
        self.mouse_down_starting_x = 0
        self.mouse_down_starting_y = 0
        self.displayed_selection_starting_x = 0
        self.displayed_selection_starting_y = 0

        # Whether the user is placing an object that requires one point
        # e.g. window, door
        self.place_one_point = False

        # Whether the user is placing an object that requires two points
        # e.g. line, exterior/interior wall
        self.place_two_points = False

        # Whether the user placed the first point of the two-point placement
        # e.g. placed first point of the line
        self.first_point_placed = False

        # First and second point positions
        self.first_point_x = 0
        self.first_point_y = 0
        self.second_point_x = 0
        self.second_point_y = 0

        # Whether the line placement by the user is snapping to an axis
        # e.g. user is placing a line while holding the shift key
        self.horizontal_line = False
        self.vertical_line = False

        # Thickness of the current line placement
        self.line_thickness = 0

        # Nearest vertex to snap to
        self.nearest_vertex = None

        # Nearest vertex axis to snap to
        self.nearest_vertex_axis = None

        # Nearest line to place door/window on
        self.nearest_line = None

        # Line placement type: regular line, exterior line, interior line, etc.
        self.placement_type = None

        # Text typed by the user
        self.text = ''

        # Filename to load
        self.load_filename = ''

        # Entities selected by the user
        self.selected_entities = set()

        # Whether the user is using the current selection
        # e.g. user is moving the selected entity, so a subsequent mouse click
        # for the move location should not deselect the entity
        # or select a new entity
        self.using_selection = False

        # Item that the user is moving
        self.item_to_move = None

        # Last time user selected an entity
        self.last_selection = sdl2.SDL_GetTicks()

        # Which vertex the user is moving an entity in reference too
        # e.g. start or end vertex of a line, or left/right end of a
        # horizontal window
        self.current_moving_vertex = None

        # Whether the user is moving an entity based on the start or end vertex
        # for a line, or the left/right top/bottom vertex for a door/window
        self.use_start_vertex = True

        # Calls the abstract reset method for all panels
        for panel in self.panels:
            panel.reset()

    def reset_text(self):
        """Resets the text being displayed on the user interface.
        """
        self.center_text.set_top_text('')
        self.center_text.set_bottom_text('')

    def init_text_displayers(self):
        """Initializes the center text displayer and message stack.
        """
        self.text_displayers = []
        self.center_text = text.CenterText()
        self.message_stack = text.MessageStack()
        self.text_displayers.append(self.center_text)
        self.text_displayers.append(self.message_stack)

    def init_panels(self):
        """Initializes the center, left, and right button panels.
        """
        self.panels = []
        self.panels.append(panels.CenterButtonPanel())
        self.panels.append(panels.LeftButtonPanel())
        self.layers_panel = panels.RightButtonPanel()
        self.panels.append(self.layers_panel)

    def init_handlers(self):
        """Initializes the poll event handlers.
        """
        self.handlers = [None] * PollingType.NUM_TYPES

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
        self.handlers[PollingType.UNDOING] = polling.Undoing()
        self.handlers[PollingType.REDOING] = polling.Redoing()
        self.handlers[PollingType.SAVING] = polling.Saving()
        self.handlers[PollingType.LOADING] = polling.Loading()
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