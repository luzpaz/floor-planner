from enum import Enum

EntityType = Enum(
    'EntityType',
    'NONE\
    EXTERIOR_WALL\
    INTERIOR_WALL\
    REGULAR_LINE\
    BUTTON_PANEL\
    SELECTED_BUTTON\
    BUTTON_BACKGROUND\
    SELECT_BUTTON\
    ERASE_BUTTON\
    DRAW_BUTTON\
    MOVE_BUTTON\
    MEASURE_BUTTON\
    ADD_TEXT_BUTTON\
    PAN_BUTTON\
    ZOOM_BUTTON\
    GRID_BUTTON\
    LAYERS_BUTTON\
    SETTINGS_BUTTON\
    UNDO_BUTTON\
    REDO_BUTTON\
    SAVE_BUTTON\
    EXPORT_BUTTON\
    EXIT_BUTTON\
    EXTERIOR_WALL_BUTTON\
    INTERIOR_WALL_BUTTON\
    WINDOW_BUTTON\
    DOOR_BUTTON\
    LOADING')

ModelMutex = Enum(
    'ModelMutex',
    'LINES\
    VERTICES\
    RECTANGLES')