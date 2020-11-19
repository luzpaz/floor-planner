import os
import sdl2
import sdl2.ext

from entities import Line
from entity_types import EntityType
from tools import ExportCommand

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
        """Begins two-point placement for a regular line."""
        controller.reset()
        controller.line_type = EntityType.REGULAR_LINE
        controller.line_thickness = Line.REGULAR_LINE
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING

class Moving:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()
        
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
    """The polling event handler for adding user text."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Adds user text to the mouse location after the user presses ENTER."""

        controller.center_text.set_top_text(
            'Move cursor to text location, type text, and press ENTER.')
        controller.center_text.set_bottom_text(controller.text)

        if keystate[sdl2.SDL_SCANCODE_RETURN]:
            mouse = controller.get_adjusted_mouse(model)
            model.add_user_text(controller.text, (mouse[0], mouse[1]))
            controller.reset()
     
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
        controller.message_stack.insert(['Not implemented'])
        controller.reset()

class DisplayGrid:
    """The polling event handler for displaying the drawing grid."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Toggles whether to display the drawing grid lines.
        """
        controller.display_grid = not controller.display_grid
        model.update_needed = True
        controller.reset()

class Layers:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()

class Settings:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()

class Undoing:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()

class Redoing:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()
        
class Saving:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()
        
class WritingInventory:
    """The polling event handler for exporting the inventory to a txt tile."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Exports inventory to a txt file."""
        controller.loading = True
        controller.message_stack.insert(['Created list of entities: '\
            + str(os.getcwd()) + '\list.txt'])
        with open('list.txt', 'w') as file:
            file.write(model.get_inventory())
        controller.reset()
        controller.loading = False
        
class Exporting:
    """The polling event handler for exporting the drawing to png."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Adds the export command to be executed by the application."""
        commands.append(ExportCommand())
        controller.reset()
        controller.message_stack.insert(['Exported drawing: '\
            + str(os.getcwd()) + '\export.png'])
        controller.loading = True
        
class DrawExteriorWall:
    """The polling event handler for drawing a exterior wall."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins two-point placement for a exterior wall."""
        controller.reset()
        controller.line_type = EntityType.EXTERIOR_WALL
        controller.line_thickness = Line.EXTERIOR_WALL
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING
        
class DrawInteriorWall:
    """The polling event handler for drawing a interior wall."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins two-point placement for a interior wall."""
        controller.reset()
        controller.line_type = EntityType.INTERIOR_WALL
        controller.line_thickness = Line.INTERIOR_WALL
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING
        
class DrawWindow:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()
        
class DrawDoor:
    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        controller.message_stack.insert(['Not implemented'])
        controller.reset()
        
class PollingType:
    """Enum for indexing handlers list in the controller."""
    SELECTING = 0
    ERASING = 1
    DRAWING = 2
    MOVING = 3
    MEASURING = 4
    ADDING_TEXT = 5
    PANNING = 6
    ZOOMING = 7
    DISPLAY_GRID = 8
    LAYERS = 9
    SETTINGS = 10
    UNDOING = 11
    REDOING = 12
    SAVING = 13
    EXPORTING = 14
    WRITING_INVENTORY = 15
    EXITING = 16
    DRAW_EXTERIOR_WALL = 17
    DRAW_INTERIOR_WALL = 18
    DRAW_WINDOW = 19
    DRAW_DOOR = 20

    NUM_TYPES = DRAW_DOOR + 1