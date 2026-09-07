# Global variables
M_PER_S_STRING = 'm/s'
KM_PER_MIN_STRING = 'km/min'
KM_PER_H_STRING = 'km/h'


def convert_speed_to_m_per_s(speed: float, unit: str):
    """
    Converts a speed from the given unit to m/s.

    Args:
        speed: Speed value expressed in unit.
        unit: Unit speed is currently expressed in.

    Returns:
        The speed converted to m/s.

    Raises:
        ValueError: If unit isn't a known speed unit.
    """
    if unit == M_PER_S_STRING:
        return speed
    elif unit == KM_PER_MIN_STRING:
        return speed * 1000 / 60
    elif unit == KM_PER_H_STRING:
        return speed * 1000 / 3600
    else:
        raise ValueError(f"Unknown unit: {unit}")


def convert_speed_in_m_per_s(speed: float, unit: str):
    """
    Converts a speed from m/s to the given unit.

    Args:
        speed: Speed value expressed in m/s.
        unit: Unit to convert the speed to.

    Returns:
        The speed converted to unit.

    Raises:
        ValueError: If unit isn't a known speed unit.
    """
    if unit == M_PER_S_STRING:
        return speed
    elif unit == KM_PER_MIN_STRING:
        return speed * 60 / 1000
    elif unit == KM_PER_H_STRING:
        return speed * 3600 / 1000
    else:
        raise ValueError(f"Unknown unit: {unit}")


def convert_speed_from_to(speed: float, unit_from: str, unit_to: str):
    """
    Converts a speed from one unit to another.

    Args:
        speed: Speed value expressed in unit_from.
        unit_from: Unit speed is currently expressed in.
        unit_to: Unit to convert the speed to.

    Returns:
        The speed converted to unit_to.

    Raises:
        ValueError: If unit_from or unit_to isn't a known speed unit.
    """
    if unit_from == unit_to:
        return speed
    else:
        return convert_speed_in_m_per_s(convert_speed_to_m_per_s(speed, unit_from), unit_to)
