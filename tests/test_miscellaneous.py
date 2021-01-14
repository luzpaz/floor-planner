import sys, unittest, os.path
sys.path.append("..\src")

from app import App
from controller import Controller
from model import Model
from tools import Tools, ExportCommand
from view import View

class ToolsTests(unittest.TestCase):
    """Tests for classes in the tools.py module."""

    def test_base_convert_to_unit_system(self):
        """Ensure converting to ft and inches returns the expected values.
        """
        self.assertEqual(Tools.convert_to_unit_system(12), '1 ft 0 in')
        self.assertEqual(Tools.convert_to_unit_system(15), '1 ft 3 in')
        self.assertEqual(Tools.convert_to_unit_system(50), '4 ft 2 in')
        self.assertEqual(Tools.convert_to_unit_system(-5), '0 ft 5 in')
        self.assertEqual(Tools.convert_to_unit_system(0, ''), '')

    def test_export_command(self):
        """Ensure the export command creates an export.png file, signaling
        that it has successfully exported the texture.
        """
        app = App()
        app.commands.append(ExportCommand())
        app.execute_commands()
        self.assertTrue(os.path.isfile('export.png'))

class AppTests(unittest.TestCase):
    """Tests for the App class (app.py)."""

    def test_initialization(self):
        """Ensure the app constructor initializes the components.
        """
        app = App()
        self.assertIsInstance(app.model, Model)
        self.assertIsInstance(app.controller, Controller)
        self.assertIsInstance(app.view, View)

    def test_loading(self):
        """Ensure app can load entities into the model from a save file.
        """
        app = App('../res/test.pkl')
        self.assertEqual(len(app.model.lines), 4)
        self.assertEqual(len(app.model.windows), 2)
        self.assertEqual(len(app.model.doors), 1)

    def test_loading_failure(self):
        """Ensure app trying to load into a file that does not exist
        adds no entities to the model.
        """
        app = App('.pkl')
        self.assertEqual(len(app.model.lines), 0)
        self.assertEqual(len(app.model.windows), 0)
        self.assertEqual(len(app.model.doors), 0)

    def test_app_loop(self):
        """TO DO: Ensure the app loop runs and exits.
        """
        pass

if __name__ == '__main__':
    unittest.main()