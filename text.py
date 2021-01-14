import sdl2

from view import FontSize

class Text:
    """Wrapper class around text to be displayed. Contains the relative
    position and size to the application screen size (%), the font,
    and the text color."""

    def __init__(self, relative_x = 0, relative_y = 0,
                 font = FontSize.SMALL, color = (0, 0, 0)):
        """Initializes the text."""
        self.relative_x = relative_x
        self.relative_y = relative_y
        self.font = font
        self.color = sdl2.SDL_Color(color[0], color[1], color[2])
        self.text = ''

class TimeStampedMessage(Text):
    """A text object with a time stamp (when the text was created)."""

    def __init__(self, text, relative_x = 0, relative_y = 0,
                 font = FontSize.SMALL, color = (0, 0, 0)):
        """Initializes the text."""
        Text.__init__(self, relative_x, relative_y, font, color)
        self.text = text
        self.time = sdl2.SDL_GetTicks()

    def __repr__(self):
        """Returns the text string for debugging."""
        return self.text

class TextDisplayer:
    """Base class for a user interface object that displays text."""

    def __init__(self):
        """Initializes the text displayer."""
        self.text = []

class CenterText(TextDisplayer):
    """Text displayer responsible for displaying text on the top center,
    bottom center, and bottom right of the application window."""

    # Indices in text list for each text
    TOP_CENTER_TEXT = 0
    BOTTOM_CENTER_TEXT = 1
    BOTTOM_RIGHT_TEXT = 2

    # Relative positions
    TOP_CENTER_RELATIVE_Y = 0.06
    BOTTOM_CENTER_RELATIVE_Y = 0.99

    # Relative positions
    BOTTOM_RIGHT_RELATIVE_X = 0.99
    BOTTOM_RIGHT_RELATIVE_Y = 0.99

    def __init__(self):
        """Initializes the center text displayers."""
        TextDisplayer.__init__(self)
        self.text.append(Text(0.50, CenterText.TOP_CENTER_RELATIVE_Y,
                         FontSize.SMALL))
        self.text.append(Text(0.50, CenterText.BOTTOM_CENTER_RELATIVE_Y,
                         FontSize.MEDIUM))
        self.text.append(Text(CenterText.BOTTOM_RIGHT_RELATIVE_X,
                         CenterText.BOTTOM_RIGHT_RELATIVE_Y, FontSize.MEDIUM))

    def set_top_text(self, top_text = ''):
        """Sets the text displayed at the top center of the screen.
        :param top_text: The text to display
        :type top_text: str
        """
        self.text[CenterText.TOP_CENTER_TEXT].text = top_text

    def set_bottom_text(self, bottom_text = ''):
        """Sets the text displayed at the bottom center of the screen.
        :param bottom_text: The text to display
        :type bottom_text: str
        """
        self.text[CenterText.BOTTOM_CENTER_TEXT].text = bottom_text

    def set_right_text(self, right_text = ''):
        """Sets the text displayed at the bottom right of the screen.
        :param right_text: The text to display
        :type right_text: str
        """
        self.text[CenterText.BOTTOM_RIGHT_TEXT].text = right_text

class MessageStack(TextDisplayer):
    """Text displayer responsible for displaying stacking messages to the user
    on the bottom left of the screen. Messages stay on the screen for the
    duration and stack as more messages appear."""

    # Time the message stays in the stack (ms)
    DURATION = 5000
    
    # Relative positions
    RELATIVE_X = 0.05
    RELATIVE_Y = 0.95

    # Spacing between texts
    SPACING = 0.03

    def update(self):
        """Removes expired messages and adjusts the positions of the messages
        so that they stack.
        """
        index = 0
        for message in self.text:
            message.relative_y = MessageStack.RELATIVE_Y\
                - MessageStack.SPACING * index
            index += 1

            if MessageStack.DURATION < sdl2.SDL_GetTicks() - message.time:
                self.text.remove(message)
                return

    def insert(self, list):
        """Inserts the messages from the list into the stack.
        :param list: List of messages to insert
        :type list: list
        """
        for message in list:
            self.text.append(TimeStampedMessage(
                message, MessageStack.RELATIVE_X))

class FPSDisplayer(TextDisplayer):
    """Text displayer responsible for displaying the average FPS every second
    on the top right corner of the screen."""

    # Relative positions
    RELATIVE_X = 0.99
    RELATIVE_Y = 0.06

    def __init__(self):
        """Initializes the FPS displayer."""
        TextDisplayer.__init__(self)
        self.text.append(Text(FPSDisplayer.RELATIVE_X, FPSDisplayer.RELATIVE_Y))

        self.last_fps = sdl2.SDL_GetTicks()
        self.frames = 0

    def update(self):
        """Updates the average frames per second of the controller thread.
        """
        self.frames += 1
        if 1000 < sdl2.SDL_GetTicks() - self.last_fps:
            self.text[0].text = 'FPS: ' + str(self.frames)
            self.last_fps = sdl2.SDL_GetTicks()
            self.frames = 0