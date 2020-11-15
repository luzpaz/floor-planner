import ctypes
import sdl2
import sdl2.sdlgfx
import sdl2.sdlimage
import sdl2.sdlttf

from ctypes import c_int, pointer
from entity_types import EntityType
from enum import Enum

class View:
    """Class responsible for rendering entities from the model and the user
    interface onto the screen.
    """

    def __init__(self):
        """Initializes SDL subsystems, SDL components, textures, and fonts
        necessary for renderering.
        """

        # Initialize SDL subsystems
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        sdl2.sdlttf.TTF_Init()

        # Temporarily hard code starting screen dimensions
        self.screen_width = 1920
        self.screen_height = 1080

        # Initialize SDL window and renderer
        self.window = sdl2.SDL_CreateWindow(
            b'House Planner',
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            self.screen_width,
            self.screen_height,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_RESIZABLE
            | sdl2.SDL_WINDOW_ALLOW_HIGHDPI)

        # Set minimum window size to 720p
        sdl2.SDL_SetWindowMinimumSize(self.window, 1280, 720)

        self.renderer = sdl2.SDL_CreateRenderer(
            self.window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        sdl2.SDL_RenderSetIntegerScale(self.renderer, sdl2.SDL_FALSE)
        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b'2')

        self.set_dpi_awareness()

        # Initialize textures
        self.textures = Textures()
        layer_dimensions = self.textures.load(self.renderer)
        self.layer_width = layer_dimensions[0]
        self.layer_height = layer_dimensions[1]

        # Initialize fonts
        self.small_text = sdl2.sdlttf.TTF_OpenFont(b'cour.ttf', 18)
        self.medium_text = sdl2.sdlttf.TTF_OpenFont(b'cour.ttf', 20)
        self.large_text = sdl2.sdlttf.TTF_OpenFont(b'cour.ttf', 24)

    def update(self, model, controller):
        """Updates the application window with entities from the model
        and the user interface, in reference to the camera position and scale.
        """

        try:
            # Clear contents on window
            sdl2.SDL_SetRenderDrawColor(self.renderer, 128, 128, 128, 255)
            sdl2.SDL_RenderClear(self.renderer)

            # Store camera attributes as class values for easier access
            self.camera_x = controller.camera.x
            self.camera_y = controller.camera.y
            self.camera_scale = controller.camera.scale

            # Only update the layers if new entities were added or removed
            if model.update_needed:
                # Update screen size
                width = pointer(c_int(0))
                height = pointer(c_int(0))
                sdl2.SDL_GetWindowSize(self.window, width, height)
                self.screen_width = width.contents.value
                self.screen_height = height.contents.value

                self.update_layer(model, controller)
                model.update_needed = False

            # Render layers currently set as visible by the user
            self.render_layer(controller.current_layer)

            # Render UI panels
            self.render_ui_panels(controller)

            # Render text from the UI and other indicators
            self.render_ui_text(controller)
            self.render_two_point_placement(controller, model)
            self.render_mouse_selection(controller)

            if controller.loading:
                self.render_loading()

            # Update window with new contents
            sdl2.SDL_RenderPresent(self.renderer)
        except:
            return

    def update_layer(self, model, controller):
        """Renders entities from model onto their corresponding layer.
        This optimizes rendering as rendering the layer once renders all
        entities simultaneously, instead of rendering each entity every frame.
        """
        sdl2.SDL_SetRenderTarget(self.renderer, self.textures.get_layer(
                                 controller.current_layer))
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderClear(self.renderer)

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
            self.render_line(line, controller.current_layer)
            entities_rendered += 1

        # Render user text
        for text in model.user_text:
            self.render_absolute_text(text)
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

    def render_absolute_text(self, text):
        """Renders text at its absolute location in black with small font.
        :param text: The text to render
        :type text: UserText from 'entities.py'
        """
        if not text or not text.text:
            return None

        font = self.small_text

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
            self.render_panel(panel)

            for button in panel.buttons:
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
            self.renderer, self.textures.get(EntityType.BUTTON_BACKGROUND),
            None, location)
        else:
            sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(EntityType.BUTTON_BACKGROUND),
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
        around vertices that it may snap to or axises it may align with.
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
            sdl2.sdlgfx.circleRGBA(
                self.renderer,
                int(nearest_vertex[0] * self.camera_scale - self.camera_x),
                int(nearest_vertex[1] * self.camera_scale - self.camera_y),
                int(10.0 * self.camera_scale), 0, 0, 0, 255)

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

    def render_loading(self):
        """Renders the loading screen as a task is blocking the renderer."""
        sdl2.SDL_RenderCopy(
            self.renderer, self.textures.get(EntityType.LOADING), None,
            sdl2.SDL_Rect(0, 0, self.screen_width, self.screen_height))

    def set_dpi_awareness(self):
        """Sets the applications DPI awareness to per-monitor-aware,
        so that the window scale is always absolute (100%).
        """
        awareness = ctypes.c_int()
        error = ctypes.windll.shcore.SetProcessDpiAwareness(2)

    def get_screen_dimensions(self):
        """Returns the screen dimensions as a tuple."""
        return (self.screen_width, self.screen_height)

    def exit(self):
        """Exits SDL subsystems, unloads textures, and frees memory allocated
        by SDL for the window and renderer.
        """
        self.textures.unload()

        sdl2.SDL_DestroyWindow(self.window)
        self.window = None

        sdl2.SDL_DestroyRenderer(self.renderer)
        self.renderer = None

        sdl2.sdlttf.TTF_Quit()
        sdl2.SDL_Quit()

