# -*- coding: utf-8 -*-
from .point import Point


class Rect:
    """
    A screen rectangular area.
       
    `Rect` is used to hold two coordinates on the screen, which usually specify
    the upper left corner and the lower right corner of views. Sometimes the
    second coordinate specify the size (extension) of the view. The two
    coordinates are named `topLeft` and `bottomRight`.       
    """
    __slots__ = ('topLeft', 'bottomRight')

    def __init__(self, ax, ay, bx, by):
        self.topLeft = Point(ax, ay)
        self.bottomRight = Point(bx, by)

    @property
    def width(self):
        return self.bottomRight.x - self.topLeft.x

    @property
    def height(self):
        return self.bottomRight.y - self.topLeft.y

    def move(self, deltaX, deltaY):
        """
        Moves the rectangle to a new position.
       
        The two parameters are added to the two old coordinates as delta
        values. Both parameters can be negative or positive.

        :param deltaX: Change in x
        :param deltaY: Change in y
        """
        self.topLeft += Point(deltaX, deltaY)
        self.bottomRight += Point(deltaX, deltaY)

    def grow(self, deltaX, deltaY):
        """
        Enlarges the rectangle by a specified value.
       
        Changes the size of the calling rectangle by subtracting `deltaX` from
        `topLeft.x`, adding `deltaX` to `bottomRight.x`, subtracting `deltaY` from
        `topLeft.y`, and adding `deltaY` to `bottomRight.y`.
       
        The left side is left-moved by `deltaX` units and the right side is
        right-moved by `deltaX` units. In a similar way the upper side is
        upper-moved by `deltaY` units and the bottom side is bottom-moved by `deltaY`
        units.

        :param deltaX: X distance
        :param deltaY: Y distance
        """
        self.topLeft -= Point(deltaX, deltaY)
        self.bottomRight += Point(deltaX, deltaY)

    def intersect(self, r: 'Rect'):
        """
        Calculates the intersection between this rectangle and the parameter
        rectangle.
       
        The resulting rectangle is the largest rectangle which contains both
        part of this rectangle and part of the parameter rectangle.

        :param r: Intersection rectangle
        """
        self.topLeft.x = max(self.topLeft.x, r.topLeft.x)
        self.topLeft.y = max(self.topLeft.y, r.topLeft.y)

        self.bottomRight.x = min(self.bottomRight.x, r.bottomRight.x)
        self.bottomRight.y = min(self.bottomRight.y, r.bottomRight.y)

    def union(self, r: 'Rect'):
        """
        Calculates the union between this rectangle and the `r` parameter
        rectangle.
       
        The resulting rectangle is the smallest rectangle which contains both
        this rectangle and the `r` rectangle.

        :param r: Union rectangle
        """
        self.topLeft.x = min(self.topLeft.x, r.topLeft.x)
        self.topLeft.y = min(self.topLeft.y, r.topLeft.y)

        self.bottomRight.x = max(self.bottomRight.x, r.bottomRight.x)
        self.bottomRight.y = max(self.bottomRight.y, r.bottomRight.y)

    def __contains__(self, point: Point) -> bool:
        """
        Is a Point `in` this `Rect`

        :param point: Point to check
        :return: True if the point is within the bounds of this rectangle
        """
        return self.topLeft.x <= point.x < self.bottomRight.x and self.topLeft.y <= point.y < self.bottomRight.y

    contains = __contains__

    def __eq__(self, other: 'Rect') -> bool:
        return self.topLeft == other.topLeft and self.bottomRight == other.bottomRight

    def __ne__(self, other: 'Rect'):
        return self.topLeft != other.topLeft or self.bottomRight != other.bottomRight

    def __repr__(self):
        return "({0.topLeft.x}, {0.topLeft.y}, {0.bottomRight.x}, {0.bottomRight.y})".format(self)

    def isEmpty(self) -> bool:
        """
        Checks if the rectangle is empty, i.e. if the first coordinate is
        greater than the second one.
       
        Empty means that `(topLeft.x >=  bottomRight.x or topLeft.y >= bottomRight.y)`.

        :return: True if this rectangle is empty
        """
        return self.topLeft.x >= self.bottomRight.x or self.topLeft.y >= self.bottomRight.y

    def copy(self) -> 'Rect':
        """
        Copy to a new `Rect`

        :return: A new `Rect` object
        """
        return Rect(self.topLeft.x, self.topLeft.y, self.bottomRight.x, self.bottomRight.y)
