import sdl2

from entity_types import EntityType
from text import Text
from view import FontSize

class Button:
    """Button that the user can click in the application window."""

    def __init__(self, id, texture, relative_x = 0, relative_y = 0,
                 relative_width = 0, relative_height = 0):
        """Initializes the button."""
        self.id = id
        self.texture = texture
        self.relative_x = relative_x
        self.relative_y = relative_y
        self.relative_width = relative_width
        self.relative_height = relative_height

        # Whether the button is currently selected by the user
        self.selected = False

    def mouse_over(self, mouse_x, mouse_y, screen_dimensions):
        """Returns true if the mouse positions collide with the button.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        :param screen_dimensions: Screen width and height
        :type screen_dimensions: tuple(int, int)
        """

        # Screen dimensions
        screen_width = screen_dimensions[0]
        screen_height = screen_dimensions[1]

        location = sdl2.SDL_Rect(
            int(self.relative_x * screen_width),
            int(self.relative_y * screen_height),
            int(self.relative_width * screen_width),
            int(self.relative_height * screen_height))

        if mouse_x > location.x + location.w: return False
        if mouse_x < location.x: return False
        if mouse_y > location.y + location.h: return False
        if mouse_y < location.y: return False
        return True

class Panel:
    """Base class for a user interface button panel."""

    def __init__(self, texture, relative_x = 0, relative_y = 0,
                 relative_width = 0, relative_height = 0):
        "Initializes the panel."
        self.texture = texture
        self.relative_x = relative_x
        self.relative_y = relative_y
        self.relative_width = relative_width
        self.relative_height = relative_height

        # The button the user currently has their mouse over
        self.button_over = None

        # Whether this panel is visible to the user
        self.visible = True

        # Set of buttons the panel houses
        self.buttons = set()

        # Whether the panel has a special rendering function
        # If so, the renderer will skip it when iterating the normal panels
        self.special_rendering = False

    def mouse_over(self, mouse_x, mouse_y, screen_dimensions):
        """Returns true if mouse positions collide with any of the buttons
        in the panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        if not self.visible:
            return False

        for button in self.buttons:
            if button.mouse_over(mouse_x, mouse_y, screen_dimensions):
                self.button_over = button.id
                return True
            self.button_over = None
        return False

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Sets the selected button and adds a polling event.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        for button in self.buttons:
            if button.id == self.button_over:
                button.selected = True
            else:
                button.selected = False

        polling_event.append(self.button_over)

    def handle_mouse_hover(self, mouse_x, mouse_y, center_text):
        """Sets the center bottom text to the button the user is hovering over.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        center_text.set_bottom_text(self.button_labels[self.button_over])

    def reset(self):
        """Resets the selected attribute of all buttons."""
        for button in self.buttons:
            button.selected = False

class CenterButtonPanel(Panel):
    """The main user interface panel appearing at the top center of the screen.
    """

    NUM_BUTTONS = 16

    RELATIVE_X = 0.0
    RELATIVE_Y = 0.0
    RELATIVE_WIDTH = 1.0
    RELATIVE_HEIGHT = 0.05

    BUTTON_RELATIVE_SIZE = 0.03
    BUTTONS_TOTAL_WIDTH = 0.60
    BUTTONS_X_BUFFER = (RELATIVE_WIDTH - BUTTONS_TOTAL_WIDTH) / 2
    BUTTONS_Y_BUFFER = 0.01

    def get_relative_x(self):
        """Returns the relative x-position of the button based on the
        number of buttons already added."""
        return len(self.buttons) / CenterButtonPanel.NUM_BUTTONS\
            * CenterButtonPanel.BUTTONS_TOTAL_WIDTH\
            + CenterButtonPanel.BUTTONS_X_BUFFER

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL.value,
                        CenterButtonPanel.RELATIVE_X,
                        CenterButtonPanel.RELATIVE_Y,
                        CenterButtonPanel.RELATIVE_WIDTH,
                        CenterButtonPanel.RELATIVE_HEIGHT)

        entity_type = EntityType.SELECT_BUTTON.value
        while entity_type <= EntityType.EXIT_BUTTON.value:
            # Skip settings and list entities
            if entity_type != EntityType.SETTINGS_BUTTON.value\
                and entity_type != EntityType.INVENTORY_BUTTON.value:
                self.buttons.add(Button(len(self.buttons), entity_type,
                    self.get_relative_x(),
                    CenterButtonPanel.RELATIVE_Y
                    + CenterButtonPanel.BUTTONS_Y_BUFFER,
                    CenterButtonPanel.BUTTON_RELATIVE_SIZE,
                    CenterButtonPanel.BUTTON_RELATIVE_SIZE))

            entity_type += 1

        self.button_labels =\
            [
                'Select (ESC)',
                'Eraser Tool (CTRL + E)',
                'Draw Line (CTRL + D)',
                'Move Entity',
                'Measure Distance (CTRL + M)',
                'Add Text (CTRL + T)',
                'Pan Camera',
                'Zoom Camera',
                'Display Drawing Grid (CTRL + G)',
                'Open Layers',
                'Undo (CTRL + Z)',
                'Redo (CTRL + Y)',
                'Save Drawing (CTRL + S)',
                'Load Drawing (CTRL + O)',
                'Export to PNG (CTRL + E)',
                'Exit Application (ALT + F4)',
            ]

