#! /usr/bin/env python3
# coding: utf-8


# Third party library
import numpy as np


# Global variables
COORDINATES_TOLERANCE = 0.00000001
EARTH_RADIUS_IN_KM = 6371


# Class Location
class Location:

    def __init__(self, first_coordinate=None, second_coordinate=None, is_geographic=True):
        """Create a location defined given either geographic coordinates or cartesian coordinates

        :param first_coordinate: latitude in degrees, if coordinates are geographic; x in km otherwise (float)
        :param second_coordinate: longitude in degrees, if coordinates are geographic; y in km otherwise (float)
        :param is_geographic: True if _coordinates are geographic, False otherwise (bool)
        """
        self._is_geographic = True
        self._coordinates = None
        if first_coordinate is not None:
            self._is_geographic = is_geographic
            self._coordinates = np.array([first_coordinate, second_coordinate], dtype=np.float64)
            if self.is_geographic():
                self._coordinates = self._coordinates * np.pi / 180

    def __eq__(self, location):
        return np.isclose(self._coordinates, location.coordinates, atol=COORDINATES_TOLERANCE)

    @property
    def coordinates(self):
        return self._coordinates

    @property
    def latitude(self):
        if self.is_geographic():
            return self.coordinates[0]
        else:
            raise ValueError("This location is not geographic")

    def get_latitude(self, radians=True):
        if radians:
            return self.latitude
        else:
            return np.rad2deg(self.latitude)

    @property
    def longitude(self):
        if self.is_geographic():
            return self.coordinates[1]
        else:
            raise ValueError("This location is not geographic")

    def get_longitude(self, radians=True):
        if radians:
            return self.longitude
        else:
            return np.rad2deg(self.longitude)

    def is_empty(self):
        return self._coordinates is None

    def is_geographic(self):
        return self._is_geographic

    def is_cartesian(self):
        return not self.is_geographic()

    def distance_to(self, location):
        if self.is_empty():
            raise ValueError("this location is empty")
        elif location is None or location.is_empty():
            raise ValueError("the given location is empty")
        else:
            if self.is_geographic():
                if location.is_cartesian():
                    raise ValueError("this location is geographic while the given location is cartesian")
                return compute_geographic_distance(self.coordinates, location.coordinates)
            else:
                if location.is_geographic():
                    raise ValueError("this location is cartesian while the given location is geographic")
                return compute_cartesian_distance(self.coordinates, location.coordinates)

    def __repr__(self):
        if self.is_empty():
            return "(Ø,Ø)"
        else:
            return f"({np.round(self._coordinates[0], 3)}, {np.round(self._coordinates[1], 3)})"


def compute_cartesian_distance(coordinates1, coordinates2):
    """Compute the distance between two pairs of cartesian coordinates

    :param coordinates1: array (numpy.array or list) of two cartesian coordinates (float)
    :param coordinates2: array (numpy.array or list) of two cartesian coordinates (float)
    :returns: distance in km (float)
    """
    return np.linalg.norm(coordinates2 - coordinates1, 2)


def compute_geographic_distance(coordinates1, coordinates2):
    """Compute the distance between two pairs of geographic coordinates

    :param coordinates1: array (numpy.array or list) of two geographic coordinates (float),
    (coordinates[0] is a latitude in radians, coordinates[1] is a longitude in radians)
    :param coordinates2: array (numpy.array or list) of two geographic coordinates (float),
    (coordinates[0] is a latitude in radians, coordinates[1] is a longitude in radians)
    :returns: distance in km (float)
    """
    if np.equal(coordinates1, coordinates2).all():
        return 0
    else:
        return EARTH_RADIUS_IN_KM * np.arccos(
            min(1.0,
                np.sin(coordinates1[0]) * np.sin(coordinates2[0]) +
                np.cos(coordinates1[0]) * np.cos(coordinates2[0]) * np.cos(coordinates2[1]-coordinates1[1])
                )
        )


def main():

    # Create geographic locations
    example_geographic_location1 = Location(44.556549383420084, -0.31939224223757195)
    example_geographic_location2 = Location(44.967500952177986, -0.6086852638150881)
    print(example_geographic_location1)
    print(example_geographic_location2)
    print(example_geographic_location1.distance_to(example_geographic_location2))

    # Create cartesian locations
    example_cartesian_location1 = Location(1, 0, is_geographic=False)
    example_cartesian_location2 = Location(1, 1, is_geographic=False)
    print(example_cartesian_location1)
    print(example_cartesian_location2)
    print(example_cartesian_location1.distance_to(example_cartesian_location2))

    # Create empty location
    example_empty_location = Location()
    print(example_empty_location)


if __name__ == '__main__':
    main()
