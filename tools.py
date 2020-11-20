import sdl2, sdl2.sdlimage

from ctypes import c_int, pointer

class Tools:
    """The class offering static utilities needed across various classes."""

    def convert_to_unit_system(value, unit_system = 'ft'):
        """Returns the value in the unit system specified.
        Currently only supports feet and inches.
        :param value: The pixel value, default as inches
        :type value: double
        :param unit_system: The target unit system
        :type unit_system: str
        """
        value = abs(value)

        if unit_system == 'ft':
            feet = value // 12
            inches = value - feet * 12
            return str(int(feet)) + " ft " + str(int(inches)) + " in"
        return ''

class Command:
    """The base class for a command to execute using the application."""
    def execute(self, app):
        pass

class ExportCommand(Command):
    """The command that exports the drawing to a png file."""
    def execute(self, app):
        export = Exporter(app.view.renderer, app.view.textures.layers[0])

class Exporter:
    """The class responsible for exporting the drawing into a png file."""

    # Minimum interval (ms) between exports
    EXPORT_INTERVAL = 5000

    # Last time an export was completed
    last_export = -EXPORT_INTERVAL

    def __init__(self, renderer, texture):
        """Exports the texture into a png file.
        :param renderer: The SDL renderer
        :type renderer: SDL_Renderer
        :param texture: The SDL texture to export
        :type texture: SDL_Texture
        """

        # Do not perform more than one export in a 5 second period
        if Exporter.EXPORT_INTERVAL > sdl2.SDL_GetTicks()\
            - Exporter.last_export:
            return

        sdl2.SDL_SetRenderTarget(renderer, texture)

        width = pointer(c_int(0))
        height = pointer(c_int(0))
        sdl2.SDL_QueryTexture(texture, None, None, width, height)
        width = width.contents.value
        height = height.contents.value

        surface = sdl2.SDL_CreateRGBSurface(
            0, width, height, 32, 0, 0, 0, 0);

        sdl2.SDL_RenderReadPixels(
            renderer, None, surface.contents.format.contents.format,
            surface.contents.pixels, surface.contents.pitch)

        sdl2.sdlimage.IMG_SavePNG(surface, b'export.png')
        sdl2.SDL_FreeSurface(surface)

        sdl2.SDL_SetRenderTarget(renderer, None)
        last_export = sdl2.SDL_GetTicks()