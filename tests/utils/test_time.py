# Third-party library
import pytest

# Local library
from src.utils.time import *


###################
# get_hour_format #
###################

@pytest.mark.parametrize("time_string, expected_format", [
    pytest.param("11:59AM", TWELVE_HOURS_FORMAT, id="twelve_hours"),
    pytest.param("11h59", TWENTY_FOUR_HOURS_FORMAT_WITH_H, id="twenty_four_hours_with_h"),
    pytest.param("11:59", TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS, id="twenty_four_hours_with_dots"),
])
def test_get_hour_format_identifies_the_format(time_string, expected_format):
    assert get_hour_format(time_string) == expected_format


def test_get_hour_format_raises_on_an_unrecognized_string():
    with pytest.raises(ValueError):
        _ = get_hour_format("1159")


#####################################
# convert_time_string_to_nb_minutes #
#####################################

@pytest.mark.parametrize("time_string, expected_nb_minutes", [
    pytest.param("11:59AM", 719, id="twelve_hours_am"),
    pytest.param("12:00PM", 720, id="twelve_hours_noon"),
    pytest.param("12:01PM", 721, id="twelve_hours_just_after_noon"),
    pytest.param("01:00PM", 780, id="twelve_hours_pm"),
])
def test_convert_time_string_to_nb_minutes_parses_twelve_hour_strings(time_string, expected_nb_minutes):
    assert convert_time_string_to_nb_minutes(time_string) == expected_nb_minutes


@pytest.mark.parametrize("time_string, expected_nb_minutes", [
    pytest.param("11h59", 719, id="with_h"),
    pytest.param("13h00", 780, id="with_h_afternoon"),
    pytest.param("11:59", 719, id="with_dots"),
    pytest.param("13:00", 780, id="with_dots_afternoon"),
])
def test_convert_time_string_to_nb_minutes_parses_twenty_four_hour_strings(time_string, expected_nb_minutes):
    assert convert_time_string_to_nb_minutes(time_string) == expected_nb_minutes


def test_convert_time_string_to_nb_minutes_normalizes_a_twenty_four_hour_string_without_minutes():
    assert convert_time_string_to_nb_minutes("11h") == 660


def test_convert_time_string_to_nb_minutes_raises_on_an_unrecognized_string():
    with pytest.raises(ValueError):
        _ = convert_time_string_to_nb_minutes("1159")


#####################################
# convert_nb_minutes_to_time_string #
#####################################

@pytest.mark.parametrize("nb_minutes, hour_format, expected_time_string", [
    pytest.param(719, TWELVE_HOURS_FORMAT, "11:59AM", id="twelve_hours"),
    pytest.param(780, TWENTY_FOUR_HOURS_FORMAT_WITH_H, "13h00", id="twenty_four_hours_with_h"),
    pytest.param(780, TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS, "13:00", id="twenty_four_hours_with_dots"),
])
def test_convert_nb_minutes_to_time_string_formats_the_given_minutes(nb_minutes, hour_format, expected_time_string):
    assert convert_nb_minutes_to_time_string(nb_minutes, hour_format) == expected_time_string


def test_convert_nb_minutes_to_time_string_raises_on_an_unknown_hour_format():
    with pytest.raises(ValueError):
        _ = convert_nb_minutes_to_time_string(719, "unknown_format")


#######################################
# convert_time_string_in_given_format #
#######################################

def test_convert_time_string_in_given_format_returns_the_string_unchanged_when_already_in_that_format():
    assert convert_time_string_in_given_format("11:59AM", TWELVE_HOURS_FORMAT) == "11:59AM"


def test_convert_time_string_in_given_format_converts_between_formats():
    assert convert_time_string_in_given_format("11:59PM", TWENTY_FOUR_HOURS_FORMAT_WITH_H) == "23h59"


############################################
# get_hour_format_associated_with_language #
############################################

@pytest.mark.parametrize("language, expected_format", [
    pytest.param(LANGUAGE_ENGLISH_KEY, TWELVE_HOURS_FORMAT, id="english"),
    pytest.param(LANGUAGE_FRENCH_KEY, TWENTY_FOUR_HOURS_FORMAT_WITH_H, id="french"),
])
def test_get_hour_format_associated_with_language_returns_the_conventional_format(language, expected_format):
    assert get_hour_format_associated_with_language(language) == expected_format


def test_get_hour_format_associated_with_language_raises_on_an_unsupported_language():
    with pytest.raises(NotImplementedError):
        _ = get_hour_format_associated_with_language("unsupported_language")
