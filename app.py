import sdl2

from model import Model
from controller import Controller
from view import View

class App:
    def __init__(self):
        """Initialize the application MVC components"""
        self.model = Model()
        self.view = View()
        self.controller = Controller()

        self.running = False

    def run(self):
        """Begins execution of application loop, which handles user input and
        renders entities onto the window. Returns true if closed with no error.
        """
        
        self.running = True

        while self.running:
            self.running = self.controller.handle_input(self.model)
            self.view.update(self.model, self.controller)

        self.view.exit()

        return True

if __name__ == '__main__':
    app = App()
    app.run()