from enum import Enum

EntityType = Enum(
    'EntityType',
    'NONE\
    EXTERIOR_WALL\
    INTERIOR_WALL\
    BUTTON_PANEL\
    SELECT_BUTTON\
    DELETE_BUTTON\
    DRAW_BUTTON\
    MOVE_BUTTON\
    MEASURE_BUTTON\
    ADD_TEXT_BUTTON\
    PAN_BUTTON\
    ZOOM_BUTTON\
    LAYERS_BUTTON\
    SETTINGS_BUTTON\
    UNDO_BUTTON\
    REDO_BUTTON\
    SAVE_BUTTON')