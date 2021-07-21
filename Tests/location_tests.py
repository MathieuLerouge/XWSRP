###########
# Modules #
###########

# Basic modules
import sys, os

# Add Classes directory to system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Classes'))

# Project modules
from location import *


####################
# Global variables #
####################

# Define global geographic locations
exampleGeographicLocation1 = Location(44.556549383420084, -0.31939224223757195)
exampleGeographicLocation2 = Location(44.967500952177986, -0.6086852638150881)

# Define global cartesian locations
exampleCartesianLocation1 = Location(1, 0, geographic = False)
exampleCartesianLocation2 = Location(1, 1, geographic = False)

# Define global empty location
exampleEmptyLocation = Location()



#########
# Tests #
#########

def runLocationTests():

    # Geographic locations
    print("")
    print(exampleGeographicLocation1)
    print(exampleGeographicLocation2)
    print(exampleGeographicLocation1.isGeographic())
    print(exampleGeographicLocation1.isCartesian())

    # Cartesian locations
    print("")
    print(exampleCartesianLocation1)
    print(exampleCartesianLocation2)
    print(exampleCartesianLocation1.isGeographic())
    print(exampleCartesianLocation1.isCartesian())

    # Empty location
    print("")
    print(exampleEmptyLocation)

    # Distances
    print("")
    print(computeDistance(exampleGeographicLocation1, exampleGeographicLocation2))
    print(computeDistance(exampleCartesianLocation1, exampleCartesianLocation2))
    print(computeDistance(exampleGeographicLocation1, exampleEmptyLocation))
    print("")



########
# Main #
########

if __name__ == '__main__':
    runLocationTests()
