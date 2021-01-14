from copy import deepcopy

class AddAction:
    """The action container for when a user adds an entity."""
    
    def __init__(self, entity = None):
        """Initializes the add action.
        :param entity: The entity the user added
        :type entity: Any entity class from 'entities.py'
        """
        self.entity = entity

    def undo(self, controller, model):
        """Defines what is needed to undo this action:
        Removes the added entity from the model."""
        model.remove_entity(self.entity, False)

    def redo(self, controller, model):
        """Defines what is needed to redo this action:
        Adds the removed entity into the model."""
        model.add_entity(self.entity)

    def __str__(self):
        """Returns description."""
        return 'Added ' + str(self.entity)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.entity.__repr__()

class DeleteAction:
    """The action container for when a user deletes an entity."""
    
    def __init__(self, entity = None):
        """Initializes the delete action.
        :param entity: The entity the user deleted
        :type entity: Any entity class from 'entities.py'
        """
        self.entity = entity

    def undo(self, controller, model):
        """Defines what is needed to undo this action:
        Adds the deleted entity into the model."""
        model.add_entity(self.entity)

    def redo(self, controller, model):
        """Defines what is needed to redo this action:
        Removes the added entity from the model."""
        model.remove_entity(self.entity, False)

    def __str__(self):
        """Returns description."""
        return 'Deleted ' + str(self.entity)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.entity.__repr__()

class MoveAction:
    """The action container for when a user moves an entity."""

    def __init__(self, previous_state = None):
        """Copies the previous state of the entity the user moved.
        :param previous_state: The entity the user *will* move
        :type entity: Any entity class from 'entities.py'"""
        self.previous = deepcopy(previous_state)
        self.current = None

    def undo(self, controller, model):
        """Defines what is needed to undo this action:
        Replaces the current entity with its previous state."""
        model.remove_entity(self.current, False)
        model.add_entity(self.previous)

    def redo(self, controller, model):
        """Defines what is needed to redo this action:
        Replaces the previous entity with its moved state."""
        model.remove_entity(self.previous, False)
        model.add_entity(self.current)

    def __str__(self):
        """Returns description."""
        return 'Moved ' + str(self.current)

    def __repr__(self):
        """Returns info needed for debugging."""
        return self.current.__repr__()

class ActionType:
    ADD = 0
    DELETE = 1
    MOVE = 2