class LeftButtonPanel(Panel):
    """The user interface panel appearing at the left side of the screen.
    """

    NUM_BUTTONS = 4

    BUTTON_RELATIVE_SIZE = 0.03
    BUTTONS_TOTAL_HEIGHT = 0.14
    BUTTONS_X_BUFFER = 0.005
    BUTTONS_Y_BUFFER = 0.01

    RELATIVE_X = 0.0
    RELATIVE_WIDTH = 0.04
    RELATIVE_HEIGHT = BUTTONS_TOTAL_HEIGHT + 1.5 * BUTTONS_Y_BUFFER
    RELATIVE_Y = (1.0 - RELATIVE_HEIGHT) / 2

    BUTTONS_Y_BUFFER = RELATIVE_Y + BUTTONS_Y_BUFFER

    def get_relative_y(self):
        """Returns the relative y-position of the button based on the
        number of buttons already added."""
        return len(self.buttons) / LeftButtonPanel.NUM_BUTTONS\
            * LeftButtonPanel.BUTTONS_TOTAL_HEIGHT\
            + LeftButtonPanel.BUTTONS_Y_BUFFER

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL.value,
                        LeftButtonPanel.RELATIVE_X,
                        LeftButtonPanel.RELATIVE_Y,
                        LeftButtonPanel.RELATIVE_WIDTH,
                        LeftButtonPanel.RELATIVE_HEIGHT)

        entity_type = EntityType.EXTERIOR_WALL_BUTTON.value
        while entity_type <= EntityType.DOOR_BUTTON.value:
            self.buttons.add(Button(len(self.buttons),
                entity_type,
                LeftButtonPanel.RELATIVE_X + LeftButtonPanel.BUTTONS_X_BUFFER,
                self.get_relative_y(),
                LeftButtonPanel.BUTTON_RELATIVE_SIZE,
                LeftButtonPanel.BUTTON_RELATIVE_SIZE))
            entity_type += 1

        self.button_labels =\
            [
                'Draw Exterior Wall (0)',
                'Draw Interior Wall (1)',
                'Place Window (2)',
                'Place Door (3)',
            ]

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Same as Panel.handle_mouse_click but adjusts the polling event
        to account for the number of buttons in the central button panel.
        """
        Panel.handle_mouse_click(self, mouse_x, mouse_y,
                                 center_text, polling_event)
        polling_event[0] += CenterButtonPanel.NUM_BUTTONS

class RightButtonPanel(Panel):
    """The user interface panel appearing at the right side of the screen.
    """

    NUM_BUTTONS = 4

    BUTTON_RELATIVE_SIZE = 0.03
    BUTTONS_TOTAL_HEIGHT = 0.14
    BUTTONS_X_BUFFER = 0.005
    BUTTONS_Y_BUFFER = 0.01

    RELATIVE_X = 0.961
    RELATIVE_WIDTH = 0.04
    RELATIVE_HEIGHT = BUTTONS_TOTAL_HEIGHT + 1.5 * BUTTONS_Y_BUFFER
    RELATIVE_Y = (1.0 - RELATIVE_HEIGHT) / 2

    BUTTONS_Y_BUFFER = RELATIVE_Y + BUTTONS_Y_BUFFER

    def get_relative_y(self):
        """Returns the relative y-position of the button based on the
        number of buttons already added."""
        return len(self.buttons) / RightButtonPanel.NUM_BUTTONS\
            * RightButtonPanel.BUTTONS_TOTAL_HEIGHT\
            + RightButtonPanel.BUTTONS_Y_BUFFER

    def __init__(self):
        """Initializes the buttons."""
        Panel.__init__(self, EntityType.BUTTON_PANEL.value,
                        RightButtonPanel.RELATIVE_X,
                        RightButtonPanel.RELATIVE_Y,
                        RightButtonPanel.RELATIVE_WIDTH,
                        RightButtonPanel.RELATIVE_HEIGHT)

        for button in range(RightButtonPanel.NUM_BUTTONS):
            self.buttons.add(Button(len(self.buttons),
                EntityType.LAYER.value,
                RightButtonPanel.RELATIVE_X + RightButtonPanel.BUTTONS_X_BUFFER,
                self.get_relative_y(),
                RightButtonPanel.BUTTON_RELATIVE_SIZE,
                RightButtonPanel.BUTTON_RELATIVE_SIZE))

        self.button_labels =\
            [
                'Layer 1',
                'Layer 2',
                'Layer 3',
                'Layer 4',
            ]

        # Not visible by default
        self.visible = False

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Same as Panel.handle_mouse_click but adjusts the polling event
        to account for the number of buttons in the previous panel.
        """
        Panel.handle_mouse_click(self, mouse_x, mouse_y,
                                 center_text, polling_event)
        polling_event[0] += CenterButtonPanel.NUM_BUTTONS\
            + LeftButtonPanel.NUM_BUTTONS

