import glob, pickle, os, sdl2, sdl2.ext

from copy import deepcopy
from entities import Line
from entity_types import EntityType
from tools import ExportCommand, Loader

class Erasing:
    """The polling event handler for erasing entities."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Allows the user to erase entities simply by clicking them.
        User does not have to select entities then press the DELETE key.
        """

        # Display hint
        controller.center_text.set_top_text(
            'Select entities to erase.')

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
    """The polling event handler for moving an entity."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Moves the selected entity to the new location specified by the user,
        with reference to the vertex of the entity toggled by the user.
        """

        # Display hint
        controller.center_text.set_top_text(
            'Select an entity and click on a new vertex location.'\
                + ' Toggle between vertices with TAB.')

        # Toggle between vertices of the selected entity
        if keystate[sdl2.SDL_SCANCODE_TAB]:
            controller.use_start_vertex = not controller.use_start_vertex

        # Allow time between mouse clicks so that the user does not accidentally
        # instantly move an entity after selecting it
        if len(controller.selected_entities) > 0\
            and sdl2.SDL_GetTicks() - controller.last_selection > 250:
            controller.using_selection = True

            # Get entity's moving vertex to display
            if controller.item_to_move:
                controller.current_moving_vertex =\
                    controller.item_to_move.get_moving_vertex(
                        controller.use_start_vertex)

            # User selected on new location for entity
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN\
                and controller.item_to_move:

                move_action = MoveAction(controller.item_to_move)

                adjusted_mouse = controller.get_adjusted_mouse(model)

                controller.item_to_move.move(
                    adjusted_mouse[0], adjusted_mouse[1],
                    controller.use_start_vertex)
                controller.moved_entities.add(
                    (controller.item_to_move,
                    (adjusted_mouse[0], adjusted_mouse[1])))
                
                move_action.current = controller.item_to_move
                model.actions.append(move_action)

                model.update_needed = True
                model.update_verticies()
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
            text = model.add_user_text(controller.text, (mouse[0], mouse[1]))
            controller.reset()
            text.layer = controller.current_layer
     
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
    """The polling event handler for toggling the visibility of the layers
    panel on the right side of the screen."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Toggles whether to display the layers panel.
        """
        controller.layers_panel.visible = not controller.layers_panel.visible
        controller.reset()

class Settings:
    """The polling event handler for toggling the visibility of the settings
    panel in the center of the screen."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Toggles whether to display the settings panel.
        """
        controller.center_text.set_top_text(
            'Press ESC to close settings.')
        controller.settings_panel.visible = True

class Undoing:
    """The polling event handler for undoing the last action."""

    # Minimum time required between undos (ms)
    INTERVAL = 150

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
    INTERVAL = 150

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
        """Sets the filename for the current app session based on the number of
        .pkl files there are in the app directory."""

        # Search directory for number of .pkl files to determine filename
        num_pkl_files = 0
        for file in glob.glob('*.pkl'):
            num_pkl_files += 1
        self.filename = 'save{}.pkl'.format(num_pkl_files + 1)

        self.last_save = sdl2.SDL_GetTicks()

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Saves the model entities to a file."""
        
        # Only save every interval so that user holding Ctrl+S does
        # not rapidly save many times
        if Saving.INTERVAL > sdl2.SDL_GetTicks() - self.last_save:
            return

        with open(self.filename, 'wb') as file:
            pickle.dump(model.lines, file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(model.windows, file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(model.doors, file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(model.user_text, file, pickle.HIGHEST_PROTOCOL)

        controller.message_stack.insert(['Saved drawing: '\
            + str(os.getcwd()) + '\\' + self.filename])
        self.last_save = sdl2.SDL_GetTicks()
        controller.reset()

class Loading:
    """The polling event handler for loading the model entities from file."""

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Loads the model entities from the file."""
        
        if not controller.load_filename:
            controller.center_text.set_top_text(
                'Drap and drop .pkl file to the screen to load it.')
            return

        adjusted_filename = str(controller.load_filename)

        # Adjust filename if it comes as bytes (from SDL drag/drop)
        if adjusted_filename[0:2] == "b'":
            adjusted_filename = adjusted_filename[2:-1]

        try:
            loader = Loader(model, adjusted_filename)
            controller.message_stack.insert(('Loaded from save file: '
                                             + adjusted_filename,))
        except:
            controller.message_stack.insert(('Error loading save file: '
                                             + adjusted_filename,))
            model = Model() # reset model

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

class SetLayer:
    """The polling event handler for setting the layer."""

    def __init__(self, layer = 0):
        """Sets the layer for this handler to set to."""
        self.layer = layer

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Sets the current layer of the controller."""
        controller.current_layer = self.layer
        controller.reset()
        model.update_needed = True

class RasterizeGraphics:
    """The polling event handler for changing to rasterized graphics rendering.
    """

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Sets the graphics rendering to rasterized."""
        controller.rasterize_graphics = True
        controller.polling = PollingType.SETTINGS

class VectorizeGraphics:
    """The polling event handler for changing to vectorized graphics rendering.
    """

    def handle(self, controller, model, keystate, event,
               screen_dimensions, commands):
        """Sets the graphics rendering to vectorized."""
        controller.message_stack.insert(('Feature coming soon',))
        controller.polling = PollingType.SETTINGS

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
    LOADING = 14
    EXPORTING = 15
    INVENTORY = 16
    EXITING = 17

    DRAW_EXTERIOR_WALL = 18
    DRAW_INTERIOR_WALL = 19
    DRAW_WINDOW = 20
    DRAW_DOOR = 21

    # TO DO: make layers dynamic
    LAYER_0 = 22
    LAYER_1 = 23
    LAYER_2 = 24
    LAYER_3 = 25

    RASTERIZE = 26
    VECTORIZE = 27

    NUM_TYPES = VECTORIZE + 1

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

    def __str__(self):
        """Returns description."""
        return 'Added ' + str(self.entity)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.entity.__repr__()

class DeleteAction:
    """The action container for when a user deletes an entity."""
    
    def __init__(self, entity = None):
        """Initializes the delete action.
        :param entity: The entity the user deleted
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

    def __str__(self):
        """Returns description."""
        return 'Deleted ' + str(self.entity)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.entity.__repr__()

class MoveAction:
    """The action container for when a user moves an entity."""

    def __init__(self, previous_state = None):
        """Copies the previous state of the entity the user moved.
        :param previous_state: The entity the user *will* move
        :type entity: Any entity class from 'entities.py'"""
        self.previous = deepcopy(previous_state)
        self.current = None

    def undo(self, controller, model):
        """Defines what is needed to undo this action:
        Replaces the current entity with its previous state."""
        model.remove_entity(self.current, False)
        model.add_entity(self.previous)

    def redo(self, controller, model):
        """Defines what is needed to redo this action:
        Replaces the previous entity with its moved state."""
        model.remove_entity(self.previous, False)
        model.add_entity(self.current)

    def __str__(self):
        """Returns description."""
        return 'Moved ' + str(self.current)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.current.__repr__()

class ActionType:
    ADD = 0
    DELETE = 1
    MOVE = 2