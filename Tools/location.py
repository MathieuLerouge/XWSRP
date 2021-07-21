###########
# Modules #
###########

# Basic modules
import numpy as np



##################
# Class Location #
##################


class Location:

    geographic = None
    coordinates = None
    coordinatesInRadians = None

    def __init__(self, firstCoordinate = None, secondCoordinate = None, geographic = True):
        if firstCoordinate != None:
            self.geographic = geographic
            self.coordinates = np.array([firstCoordinate, secondCoordinate], dtype = np.float64)
            if geographic:
                # Remark: coordinates[0] is a lattitude, coordinates[1] is a longitude
                self.coordinatesInRadians = self.coordinates*np.pi/180

    def __eq__(self, location):
        return np.isclose(self.coordinates, location.coordinates, atol = 0.00000001)

    def isEmpty(self):
        return self.geographic == None

    def isCartesian(self):
        return not(self.geographic)

    def isGeographic(self):
        return self.geographic

    def distanceTo(self, location):
        if self.isEmpty() or location.isEmpty():
            return 0
        else:
            if self.geographic:
                return computeGeographicDistance(self.coordinatesInRadians, location.coordinatesInRadians)
            else:
                return computeCartesianDistance(self.coordinates, location.coordinates)

    def __repr__(self):
        if self.isEmpty():
            return "Empty location"
        else:
            return f"({self.coordinates[0]}, {self.coordinates[1]})"



#############
# Functions #
#############


def computeCartesianDistance(coordinates1, coordinates2):
    return np.linalg.norm(coordinates2 - coordinates1, 2)


def computeGeographicDistance(coordinates1, coordinates2):
    # Remark 1: coordinates[0] is a lattitude, coordinates[1] is a longitude
    # Remark 2: inputs must be in radians
    # Remark 3: the result is in km
    earthRadius = 6371
    return earthRadius*np.arccos(
        min(1.0,
            np.sin(coordinates1[0])*np.sin(coordinates2[0]) +
            np.cos(coordinates1[0])*np.cos(coordinates2[0])*np.cos(coordinates2[1] - coordinates1[1])
        )
    )