class Textures:
    """Class that contains and manages the application's textures and layers.
    """

    def get(self, texture):
        """Returns the SDL texture designated by the texture enum.
        :param texture: The texture enum from 'entity_types.py'
        :type texture: int
        """
        return self.textures.get(texture)

    def get_layer(self, layer):
        """Returns the SDL texture for the layer designated by the layer index.
        :param layer: The layer index from the Textures class to return
        :type layer: int
        """
        return self.layers.get(layer)

    def create(self, renderer, filename):
        """Creates and returns a SDL texture loaded from the png file.
        :param renderer: The SDL renderer used to create the texture
        :type renderer: SDL_Renderer
        :param filename: The relative location of the png file
        :type filename: str
        """
        return sdl2.sdlimage.IMG_LoadTexture(renderer, filename)

    def load(self, renderer):
        """Creates and stores textures from file and initializes layers.
        Returns the dimensions of the layer textures.
        :param renderer: The SDL renderer used to create the textures
        :type renderer: SDL_Renderer
        """
        self.textures = {}
        self.layers = {}

        # Create textures...
        self.textures[EntityType.BUTTON_PANEL] = self.create(
            renderer, b'textures/button_panel.png')
        
        self.textures[EntityType.BUTTON_BACKGROUND] = self.create(
            renderer, b'textures/button.png')
        self.textures[EntityType.SELECTED_BUTTON] = self.create(
            renderer, b'textures/button_alternate.png')

        self.textures[EntityType.SELECT_BUTTON] = self.create(
            renderer, b'textures/select_button.png')
        self.textures[EntityType.ERASE_BUTTON] = self.create(
            renderer, b'textures/erase_button.png')
        self.textures[EntityType.DRAW_BUTTON] = self.create(
            renderer, b'textures/draw_button.png')
        self.textures[EntityType.MOVE_BUTTON] = self.create(
            renderer, b'textures/move_button.png')
        self.textures[EntityType.MEASURE_BUTTON] = self.create(
            renderer, b'textures/measure_button.png')
        self.textures[EntityType.ADD_TEXT_BUTTON] = self.create(
            renderer, b'textures/add_text_button.png')
        self.textures[EntityType.PAN_BUTTON] = self.create(
            renderer, b'textures/pan_button.png')
        self.textures[EntityType.ZOOM_BUTTON] = self.create(
            renderer, b'textures/zoom_button.png')
        self.textures[EntityType.LAYERS_BUTTON] = self.create(
            renderer, b'textures/layers_button.png')
        self.textures[EntityType.SETTINGS_BUTTON] = self.create(
            renderer, b'textures/settings_button.png')
        self.textures[EntityType.UNDO_BUTTON] = self.create(
            renderer, b'textures/undo_button.png')
        self.textures[EntityType.REDO_BUTTON] = self.create(
            renderer, b'textures/redo_button.png')
        self.textures[EntityType.SAVE_BUTTON] = self.create(
            renderer, b'textures/save_button.png')
        self.textures[EntityType.EXPORT_BUTTON] = self.create(
            renderer, b'textures/export_button.png')

        self.textures[EntityType.LOADING] = self.create(
            renderer, b'textures/loading.png')

        # Get maximum texture size
        info = sdl2.SDL_RendererInfo()
        sdl2.SDL_GetRendererInfo(renderer, info)
        layer_width = int(info.max_texture_width * 0.25)
        layer_height = int(info.max_texture_height * 0.25)

        # Create layers
        self.layers[0] = sdl2.SDL_CreateTexture(renderer,
                                       sdl2.SDL_PIXELFORMAT_RGBA8888,
                                       sdl2.SDL_TEXTUREACCESS_TARGET,
                                       layer_width, layer_height)
        sdl2.SDL_SetRenderTarget(renderer, self.layers[0])
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_SetRenderTarget(renderer, None)

        return (layer_width, layer_height)

    def unload(self):
        """Frees memory allocated by SDL for each texture and layer.
        """
        for texture in self.textures:
            sdl2.SDL_DestroyTexture(self.textures[texture])
        for layer in self.layers:
            sdl2.SDL_DestroyTexture(self.layers[layer])
        self.textures.clear()
        self.layers.clear()

FontSize = Enum('Font Size', 'SMALL MEDIUM LARGE')