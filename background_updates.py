class BackgroundUpdater:
    """The class responsible for performing background updates."""

    def update(self, app, condition):
        """Performs background updates when notified by the model."""

        with condition:
            condition.wait()