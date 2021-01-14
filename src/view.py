import ctypes, sdl2, sdl2.sdlgfx, sdl2.sdlimage, sdl2.sdlttf

from ctypes import c_int, pointer
from entity_types import EntityType
from enum import Enum
from textures import Textures

class View:
    """Responsible for rendering entities from the model and the user
    interface onto the screen.
    """

    def __init__(self):
        """Initializes SDL subsystems, SDL components, textures, and fonts
        necessary for rendering.
        """
        self.init_sdl_subsystems()
        self.determine_window_size()
        self.init_window()
        self.init_renderer()
        self.set_dpi_awareness()
        self.init_textures()
        self.init_fonts()

    def update(self, model, controller):
        """Updates the application window with entities from the model
        and the user interface.
        """

        try:
            self.clear_buffer()
            self.fetch_camera_values(controller)

            if model.update_needed:
                self.update_screen_size()
                self.resize_fonts()
                self.update_layer(model, controller)
                model.update_needed = False

            self.render_layer(controller.current_layer)
            self.render_text_from_model(controller, model)

            self.render_ui_panels(controller)
            self.render_ui_text(controller)
            self.render_two_point_placement(controller, model)
            self.render_moving_vertex(controller)
            self.render_mouse_selection(controller)

            if controller.loading:
                self.render_loading()

            self.swap_buffer()
        except:
            return
        
    def clear_buffer(self):
        """Clears the contents displayed on the window.
        """
        sdl2.SDL_SetRenderDrawColor(self.renderer, 128, 128, 128, 255)
        sdl2.SDL_RenderClear(self.renderer)

    def swap_buffer(self):
        """Updates the window with the rendered content.
        """
        sdl2.SDL_RenderPresent(self.renderer)

    def fetch_camera_values(self, controller):
        """Stores camera attributes as class values for easier access.
        """
        self.camera_x = controller.camera.x
        self.camera_y = controller.camera.y
        self.camera_scale = controller.camera.scale

    def update_screen_size(self):
        """Sets the screen width and height to the application's current
        window resolution, necessary when user resizes the window.
        """
        width = pointer(c_int(0))
        height = pointer(c_int(0))
        sdl2.SDL_GetWindowSize(self.window, width, height)
        self.screen_width = width.contents.value
        self.screen_height = height.contents.value

    def update_layer(self, model, controller):
        """Renders entities from model onto their corresponding layer.
        This optimizes rendering as rendering the layer once renders all
        entities simultaneously, instead of rendering each entity every frame.
        """
        sdl2.SDL_SetRenderTarget(self.renderer, self.textures.get_layer(
                                 controller.current_layer))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderClear(self.renderer)

        return self.render_entities(model, controller)

    def render_entities(self, model, controller):
        """Renders the entities from the model onto the renderer target.
        """

        entities_rendered = 0

        # Render drawing grid
        if controller.display_grid:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0xB2, 0xB2, 0xB2, 0xFF);
            for i in range(self.layer_width):
                sdl2.SDL_RenderDrawLine(
                    self.renderer, -controller.snap_interval,
                    i * controller.snap_interval * 2,
                    self.layer_width,
                    i * controller.snap_interval * 2)
                sdl2.SDL_RenderDrawLine(
                    self.renderer, i * controller.snap_interval * 2,
                    -controller.snap_interval,
                    i * controller.snap_interval * 2,
                    self.layer_width)

        # Render lines
        for line in model.lines:
            if line.layer != controller.current_layer:
                continue
            self.render_line(line, controller.current_layer)
            entities_rendered += 1

        # Render square vertices to close the gap between connecting lines
        for vertex in model.square_vertices:
            if vertex.layer != controller.current_layer:
                continue
            self.render_square_vertex(vertex)
            entities_rendered += 1

        # Render windows
        for window in model.windows:
            if window.layer != controller.current_layer:
                continue
            self.render_window(window, controller.current_layer)
            entities_rendered += 1

        # Render doors
        for door in model.doors:
            if door.layer != controller.current_layer:
                continue
            self.render_door(door, controller.current_layer)
            entities_rendered += 1

        sdl2.SDL_SetRenderTarget(self.renderer, None)
        return entities_rendered

    def render_layer(self, layer):
        """Renders all contents of the layer onto the screen.
        :param layer: The layer index from the Textures class to render
        :type layer: int
        """
        sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get_layer(layer), None,
            sdl2.SDL_Rect(int(-self.camera_x),
                          int(-self.camera_y),
                          int(self.layer_width * self.camera_scale),
                          int(self.layer_height * self.camera_scale)))

    def render_text_from_model(self, controller, model):
        """Renders the user placed text from the model.
        :param controller: The application controller
        :type controller: Controller from 'controller.py'
        :param model: The application model
        :type model: Model from 'model.py'
        """
        for text in model.user_text:
            if text.layer != controller.current_layer:
                continue
            self.render_user_text(text)

    def render_ui_text(self, controller):
        """Renders all text in text displayers from the user interface.
        :param controller: The application controller.
        :type controller: Controller from 'controller.py'
        """
        text_rendered = 0

        for text_displayer in controller.text_displayers:
            for text in text_displayer.text:
                self.render_relative_text(text)
                text_rendered += 1

        return text_rendered

    def render_relative_text(self, text):
        """Renders text at its relative location with its font and color.
        :param text: The text to render
        :type text: Text from 'controller.py'
        """
        if not text or not text.text:
            return None

        if text.font == FontSize.SMALL:
            font = self.small_text
        elif text.font == FontSize.MEDIUM:
            font = self.medium_text
        elif text.font == FontSize.LARGE:
            font = self.large_text

        surface = sdl2.sdlttf.TTF_RenderText_Solid(
            font, str.encode(text.text), text.color)

        # Failed to create surface
        if not surface: return None

        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)

        width = pointer(c_int(0))
        height = pointer(c_int(0))
        sdl2.SDL_QueryTexture(texture, None, None, width, height)
        width = width.contents.value
        height = height.contents.value

        # Center the text relative to the screen width
        if text.relative_x == 0.50:
            text_x = int(self.center_text(width))
        # Place text at its specified relative location
        else:
            text_x = int(text.relative_x * self.screen_width)

        text_y = int(self.screen_height * text.relative_y)

        # Adjust location of text to fit the screen
        if text.relative_y > 0.50:
            text_y -= height

        if text.relative_x > 0.50:
            text_x -= width

        sdl2.SDL_RenderCopyEx(self.renderer, texture, None,
                              sdl2.SDL_Rect(text_x, text_y, width, height),
                              0.0, None, sdl2.SDL_FLIP_NONE)
        sdl2.SDL_DestroyTexture(texture)
        return True

    def render_user_text(self, text, centered = True):
        """Renders text at its absolute location in black with tiny font.
        :param text: The text to render
        :type text: UserText from 'entities.py'
        :param centered: Whether to center the text within its location
        :type centered: boolean
        """
        if not text or not text.text:
            return None

        font = self.tiny_text

        surface = sdl2.sdlttf.TTF_RenderText_Solid(
            font, str.encode(text.text), sdl2.SDL_Color(0, 0, 0))

        # Failed to create surface
        if not surface: return None

        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)

        width = pointer(c_int(0))
        height = pointer(c_int(0))
        sdl2.SDL_QueryTexture(texture, None, None, width, height)
        width = width.contents.value
        height = height.contents.value

        text_x = text.position[0]
        text_y = text.position[1]

        # Adjust to camera
        text_x = int(text_x * self.camera_scale - self.camera_x - width / 2)
        text_y = int(text_y * self.camera_scale - self.camera_y - height / 2)

        # Underline text if selected
        if text.selected:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
            sdl2.SDL_RenderDrawLine(self.renderer, text_x, text_y + height,
                                    text_x + width, text_y + height)

        sdl2.SDL_RenderCopyEx(self.renderer, texture, None,
                              sdl2.SDL_Rect(text_x, text_y, width, height),
                              0.0, None, sdl2.SDL_FLIP_NONE)
        sdl2.SDL_DestroyTexture(texture)
        return True

    def center_text(self, text_width):
        """Returns the x-postion needed to center the text width for the
        current screen width.
        :param text_width: Width of the text to center
        :type text_width: int
        """
        return int(self.screen_width / 2 - text_width / 2)

    def render_ui_panels(self, controller):
        """Renders the user interface panels onto the screen.
        :param controller: The application controller
        :type controller: Controller from 'controller.py'
        """
        for panel in controller.panels:
            if not panel.visible or panel.special_rendering:
                continue

            self.render_panel(panel)

            for button in panel.buttons:
                self.render_button(button)

    def render_settings_panel(self, controller):
        """Renders the settings panel to the screen with its buttons and text.
        :param controller: The application controller
        :type controller: Controller from 'controller.py'
        """
        self.render_panel(controller.settings_panel)

        for settings_button in controller.settings_panel.buttons:
            self.render_relative_text(settings_button.top_text)
            self.render_relative_text(settings_button.bottom_text)

            for button in settings_button.buttons:
                self.render_button(button)

    def render_panel(self, panel):
        """Renders the panel onto the screen.
        :param panel: The panel to render
        :type panel: Panel from 'controller.py'
        """
        location = sdl2.SDL_Rect(
            int(panel.relative_x * self.screen_width),
            int(panel.relative_y * self.screen_height),
            int(panel.relative_width * self.screen_width),
            int(panel.relative_height * self.screen_height))
        sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(panel.texture), None, location)
        
    def render_button(self, button):
        """Renders the buttons onto the screen.
        :param button: The button to render
        :type button: Button from 'controller.py'
        """
        location = sdl2.SDL_Rect(
            int(button.relative_x * self.screen_width),
            int(button.relative_y * self.screen_height),
            int(button.relative_width * self.screen_width),
            int(button.relative_height * self.screen_height))

        if button.selected:
            sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(EntityType.SELECTED_BUTTON.value),
            None, location)
        else:
            sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(EntityType.BUTTON_BACKGROUND.value),
            None, location)
        
        # Change render location to a square
        previous_width = location.w
        location.x += int(previous_width / 4)

        if location.w < location.h:
            location.h = location.w
        elif location.h < location.w:
            location.w = location.h

        sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(button.texture), None, location)

    def render_two_point_placement(self, controller, model):
        """Renders current line placement by the user and indicators
        around vertices that it may snap to or axes it may align with.
        :param controller: The application controller
        :type controller: Controller from 'controller.py'
        :param model: The application model
        :type model: Model from 'model.py'
        """
        line = controller.get_two_point_placement(model)
        
        if not (line[0][0] == 0 and line[0][1] == 0\
           and line[1][0] == 0 and line[1][1] == 0):
            self.render_line_placement(line)        

        # Render snapping to nearest vertex if applicable
        nearest_vertex = controller.get_nearest_vertex()
        if nearest_vertex:
            sdl2.sdlgfx.filledCircleRGBA(
                self.renderer,
                int(nearest_vertex[0] * self.camera_scale - self.camera_x),
                int(nearest_vertex[1] * self.camera_scale - self.camera_y),
                int(3.0 * self.camera_scale), 255, 0, 0, 255)

        # Render snapping to nearest vertex axis if applicable
        nearest_vertex_axis = controller.get_nearest_axis()
        if nearest_vertex_axis:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
            sdl2.SDL_RenderDrawLine(
                self.renderer,
                int(controller.mouse_x * self.camera_scale - self.camera_x),
                int(controller.mouse_y * self.camera_scale - self.camera_y),
                int(nearest_vertex_axis[0] * self.camera_scale - self.camera_x),
                int(nearest_vertex_axis[1] * self.camera_scale - self.camera_y))
        return True

    def render_moving_vertex(self, controller):
        """Renders the current moving vertex (the vertex used as the reference
        for the entity that the user is moving).
        :param controller: The application controller
        :type controller: Controller from 'controller.py'
        """
        if not controller.current_moving_vertex:
            return False

        sdl2.sdlgfx.filledCircleRGBA(
                self.renderer,
                int(controller.current_moving_vertex[0]
                    * self.camera_scale - self.camera_x),
                int(controller.current_moving_vertex[1]
                    * self.camera_scale - self.camera_y),
                int(3.0 * self.camera_scale), 255, 0, 0, 255)
        return True

    def render_line_placement(self, line):
        """Renders the line provided in reference to the camera's current
        location and scale.
        :param line: The line to render
        :type line: tuple(tuple(int, int), tuple(int, int), int)
        """
        start = line[0]
        end = line[1]
        thickness = line[2]

        sdl2.sdlgfx.thickLineRGBA(
            self.renderer,
            int(start[0] * self.camera_scale - self.camera_x),
            int(start[1] * self.camera_scale - self.camera_y),
            int(end[0] * self.camera_scale - self.camera_x),
            int(end[1] * self.camera_scale - self.camera_y),
            int(thickness * self.camera_scale),
            0, 0, 0, 255)
        return True

    def render_mouse_selection(self, controller):
        """Renders rectangle created from user pressing and dragging the mouse.
        :type controller: Controller from 'controller.py'
        :param model: The application model
        """
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderDrawRect(
            self.renderer, controller.get_mouse_selection())
        return True

    def render_line(self, line, layer = 0):
        """Renders the line provided with absolute location (as opposed to
        relative to the camera) onto the layer provided.
        :param line: The line to render
        :type line: Line from 'entities.py'
        :param layer: The layer index from the Textures class to render onto
        :type layer: int
        """
        sdl2.SDL_SetRenderTarget(self.renderer, self.textures.get_layer(layer))
        sdl2.sdlgfx.thickLineRGBA(
            self.renderer, int(line.start[0]), int(line.start[1]),
            int(line.end[0]), int(line.end[1]), int(line.thickness),
            line.get_color()[0], line.get_color()[1], line.get_color()[2], 255)
        return True

    def render_window(self, window, layer = 0):
        """Renders the window provided with absolute location onto the layer.
        Renders a solid white rectangle for the background and black borders.
        :param window: The window to render
        :type window: Window from 'entities.py'
        :param layer: The layer index from the Textures class to render onto
        :type layer: int
        """
        sdl2.SDL_SetRenderTarget(self.renderer, self.textures.get_layer(layer))
        
        # Render white background
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderFillRect(self.renderer, sdl2.SDL_Rect(
            window.x, window.y, window.width, window.height))

        # Render black borders, render green borders if selected
        if window.selected:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 34, 139, 34, 255)
        else:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)

        # Top border
        sdl2.SDL_RenderDrawLine(self.renderer, window.x, window.y,
                                window.x + window.width - 1, window.y)

        # Bottom border
        sdl2.SDL_RenderDrawLine(self.renderer, window.x, window.y
                                + window.height - 1,
                                window.x + window.width - 1,
                                window.y + window.height - 1)

        # Left border
        sdl2.SDL_RenderDrawLine(self.renderer, window.x, window.y,
                                window.x, window.y + window.height - 1)

        # Right border
        sdl2.SDL_RenderDrawLine(self.renderer, window.x + window.width - 1,
                                window.y, window.x + window.width - 1,
                                window.y + window.height - 1)
        return True

    def render_door(self, door, layer = 0):
        """Renders the door provided with absolute location onto the layer.
        Renders a solid white rectangle for the background and black borders.
        :param door: The door to render
        :type door: Door from 'entities.py'
        :param layer: The layer index from the Textures class to render onto
        :type layer: int
        """
        sdl2.SDL_SetRenderTarget(self.renderer, self.textures.get_layer(layer))
        
        # Render grey background
        sdl2.SDL_SetRenderDrawColor(self.renderer, 128, 128, 128, 255)
        sdl2.SDL_RenderFillRect(self.renderer, sdl2.SDL_Rect(
            door.x, door.y, door.width, door.height))
        
        # Render black borders, render green borders if selected
        if door.selected:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 34, 139, 34, 255)
        else:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)

        # Top border
        sdl2.SDL_RenderDrawLine(self.renderer, door.x, door.y,
                                door.x + door.width - 1, door.y)

        # Bottom border
        sdl2.SDL_RenderDrawLine(self.renderer, door.x, door.y
                                + door.height - 1,
                                door.x + door.width - 1,
                                door.y + door.height - 1)

        # Left border
        sdl2.SDL_RenderDrawLine(self.renderer, door.x, door.y,
                                door.x, door.y + door.height - 1)

        # Right border
        sdl2.SDL_RenderDrawLine(self.renderer, door.x + door.width - 1,
                                door.y, door.x + door.width - 1,
                                door.y + door.height - 1)
        return True

    def render_square_vertex(self, vertex, layer = 0):
        """Renders the square vertex provided with absolute location onto the
        layer. Renders a solid black rectangle.
        :param vertex: The square vertex to render
        :type vertex: RectangularEntity from 'entities.py'
        :param layer: The layer index from the Textures class to render onto
        :type layer: int
        """
        sdl2.SDL_SetRenderTarget(self.renderer, self.textures.get_layer(layer))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderFillRect(self.renderer, sdl2.SDL_Rect(
            vertex.x, vertex.y, vertex.width, vertex.height))

    def render_loading(self):
        """Renders the loading screen as a task is blocking the renderer."""
        sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(EntityType.LOADING), None,
            sdl2.SDL_Rect(0, 0, self.screen_width, self.screen_height))

    def set_dpi_awareness(self):
        """Sets the applications DPI awareness to per-monitor-aware,
        so that the window scale is absolute (100%).
        """
        awareness = ctypes.c_int()
        error = ctypes.windll.shcore.SetProcessDpiAwareness(2)

    def get_screen_dimensions(self):
        """Returns the screen dimensions as a tuple."""
        return (self.screen_width, self.screen_height)
    
    def init_sdl_subsystems(self):
        """Initializes SDL video and TTF subsystems.
        """
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        sdl2.sdlttf.TTF_Init()

    def determine_window_size(self):
        """Sets the window size to the user's current display resolution.
        """
        display_mode = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetCurrentDisplayMode(0, display_mode)

        self.screen_width = int(display_mode.w)
        self.screen_height = int(display_mode.h)

    def init_window(self):
        """Initializes the SDL window ands sets the minimum window size.
        """
        self.window = sdl2.SDL_CreateWindow(
            b'Floor Sketcher',
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            self.screen_width,
            self.screen_height,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_RESIZABLE
            | sdl2.SDL_WINDOW_ALLOW_HIGHDPI)

        # Set minimum window size to 720p
        sdl2.SDL_SetWindowMinimumSize(self.window, 1280, 720)

    def init_renderer(self):
        """Initializes the SDL renderer and sets the renderer hints.
        """
        self.renderer = sdl2.SDL_CreateRenderer(
            self.window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        sdl2.SDL_RenderSetIntegerScale(self.renderer, sdl2.SDL_FALSE)
        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b'2')

    def init_textures(self):
        """Loads textures from file and sets the layer dimensions.
        """
        self.textures = Textures()
        layer_dimensions = self.textures.load(self.renderer)
        self.layer_width = layer_dimensions[0]
        self.layer_height = layer_dimensions[1]

    def init_fonts(self, free_current = False):
        """Initializes the fonts based on the current screen dimensions.
        :param free_current: Whether to free the memory allocated for the
        current fonts. Necessary if re-initializing the fonts after changing
        the screen size during runtime.
        :type free_current: boolean.
        """
        if free_current:
            self.free_fonts()

        self.tiny_text = sdl2.sdlttf.TTF_OpenFont(
            b'../res/cour.ttf', int(self.screen_height * 0.013))
        self.small_text = sdl2.sdlttf.TTF_OpenFont(
            b'../res/cour.ttf', int(self.screen_height * 0.017))
        self.medium_text = sdl2.sdlttf.TTF_OpenFont(
            b'../res/cour.ttf', int(self.screen_height * 0.019))
        self.large_text = sdl2.sdlttf.TTF_OpenFont(
            b'../res/cour.ttf', int(self.screen_height * 0.021))

    def resize_fonts(self):
        """Re-initializes the fonts."""
        self.init_fonts(True)

    def free_fonts(self):
        """Frees memory allocated by TTF for the fonts.
        """
        sdl2.sdlttf.TTF_CloseFont(self.tiny_text)
        sdl2.sdlttf.TTF_CloseFont(self.small_text)
        sdl2.sdlttf.TTF_CloseFont(self.medium_text)
        sdl2.sdlttf.TTF_CloseFont(self.large_text)

    def exit(self):
        """Exits SDL subsystems, unloads textures, and frees memory allocated
        by SDL for the window and renderer.
        """
        self.textures.unload()
        self.free_fonts()

        sdl2.SDL_DestroyWindow(self.window)
        self.window = None

        sdl2.SDL_DestroyRenderer(self.renderer)
        self.renderer = None

        sdl2.sdlttf.TTF_Quit()
        sdl2.SDL_Quit()

FontSize = Enum('Font Size', 'SMALL MEDIUM LARGE')