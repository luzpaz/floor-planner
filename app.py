import os, sdl2, sys, threading

from model import Model
from controller import Controller
from tools import Loader
from view import View

class App:
    """Houses the MVC components and executes the application loop."""

    def __init__(self, load = ''):
        """Initializes the application MVC components.
        :param load: Saved filename to load from
        :type load: str
        """
        self.model = Model()
        self.view = View()
        self.controller = Controller()

        # Whether the application loop is executing
        self.running = False

        # Commands received from the controller
        self.commands = []

        # Load from saved file if provided
        if load: self.load_from_file(load)

    def run(self):
        """Begins execution of application loop, which handles user input and
        renders entities onto the window.
        """
        self.running = True

        background_thread = threading.Thread(
            target = App.background_updates,
            args = (self, self.model.update_background))
        background_thread.start()

        while self.running:
            self.running = self.controller.handle_input(
                self.model, self.view.get_screen_dimensions(), self.commands)
            self.view.update(self.model, self.controller)
            self.execute_commands()

        self.view.exit()
        background_thread.join()

        return True

    def background_updates(app, condition):
        """Thread function for running background updates. Thread stops when
        the application loop ends.
        :param app: The application
        :type app: App from 'app.py'
        """
        background_updater = BackgroundUpdater()

        while app.running:
            background_updater.update(app, condition)

    def execute_commands(self):
        """Executes commands received from the controller."""
        for command in self.commands:
            command.execute(self)

        self.commands.clear()
        self.controller.loading = False

    def load_from_file(self, filename = ''):
        """Tries to load model entities from the filename.
        :param filename: Saved filename to load from
        :type filename: str
        """

        try:
            loader = Loader(self.model, filename)
            self.controller.message_stack.insert(('Loaded from save file: '
                                                  + filename,))
        except:
            self.controller.message_stack.insert(('Error loading save file: '
                                                  + filename,))
            self.model = Model() # reset model

class BackgroundUpdater:
    """Performs background updates."""

    def update(self, app, condition):
        """Performs background updates when notified by the model."""

        with condition:
            condition.wait()
            # Future background updates can be added here
            
if __name__ == '__main__':
    load = ''

    # Load save file if supplied as command line argument
    if len(sys.argv) > 1:
        load = sys.argv[1]

    app = App(load)
    app.run()