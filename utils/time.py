#! /usr/bin/env python3
# coding: utf-8


# Standard library
import datetime as dt


def convert_time_string_to_nb_minutes(time_string):
    """
    Convert a given time as string to a number of minutes

    :param time_string: time string with format HH:MMam or HH:MMpm (str)
    :return: number of minutes (int)
    """
    return int((dt.datetime.strptime(time_string, '%I:%M%p') -
                dt.datetime.strptime("00:00am", '%H:%M%p')).total_seconds()/60)


def convert_nb_minutes_to_time_string(nb_minutes):
    midnight = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    time = midnight + dt.timedelta(0, 60*nb_minutes)
    return time.strftime('%I:%M%p')
