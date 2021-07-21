###########
# Modules #
###########

# Project modules
from Tools.time import *



#########################
# Class IntegerInterval #
#########################

class IntegerInterval:

    lowerBound = None
    upperBound = None

    def __init__(self, lowerBound = None, upperBound = None):
        self.lowerBound = lowerBound
        self.upperBound = upperBound

    def isEmpty(self):
        return self.lowerBound is None

    def copy(self):
        return IntegerInterval(
            lowerBound = self.lowerBound,
            upperBound = self.upperBound
        )

    def contains(self, x):
        return self.lowerBound <= x and x <= self.upperBound

    def containsAll(self, xs):
        for x in xs:
            if not(self.contains(x)):
                return False
        return True

    def computeSubstractionBy(self, interval):
        intersection = self.computeIntersectionWith(interval)
        if intersection.isEmpty():
            return self.copy()
        else:
            if intersection.lowerBound == self.lowerBound:
                if intersection.upperBound == self.upperBound:
                    return IntegerInterval()
                else:
                    return IntegerInterval(
                        lowerBound = intersection.upperBound,
                        upperBound = self.upperBound
                    )
            else :
                if intersection.upperBound == self.upperBound:
                    return IntegerInterval(
                        lowerBound = self.lowerBound,
                        upperBound = intersection.lowerBound
                    )
                else:
                    substraction = IntervalUnion()
                    substraction.add(
                        IntegerInterval(
                            lowerBound = self.lowerBound,
                            upperBound = intersection.lowerBound
                        )
                    )
                    substraction.add(
                        IntegerInterval(
                            lowerBound = intersection.upperBound,
                            upperBound = self.upperBound
                        )
                    )
                    return substraction

    def computeIntersectionWith(self, interval):
        lowerBound = max(self.lowerBound, interval.lowerBound)
        upperBound = min(self.upperBound, interval.upperBound)
        intersection = IntegerInterval()
        if upperBound - lowerBound >= 0:
            intersection.lowerBound = lowerBound
            intersection.upperBound = upperBound
        return intersection

    def toTimeString(self):
        if self.isEmpty():
            return "Ø"
        else:
            return f"[{convert_nb_minutes_to_time_string(self.lowerBound)};{convert_nb_minutes_to_time_string(self.upperBound)}]"

    def __repr__(self):
        if self.isEmpty():
            return "Ø"
        else:
            return f"[{self.lowerBound};{self.upperBound}]"



#######################
# Class IntervalUnion #
#######################

class IntervalUnion:

    nbIntervals = 0
    intervals = None

    def __init__(self, interval = None):
        if interval != None and not(interval.isEmpty()):
            self.nbIntervals = 1
            self.intervals = [interval]

    def isEmpty(self):
        return self.nbIntervals == 0

    def reset(self):
        self.nbIntervals = 0
        self.intervals = None

    def __getitem__(self, item):
        return self.intervals[item]

    def addInterval(self, interval, copyWhenAdding = False):
        if not(interval.isEmpty()):
            if self.nbIntervals == 0:
                self.intervals = []
            if copyWhenAdding:
                self.intervals.append(interval.copy())
            else:
                self.intervals.append(interval)
            self.nbIntervals += 1

    def addUnion(self, union, copyWhenAdding = False):
        if not(union.isEmpty()):
            if self.nbIntervals == 0:
                self.intervals = []
            for interval in union:
                self.nbIntervals += 1
                if copyWhenAdding:
                    self.intervals.append(interval.copy())
                else:
                    self.intervals.append(interval)

    def add(self, set, copyWhenAdding = False):
        if type(set) == IntegerInterval:
            self.addInterval(set, copyWhenAdding)
        if type(set) == IntervalUnion:
            self.addUnion(set, copyWhenAdding)

    def computeSubstractionBy(self, interval):
        substraction = IntervalUnion()
        for intervalBis in self.intervals:
            substraction.add(intervalBis.computeSubstractionBy(interval))
        return substraction

    def computeIntersectionWith(self, interval):
        intersection = IntervalUnion()
        if not(self.isEmpty()):
            for intervalBis in self.intervals:
                intersection.addInterval(
                    intervalBis.computeIntersectionWith(interval)
                )
        return intersection

    def toTimeString(self):
        if self.isEmpty():
            return "Ø"
        else:
            stringRepresentation = self.intervals[0].toTimeString()
            for interval in self.intervals[1:]:
                stringRepresentation += " U " + interval.toTimeString()
            return stringRepresentation

    def __repr__(self):
        if self.isEmpty():
            return "Ø"
        else:
            stringRepresentation = self.intervals[0].__repr__()
            for interval in self.intervals[1:]:
                stringRepresentation += " U " + str(interval)
            return stringRepresentation
