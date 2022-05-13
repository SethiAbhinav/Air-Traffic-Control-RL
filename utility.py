import math

class Utility:
    # Returns the Euclidean distance between two points in 2D space.
    @staticmethod
    def locDist(loc1, loc2):
        return math.sqrt( Utility.locDistSq(loc1, loc2) )

    @staticmethod
    def locDistSq(loc1, loc2):
        dx = loc1[0] - loc2[0]
        dy = loc1[1] - loc2[1]
        return ( (dx ** 2) + (dy ** 2) )

    @staticmethod
    def getPointLineIntersect(p1, p2, p3):
        return (None, 0)