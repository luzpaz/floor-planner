import sdl2.ext

from entities import Line
from entity_types import EntityType

class Erasing:
    """The polling event handler for erasing entities."""
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Allows the user to erase entities simply by clicking them.
        User does not have to select entities then press the DELETE key.
        """
        for entity in controller.selected_entities:
            model.remove_entity(entity)
        controller.selected_entities.clear()

class Drawing:
    """The polling event handler for drawing a regular line."""
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins two-point placement for a regular line.
        """
        controller.reset()
        controller.line_type = EntityType.REGULAR_LINE
        controller.line_thickness = Line.REGULAR_LINE
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING

class Moving:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Moving")
        
class Measuring:
    """The polling event handler for measuring a line."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins two-point placement for a measurement."""
        controller.reset()
        controller.line_type = EntityType.NONE
        controller.line_thickness = Line.REGULAR_LINE
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING
        

class AddingText:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Adding Text")
     
class Panning:
    """The polling event handler for panning the camera."""
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Allows user to pan the camera simply by pressing and dragging
        the mouse. User does not have to hold the SHIFT key to pan.
        """
        controller.handle_camera_pan(event)
        
class Zooming:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Zooming")
        

class Layers:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Layers")
        

class Settings:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Settings")
        

class Undoing:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Undoing")
        

class Redoing:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Redoing")
        

class Saving:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Undoing")
        

class Exporting:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        print("Exporting")
        

class PollingType:
    """Enum for indexing handlers list in the controller."""
    NUM_TYPES = 14

    SELECTING = 0
    ERASING = 1
    DRAWING = 2
    MOVING = 3
    MEASURING = 4
    ADDING_TEXT = 5
    PANNING = 6
    ZOOMING = 7
    LAYERS = 8
    SETTINGS = 9
    UNDOING = 10
    REDOING = 11
    SAVING = 12
    EXPORTING = 13