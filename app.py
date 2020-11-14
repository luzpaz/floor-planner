import sdl2

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
        renders entities onto the window. Returns true if closed with no error.
        """
        
        self.running = True

        while self.running:
            self.running = self.controller.handle_input(
                self.model, self.commands)
            self.view.update(self.model, self.controller)
            self.execute_commands()

        self.view.exit()

        return True

    def execute_commands(self):
        """Executes commands received from the controller."""
        for command in self.commands:
            command.execute(self)

        self.commands.clear()


if __name__ == '__main__':
    app = App()
    app.run()