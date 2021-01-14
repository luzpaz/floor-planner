import sdl2

from entity_types import EntityType

class Textures:
    """Contains and manages the application's textures and layers.
    """

    # Number of layers the user can choose from
    NUM_LAYERS = 4

    def get(self, texture):
        """Returns the SDL texture designated by the texture enum.
        :param texture: The texture enum from 'entity_types.py'
        :type texture: int (value of EntityType)
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

        # Create textures from png files in textures directory
        self.textures[EntityType.BUTTON_PANEL.value] = self.create(
            renderer, b'../res/textures/button_panel.png')
        
        self.textures[EntityType.BUTTON_BACKGROUND.value] = self.create(
            renderer, b'../res/textures/button.png')
        self.textures[EntityType.SELECTED_BUTTON.value] = self.create(
            renderer, b'../res/textures/button_alternate.png')

        self.textures[EntityType.SELECT_BUTTON.value] = self.create(
            renderer, b'../res/textures/select_button.png')
        self.textures[EntityType.ERASE_BUTTON.value] = self.create(
            renderer, b'../res/textures/erase_button.png')
        self.textures[EntityType.DRAW_BUTTON.value] = self.create(
            renderer, b'../res/textures/draw_button.png')
        self.textures[EntityType.MOVE_BUTTON.value] = self.create(
            renderer, b'../res/textures/move_button.png')
        self.textures[EntityType.MEASURE_BUTTON.value] = self.create(
            renderer, b'../res/textures/measure_button.png')
        self.textures[EntityType.ADD_TEXT_BUTTON.value] = self.create(
            renderer, b'../res/textures/add_text_button.png')
        self.textures[EntityType.PAN_BUTTON.value] = self.create(
            renderer, b'../res/textures/pan_button.png')
        self.textures[EntityType.ZOOM_BUTTON.value] = self.create(
            renderer, b'../res/textures/zoom_button.png')
        self.textures[EntityType.GRID_BUTTON.value] = self.create(
            renderer, b'../res/textures/grid_button.png')
        self.textures[EntityType.LAYERS_BUTTON.value] = self.create(
            renderer, b'../res/textures/layers_button.png')
        self.textures[EntityType.SETTINGS_BUTTON.value] = self.create(
            renderer, b'../res/textures/settings_button.png')
        self.textures[EntityType.UNDO_BUTTON.value] = self.create(
            renderer, b'../res/textures/undo_button.png')
        self.textures[EntityType.REDO_BUTTON.value] = self.create(
            renderer, b'../res/textures/redo_button.png')
        self.textures[EntityType.SAVE_BUTTON.value] = self.create(
            renderer, b'../res/textures/save_button.png')
        self.textures[EntityType.LOAD_BUTTON.value] = self.create(
            renderer, b'../res/textures/load_button.png')
        self.textures[EntityType.INVENTORY_BUTTON.value] = self.create(
            renderer, b'../res/textures/inventory_button.png')
        self.textures[EntityType.EXPORT_BUTTON.value] = self.create(
            renderer, b'../res/textures/export_button.png')
        self.textures[EntityType.EXIT_BUTTON.value] = self.create(
            renderer, b'../res/textures/exit_button.png')

        self.textures[EntityType.EXTERIOR_WALL_BUTTON.value] = self.create(
            renderer, b'../res/textures/exterior_wall_button.png')
        self.textures[EntityType.INTERIOR_WALL_BUTTON.value] = self.create(
            renderer, b'../res/textures/interior_wall_button.png')
        self.textures[EntityType.WINDOW_BUTTON.value] = self.create(
            renderer, b'../res/textures/window_button.png')
        self.textures[EntityType.DOOR_BUTTON.value] = self.create(
            renderer, b'../res/textures/door_button.png')

        self.textures[EntityType.LAYER.value] = self.create(
            renderer, b'../res/textures/layer.png')

        self.textures[EntityType.RASTERIZE.value] = self.create(
            renderer, b'../res/textures/rasterize.png')
        self.textures[EntityType.VECTORIZE.value] = self.create(
            renderer, b'../res/textures/vectorize.png')

        self.textures[EntityType.LOADING.value] = self.create(
            renderer, b'../res/textures/loading.png')

        # Get maximum texture size
        info = sdl2.SDL_RendererInfo()
        sdl2.SDL_GetRendererInfo(renderer, info)
        layer_width = int(info.max_texture_width * 0.25)
        layer_height = int(info.max_texture_height * 0.25)

        # Create layers
        for layer in range(Textures.NUM_LAYERS):
            self.layers[layer] = sdl2.SDL_CreateTexture(renderer,
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