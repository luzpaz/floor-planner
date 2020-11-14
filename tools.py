class Tools:
    def convert_to_unit_system(value, unit_system = 'ft'):
        if unit_system == 'ft':
            feet = value // 12
            inches = value - feet * 12
            return str(int(feet)) + " ft " + str(int(inches)) + " in"
        return ''

