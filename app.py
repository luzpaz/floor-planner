import sdl2, threading

from background_updates import BackgroundUpdater
from model import Model
from controller import Controller
from view import View

class App:
    """The class responsible for housing the MVC components and executing
    the application loop."""

    def __init__(self):
        """Initialize the application MVC components."""
        self.model = Model()
        self.view = View()
        self.controller = Controller()

        # Whether the application loop is executing
        self.running = False

        # Commands received from the controller
        self.commands = []

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

if __name__ == '__main__':
    app = App()
    app.run()