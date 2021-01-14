import glob, polling, sdl2, unittest, os.path

from app import App
from entities import Line, RectangularEntity, Door, Window
from entity_types import EntityType
from polling import PollingType
from text import CenterText, MessageStack, FPSDisplayer
from tools import ExportCommand

class PollingTests(unittest.TestCase):
    """Tests for classes in the polling.py module."""

    def test_erasing(self):
        """Ensure the erasing poll event handler clears the selected entities.
        """
        app = App()
        line = app.model.add_line(EntityType.EXTERIOR_WALL, (0, 0), (0, 0))

        app.controller.selected_entities.add(line)
        app.controller.polling = PollingType.ERASING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(len(app.model.lines), 0)

    def test_drawing(self):
        """Ensure the drawing poll event handler begins two point placement
        for a regular line.
        """
        app = App()
        app.controller.polling = PollingType.DRAWING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)
        self.assertEqual(app.controller.placement_type, EntityType.REGULAR_LINE)

    def test_measuring(self):
        """Ensure the measuring poll event handler begins two point placement.
        """
        app = App()
        app.controller.polling = PollingType.MEASURING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)
        self.assertEqual(app.controller.placement_type, EntityType.NONE)

    def test_adding_text(self):
        """Ensure the adding text poll event handler begins two point placement.
        """
        app = App()
        app.controller.text = 'text'
        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_RETURN] = 1

        handler = polling.AddingText()
        handler.handle(app.controller, app.model, keystate, None, (0, 0), [])
        self.assertEqual(len(app.model.user_text), 1)
        
        for text in app.model.user_text:
            self.assertEqual(text.text, 'text')

    def test_display_grid(self):
        """Ensure the display grid poll event handler toggles the display
        grid attribute of the controller.
        """
        app = App()
        app.controller.polling = PollingType.DISPLAY_GRID
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.display_grid)
        self.assertTrue(app.model.update_needed)

    def test_export_command(self):
        """Ensure the writing inventory poll event handler creates a txt file.
        """

        return # temporarily disabled
        app = App()
        app.controller.polling = PollingType.INVENTORY
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(os.path.isfile('list.txt'))

    def test_exit(self):
        """Ensure the exit poll event handler returns False (signaling to stop
        the execution of the application loop.
        """
        app = App()
        app.controller.polling = PollingType.EXITING
        self.assertFalse(
            app.controller.handle_input(app.model, (1920, 1080), []))

    def test_draw_exterior_wall(self):
        """Ensure the draw exterior wall poll event handler begins two point
        placement for a exterior wall.
        """
        app = App()
        app.controller.polling = PollingType.DRAW_EXTERIOR_WALL
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)
        self.assertEqual(app.controller.placement_type,
                         EntityType.EXTERIOR_WALL)

    def test_draw_interior_wall(self):
        """Ensure the draw interior wall poll event handler begins two point
        placement for a interior wall.
        """
        app = App()
        app.controller.polling = PollingType.DRAW_INTERIOR_WALL
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_two_points)
        self.assertEqual(app.controller.placement_type,
                         EntityType.INTERIOR_WALL)

    def test_draw_window(self):
        """Ensure the draw window poll event handler begins one point
        placement for a window.
        """
        app = App()
        app.controller.polling = PollingType.DRAW_WINDOW
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_one_point)
        self.assertEqual(app.controller.placement_type,
                         EntityType.WINDOW)

    def test_draw_door(self):
        """Ensure the draw door poll event handler begins one point
        placement for a door.
        """
        app = App()
        app.controller.polling = PollingType.DRAW_DOOR
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.place_one_point)
        self.assertEqual(app.controller.placement_type,
                         EntityType.DOOR)

    def test_undo_for_add(self):
        """Ensure the undo poll event handler removes the added line.
        """
        app = App()

        app.controller.handlers[PollingType.UNDOING].last_undo = -5000

        app.model.add_line(EntityType.EXTERIOR_WALL)
        self.assertEqual(len(app.model.lines), 1)

        app.controller.polling = PollingType.UNDOING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(len(app.model.lines), 0)

    def test_redo_for_add(self):
        """Ensure the redo poll event handler adds the removed line.
        """
        app = App()
        
        line = Line()
        app.model.undos.append(polling.AddAction(line))
        app.model.lines.add(line)

        app.controller.handlers[PollingType.REDOING].last_redo = -5000
        app.controller.polling = PollingType.REDOING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(len(app.model.lines), 1)
        self.assertEqual(len(app.model.actions), 1)

    def test_undo_for_delete(self):
        """Ensure the undo poll event handler readds the removed line.
        """
        app = App()

        app.controller.handlers[PollingType.UNDOING].last_undo = -5000

        line = app.model.add_line(EntityType.EXTERIOR_WALL)
        self.assertEqual(len(app.model.lines), 1)

        app.model.remove_entity(line)
        self.assertEqual(len(app.model.lines), 0)

        app.controller.polling = PollingType.UNDOING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(len(app.model.lines), 1)

    def test_redo_for_delete(self):
        """Ensure the redo poll event handler removes the re-added line.
        """
        app = App()
        
        line = Line()
        app.model.undos.append(polling.DeleteAction(line))
        app.model.lines.add(line)

        app.controller.handlers[PollingType.REDOING].last_redo = -5000
        app.controller.polling = PollingType.REDOING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(len(app.model.lines), 0)

    def test_hint_message_for_zoom(self):
        """Ensure that the zoom poll event handler displays the hint message.
        """
        app = App()
        
        app.controller.polling = PollingType.ZOOMING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(app.controller.center_text.text[
            CenterText.TOP_CENTER_TEXT].text, 'Scroll mouse wheel'\
               + ' or use +/- on the numpad to zoom the camera.')

    def test_saving(self):
        """Ensure that the saving poll event handler creates a save filename
        with the expected name: save{}.pkl where {} is the number of .pkl files
        existing in the directory + 1
        """
        app = App()
        
        app.controller.handlers[PollingType.SAVING].last_save = -5000
        app.controller.polling = PollingType.SAVING
        app.controller.handle_input(app.model, (1920, 1080), [])

        num_pkl_files = 0
        for file in glob.glob('*.pkl'):
            num_pkl_files += 1
        filename = 'save{}.pkl'.format(num_pkl_files)
        self.assertTrue(os.path.isfile(filename))

    def test_loading(self):
        """Ensure that the loading poll event handler loads the test.pkl
        model entities.
        """
        app = App()
        
        app.controller.polling = PollingType.LOADING
        app.controller.load_filename = 'test.pkl'
        app.controller.handle_input(app.model, (1920, 1080), [])
        
        self.assertEqual(len(app.model.lines), 4)
        self.assertEqual(len(app.model.windows), 2)
        self.assertEqual(len(app.model.doors), 1)

    def test_setting_layer(self):
        """Ensure that the set layer poll event handler sets the layer of the
        controller to the corresponding layer.
        """
        app = App()

        app.controller.polling = PollingType.LAYER_2
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(app.controller.current_layer, 2)

    def test_toggling_layers_panel(self):
        """Ensure the layers poll event handler toggles between not displaying
        and displaying the layers panel.
        """
        app = App()

        app.controller.layers_panel.visible = False
        app.controller.polling = PollingType.LAYERS
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.layers_panel.visible)

    def test_settings(self):
        """Ensure the settings poll event handler toggles between not displaying
        and displaying the settings panel.
        """
        app = App()

        # Not currently implemented
        return
        
        app.controller.polling = PollingType.SETTINGS
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertTrue(app.controller.settings_panel.visible)

    def test_toggling_between_graphics_settings(self):
        """Ensure the rasterize and vectorize graphics poll event handlers
        toggle between not rasterized and vectorized graphics.
        """
        # Not Implemented...

    def test_moving_hint_text(self):
        """Ensure the moving poll event handler displayers the hint text.
        """
        app = App()
        app.controller.polling = PollingType.MOVING
        app.controller.handle_input(app.model, (1920, 1080), [])
        self.assertEqual(app.controller.center_text.text[
            CenterText.TOP_CENTER_TEXT].text,
            'Select an entity and click on a new vertex location.'\
                + ' Toggle between vertices with TAB.')

    def test_toggling_vertex_when_moving(self):
        """Ensure the moving poll event handler toggles whether to use the start
        vertex when the user presses the TAB key.
        """
        app = App()

        entities = set()
        line = Line((0, 0), (10, 10))
        entities.add(line)

        app.controller.selected_entities = entities
        app.controller.last_selection = -500

        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_TAB] = 1
        event = sdl2.SDL_Event()

        app.controller.handlers[PollingType.MOVING].handle(
            app.controller, app.model, keystate, event, (1920, 1080), [])
        self.assertFalse(app.controller.use_start_vertex)

        keystate = sdl2.SDL_GetKeyboardState(None)
        keystate[sdl2.SDL_SCANCODE_TAB] = 1
        app.controller.handlers[PollingType.MOVING].handle(
            app.controller, app.model, keystate, event, (1920, 1080), [])
        self.assertTrue(app.controller.use_start_vertex)

    def test_moving_entity(self):
        """Ensure the moving poll event handler adds a move action to the model
        when the user has an entity selected and presses on a location.
        """
        app = App()

        entities = set()
        line = Line((0, 0), (-10, -10))
        entities.add(line)

        app.controller.selected_entities = entities
        app.controller.last_selection = -500
        app.controller.item_to_move = line

        keystate = sdl2.SDL_GetKeyboardState(None)
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_MOUSEBUTTONDOWN

        app.controller.handlers[PollingType.MOVING].handle(
            app.controller, app.model, keystate, event, (1920, 1080), [])
        
        # Ensure line's previous state is the one stored in the move action
        for action in app.model.actions:
            break
        self.assertEqual(action.previous.start, line.start)
        self.assertEqual(action.previous.end, line.end)

        self.assertTrue(app.model.update_needed)
        self.assertEqual(app.controller.polling, PollingType.SELECTING)

    def test_exporting(self):
        """Ensure the exporting poll event handler adds an export command
        to the app commands.
        """
        app = App()
        app.controller.polling = PollingType.EXPORTING
        app.controller.handle_input(app.model, (1920, 1080), app.commands)
        self.assertEqual(len(app.commands), 1)
        self.assertTrue(isinstance(app.commands[0], ExportCommand))
        self.assertTrue(app.controller.loading)

if __name__ == '__main__':
    unittest.main()
