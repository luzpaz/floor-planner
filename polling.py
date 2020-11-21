import glob, pickle, os, sdl2, sdl2.ext

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
        controller.placement_type = EntityType.REGULAR_LINE
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
        controller.placement_type = EntityType.NONE
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
    """The polling event handler for zooming the camera.
    Currently does not add any additional functionality that the user cannot
    do without the poll event, but displays the hint message in case the user
    does not know the hotkeys necessary for zooming the camera.
    Future functionality: zoom on an area by mouse drag selection."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Displays the hint text for camera zooming.
        """
        controller.center_text.set_top_text(
            'Scroll mouse wheel or use +/- on the numpad to zoom the camera.')

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
    """The polling event handler for undoing the last action."""

    # Minimum time required between undos (ms)
    INTERVAL = 100

    def __init__(self):
        self.last_undo = sdl2.SDL_GetTicks()

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Undos the last action and moves it to the undo-ed actions.
        """
        controller.reset()
        
        # Only undo every interval so that user holding Ctrl+Z does
        # not rapidly undo many actions
        if Undoing.INTERVAL > sdl2.SDL_GetTicks() - self.last_undo:
            return

        # Nothing to undo
        if len(model.actions) == 0:
            return

        action = model.actions.pop()
        action.undo(controller, model)
        model.undos.append(action)
        self.last_undo = sdl2.SDL_GetTicks()

class Redoing:
    """The polling event handler for redoing the last undo."""
    
    # Minimum time required between redos (ms)
    INTERVAL = 100

    def __init__(self):
        self.last_redo = sdl2.SDL_GetTicks()

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Redos the last action and moves it to back to the actions.
        """
        controller.reset()
        
        # Only redo every interval so that user holding Ctrl+Y does
        # not rapidly redo many actions
        if Redoing.INTERVAL > sdl2.SDL_GetTicks() - self.last_redo:
            return

        # Nothing to redo
        if len(model.undos) == 0:
            return

        action = model.undos.pop()
        action.redo(controller, model)
        model.actions.append(action)
        self.last_redo = sdl2.SDL_GetTicks()
        
class Saving:
    """The polling event handler for saving the model entities to file."""

    # Minimum time required between saves (ms)
    INTERVAL = 1000

    def __init__(self):
        self.last_save = sdl2.SDL_GetTicks()

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Saves the model entities to a file."""
        
        # Only save every interval so that user holding Ctrl+S does
        # not rapidly save many times
        if Saving.INTERVAL > sdl2.SDL_GetTicks() - self.last_save:
            return

        # Search directory for number of .pkl files to determine filename
        num_pkl_files = 0
        for file in glob.glob('*.pkl'):
            num_pkl_files += 1
        filename = 'save{}.pkl'.format(num_pkl_files + 1)

        with open(filename, 'wb') as file:
            pickle.dump(model.lines, file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(model.windows, file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(model.doors, file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(model.user_text, file, pickle.HIGHEST_PROTOCOL)

        controller.message_stack.insert(['Saved drawing: '\
            + str(os.getcwd()) + '\\' + filename])
        self.last_save = sdl2.SDL_GetTicks()
        controller.reset()
        
class WritingInventory:
    """The polling event handler for exporting the inventory to a txt tile."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Exports inventory to a txt file."""
        controller.message_stack.insert(['Created list of entities: '\
            + str(os.getcwd()) + '\list.txt'])
        with open('list.txt', 'w') as file:
            file.write(model.get_inventory())
        controller.reset()
        
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
        controller.placement_type = EntityType.EXTERIOR_WALL
        controller.line_thickness = Line.EXTERIOR_WALL
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING
        
class DrawInteriorWall:
    """The polling event handler for drawing a interior wall."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins two-point placement for a interior wall."""
        controller.reset()
        controller.placement_type = EntityType.INTERIOR_WALL
        controller.line_thickness = Line.INTERIOR_WALL
        controller.place_two_points = True
        controller.polling = PollingType.SELECTING
        
class DrawWindow:
    """The polling event handler for drawing a window."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins one-point placement for a window."""
        controller.reset()
        controller.placement_type = EntityType.WINDOW
        controller.place_one_point = True
        controller.polling = PollingType.SELECTING
        
class DrawDoor:
    """The polling event handler for drawing a door."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Begins one-point placement for a door."""
        controller.reset()
        controller.placement_type = EntityType.DOOR
        controller.place_one_point = True
        controller.polling = PollingType.SELECTING
        
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

class AddAction:
    """The action container for when a user adds an entity."""
    
    def __init__(self, entity = None):
        """Initializes the add action.
        :param entity: The entity the user added
        :type entity: Any entity class from 'entities.py'
        """
        self.entity = entity

    def undo(self, controller, model):
        """Defines what is needed to undo this action:
        Removes the added entity from the model."""
        model.remove_entity(self.entity, False)

    def redo(self, controller, model):
        """Defines what is needed to redo this action:
        Adds the removed entity into the model."""
        model.add_entity(self.entity)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.entity.__repr__()

class DeleteAction:
    """The action container for when a user deletes an entity."""
    
    def __init__(self, entity = None):
        """Initializes the delete action.
        :param entity: The entity the user deleteed
        :type entity: Any entity class from 'entities.py'
        """
        self.entity = entity

    def undo(self, controller, model):
        """Defines what is needed to undo this action:
        Adds the deleted entity into the model."""
        model.add_entity(self.entity)

    def redo(self, controller, model):
        """Defines what is needed to redo this action:
        Removes the added entity from the model."""
        model.remove_entity(self.entity, False)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.entity.__repr__()

class MoveAction:
    pass

class ActionType:
    ADD = 0
    DELETE = 1
    MOVE = 2