class SettingsPanel(Panel):
    """The settings panel appearing on the center of the screen when
    the user toggles it by pressing the settings button."""

    RELATIVE_WIDTH = 0.20
    RELATIVE_HEIGHT = 0.20
    RELATIVE_X = (1.0 - RELATIVE_WIDTH) / 2.0
    RELATIVE_Y = (1.0 - RELATIVE_HEIGHT) / 2.0

    def __init__(self):
        """Initializes the settings buttons in the panel."""

        Panel.__init__(self, EntityType.BUTTON_PANEL.value,
                       SettingsPanel.RELATIVE_X,
                       SettingsPanel.RELATIVE_Y,
                       SettingsPanel.RELATIVE_WIDTH,
                       SettingsPanel.RELATIVE_HEIGHT)

        self.buttons = set()
        self.buttons.add(GraphicsButton())

        self.visible = False

        self.special_rendering = True

        self.button_labels =\
            [
                'Rasterize graphics - default setting',
                'Vectorize graphics - requires higher performance CPU/GPU',
            ]

    def mouse_over(self, mouse_x, mouse_y, screen_dimensions):
        """Returns true if mouse positions collide with any of the buttons
        in the panel.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        if not self.visible:
            return False

        for settings in self.buttons:
            for button in settings.buttons:
                if button.mouse_over(mouse_x, mouse_y, screen_dimensions):
                    self.button_over = button.id
                    return True
                self.button_over = None
        return False

    def handle_mouse_click(self, mouse_x, mouse_y, center_text, polling_event):
        """Sets the selected button and adds a polling event.
        :param mouse_x: Mouse x-position
        :param mouse_y: Mouse y-position
        :type mouse_x, mouse_y: int
        """
        for settings in self.buttons:
            for button in settings.buttons:
                if button.id == self.button_over:
                    # Currently, do not allow the user
                    # to select vectorized graphics
                    if button.id != 1:
                        button.selected = True
                    else:
                        settings.buttons[0].selected = True
                else:
                    button.selected = False

        polling_event.append(self.button_over + CenterButtonPanel.NUM_BUTTONS\
            + LeftButtonPanel.NUM_BUTTONS + RightButtonPanel.NUM_BUTTONS)

class SettingsButton:
    """A mini-panel on the settings that has a top and bottom text and
    at least two buttons."""

    TEXT_BUFFER = SettingsPanel.RELATIVE_HEIGHT * 0.15

    def __init__(self, button_relative_y = 0, top_text = '', bottom_text = '',
                 num_buttons = 0):
        """Initializes the top/bottom texts and buttons at the
        relative location."""
        self.top_text = Text(
            SettingsPanel.RELATIVE_X + SettingsPanel.RELATIVE_WIDTH / 2,
            button_relative_y - SettingsButton.TEXT_BUFFER, FontSize.LARGE,
            (127, 127, 127))
        self.top_text.text = top_text

        self.bottom_text = Text(
            SettingsPanel.RELATIVE_X + SettingsPanel.RELATIVE_WIDTH / 2,
            button_relative_y, FontSize.SMALL, (127, 127, 127))
        self.bottom_text.text = bottom_text

        self.num_buttons = num_buttons

        self.buttons = []
        self.selected_button = None

class GraphicsButton(SettingsButton):
    """The settings button for changing between using vectorized or
    rasterized graphics."""

    BUTTON_SIZE = 0.05
    RELATIVE_Y = SettingsPanel.RELATIVE_Y\
        + (SettingsPanel.RELATIVE_HEIGHT * 0.50)
    TEXT_RELATIVE_Y = RELATIVE_Y - (SettingsPanel.RELATIVE_HEIGHT * 0.15)

    BUTTON_BUFFER = 0.05

    def __init__(self):
        """Initializes the rasterize and vectorize button and top/bottom text.
        """
        SettingsButton.__init__(self, GraphicsButton.TEXT_RELATIVE_Y,
                                'Vectorize Graphics:',
                                'OFF / ON', 2)

        self.buttons.append(Button(0, EntityType.RASTERIZE.value,
                                   SettingsPanel.RELATIVE_X
                                   + GraphicsButton.BUTTON_BUFFER,
                                   GraphicsButton.RELATIVE_Y,
                                   GraphicsButton.BUTTON_SIZE,
                                   GraphicsButton.BUTTON_SIZE))
        self.buttons.append(Button(1, EntityType.VECTORIZE.value,
                                   SettingsPanel.RELATIVE_X
                                   + 2.0 * GraphicsButton.BUTTON_BUFFER,
                                   GraphicsButton.RELATIVE_Y,
                                   GraphicsButton.BUTTON_SIZE,
                                   GraphicsButton.BUTTON_SIZE))

        self.selected_button = self.buttons[0]
        self.buttons[0].selected = True