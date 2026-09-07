# Third party library
import numpy as np


# Global variables
COORDINATES_TOLERANCE = 1e-8
EARTH_RADIUS_IN_KM = 6371


############
# Location #
############

class Location:
    """
    A point defined by either geographic (latitude/longitude) or cartesian (x/y) coordinates.
    """

    def __init__(self, first_coordinate=None, second_coordinate=None, is_geographic=True):
        """
        Args:
            first_coordinate: Latitude in degrees if is_geographic, x in km otherwise. None for an empty location.
            second_coordinate: Longitude in degrees if is_geographic, y in km otherwise. None for an empty location.
            is_geographic: True if the coordinates are geographic, False if they're cartesian.
        """
        self._is_geographic = True
        self._coordinates = None
        if first_coordinate is not None:
            self._is_geographic = is_geographic
            self._coordinates = np.array([first_coordinate, second_coordinate], dtype=np.float64)
            if self.is_geographic():
                self._coordinates = self._coordinates * np.pi / 180

    def __eq__(self, location):
        """
        Returns whether both locations' coordinates are within COORDINATES_TOLERANCE of each other.

        Two empty locations are considered equal; an empty location is never equal to a non-empty one.
        """
        if not isinstance(location, Location):
            return False
        elif self.is_empty() or location.is_empty():
            return self.is_empty() and location.is_empty()
        else:
            self_coordinates = self._coordinates
            other_coordinates = location.coordinates
            assert self_coordinates is not None and other_coordinates is not None
            return bool(np.all(np.isclose(self_coordinates, other_coordinates, atol=COORDINATES_TOLERANCE)))

    @property
    def coordinates(self):
        """The raw coordinate array, or None if this location is empty."""
        return self._coordinates

    @property
    def latitude(self):
        """
        Latitude in radians.

        Raises:
            ValueError: If this location isn't geographic.
        """
        if self.is_geographic():
            return self.coordinates[0]
        else:
            raise ValueError("This location is not geographic")

    def get_latitude(self, radians=True):
        """
        Returns the latitude, in radians or degrees.

        Args:
            radians: If True, return the latitude in radians. If False, in degrees.

        Returns:
            The latitude.

        Raises:
            ValueError: If this location isn't geographic.
        """
        if radians:
            return self.latitude
        else:
            return np.rad2deg(self.latitude)

    @property
    def longitude(self):
        """
        Longitude in radians.

        Raises:
            ValueError: If this location isn't geographic.
        """
        if self.is_geographic():
            return self.coordinates[1]
        else:
            raise ValueError("This location is not geographic")

    def get_longitude(self, radians=True):
        """
        Returns the longitude, in radians or degrees.

        Args:
            radians: If True, return the longitude in radians. If False, in degrees.

        Returns:
            The longitude.

        Raises:
            ValueError: If this location isn't geographic.
        """
        if radians:
            return self.longitude
        else:
            return np.rad2deg(self.longitude)

    def is_empty(self):
        """Returns whether this location has no coordinates."""
        return self._coordinates is None

    def is_geographic(self):
        """Returns whether this location's coordinates are geographic (latitude/longitude)."""
        return self._is_geographic

    def is_cartesian(self):
        """Returns whether this location's coordinates are cartesian (x/y)."""
        return not self.is_geographic()

    def distance_to(self, location):
        """
        Returns the distance, in km, to another location.

        Args:
            location: Location to compute the distance to. Must be non-empty and use the same
                coordinate system (geographic or cartesian) as this location.

        Returns:
            The distance in km.

        Raises:
            ValueError: If either location is empty, or if the two locations don't use the same
                coordinate system.
        """
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
    """
    Returns the Euclidean distance, in km, between two pairs of cartesian (x, y) coordinates.

    Args:
        coordinates1: First pair of cartesian coordinates, in km (numpy.array or list of float).
        coordinates2: Second pair of cartesian coordinates, in km (numpy.array or list of float).

    Returns:
        The distance in km.
    """
    return np.linalg.norm(coordinates2 - coordinates1, 2)


def compute_geographic_distance(coordinates1, coordinates2):
    """
    Returns the great-circle distance, in km, between two pairs of geographic coordinates.

    Args:
        coordinates1: First (latitude, longitude) pair, in radians (numpy.array or list of float).
        coordinates2: Second (latitude, longitude) pair, in radians (numpy.array or list of float).

    Returns:
        The distance in km.
    """
    if np.equal(coordinates1, coordinates2).all():
        return 0
    else:
        return EARTH_RADIUS_IN_KM * np.arccos(
            min(1.0,
                np.sin(coordinates1[0]) * np.sin(coordinates2[0]) +
                np.cos(coordinates1[0]) * np.cos(coordinates2[0]) * np.cos(coordinates2[1] - coordinates1[1])
                )
        )
