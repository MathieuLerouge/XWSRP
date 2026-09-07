# Third-party library
import pytest

# Local library
from src.utils.speed import *


############################
# convert_speed_to_m_per_s #
############################

@pytest.mark.parametrize("speed, unit, expected_m_per_s", [
    pytest.param(10, M_PER_S_STRING, 10, id="m_per_s"),
    pytest.param(60, KM_PER_MIN_STRING, 1000.0, id="km_per_min"),
    pytest.param(3600, KM_PER_H_STRING, 1000.0, id="km_per_h"),
])
def test_convert_speed_to_m_per_s_converts_from_the_given_unit(speed, unit, expected_m_per_s):
    assert convert_speed_to_m_per_s(speed, unit) == expected_m_per_s


def test_convert_speed_to_m_per_s_raises_on_an_unknown_unit():
    with pytest.raises(ValueError):
        _ = convert_speed_to_m_per_s(10, "unknown_unit")


############################
# convert_speed_in_m_per_s #
############################

@pytest.mark.parametrize("speed, unit, expected_speed", [
    pytest.param(10, M_PER_S_STRING, 10, id="m_per_s"),
    pytest.param(1000, KM_PER_MIN_STRING, 60.0, id="km_per_min"),
    pytest.param(1000, KM_PER_H_STRING, 3600.0, id="km_per_h"),
])
def test_convert_speed_in_m_per_s_converts_to_the_given_unit(speed, unit, expected_speed):
    assert convert_speed_in_m_per_s(speed, unit) == expected_speed


def test_convert_speed_in_m_per_s_raises_on_an_unknown_unit():
    with pytest.raises(ValueError):
        _ = convert_speed_in_m_per_s(10, "unknown_unit")


#########################
# convert_speed_from_to #
#########################

def test_convert_speed_from_to_returns_the_speed_unchanged_when_units_match():
    assert convert_speed_from_to(10, KM_PER_H_STRING, KM_PER_H_STRING) == 10


def test_convert_speed_from_to_converts_between_different_units():
    assert convert_speed_from_to(3600, KM_PER_H_STRING, KM_PER_MIN_STRING) == 60.0


@pytest.mark.parametrize("unit_from, unit_to", [
    pytest.param("unknown_unit", KM_PER_H_STRING, id="unknown_unit_from"),
    pytest.param(KM_PER_H_STRING, "unknown_unit", id="unknown_unit_to"),
])
def test_convert_speed_from_to_raises_on_an_unknown_unit(unit_from, unit_to):
    with pytest.raises(ValueError):
        _ = convert_speed_from_to(10, unit_from, unit_to)
