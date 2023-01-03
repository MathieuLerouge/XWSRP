# Global variables
M_PER_S_STRING = 'm/s'
KM_PER_MIN_STRING = 'km/min'
KM_PER_H_STRING = 'km/h'


def convert_speed_to_m_per_s(speed: float, unit: str):
    """
    Convert a speed in another unit to m/s

    :param speed: speed in the given unit (float)
    :param unit: unit of the speed (str)
    :return: speed in m/s (float)
    """
    if unit == M_PER_S_STRING:
        return speed
    elif unit == KM_PER_MIN_STRING:
        return speed * 1000 / 60
    elif unit == KM_PER_H_STRING:
        return speed * 1000 / 3600
    else:
        raise ValueError("Unknown unit: " + unit)


def convert_speed_in_m_per_s(speed: float, unit: str):
    """
    Convert a speed in m/s to another unit

    :param speed: speed in m/s (float)
    :param unit: unit to convert to (str)
    :return: speed in the given unit (float)
    """
    if unit == M_PER_S_STRING:
        return speed
    elif unit == KM_PER_MIN_STRING:
        return speed * 60 / 1000
    elif unit == KM_PER_H_STRING:
        return speed * 3600 / 1000
    else:
        raise ValueError("Unknown unit: " + unit)


def convert_speed_from_to(speed: float, unit_from: str, unit_to: str):
    """
    Convert a speed in a unit to another unit

    :param speed: speed in the given unit (float)
    :param unit_from: unit of the speed (str)
    :param unit_to: unit to convert to (str)
    :return: speed in the given unit (float)
    """
    if unit_from == unit_to:
        return speed
    else:
        return convert_speed_in_m_per_s(convert_speed_to_m_per_s(speed, unit_from), unit_to)
