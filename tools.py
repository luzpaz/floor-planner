class Tools:
    """The class offering static utilities needed across various classes."""

    def convert_to_unit_system(value, unit_system = 'ft'):
        """Returns the value in the unit system specified.
        Currently only supports feet and inches.
        :param value: The pixel value, default as inches
        :type value: double
        :param unit_system: The target unit system
        :type unit_system: str
        """
        value = abs(value)

        if unit_system == 'ft':
            feet = value // 12
            inches = value - feet * 12
            return str(int(feet)) + " ft " + str(int(inches)) + " in"
        return ''

