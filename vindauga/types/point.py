# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from functools import total_ordering
from typing import Union


@total_ordering
@dataclass
class Point:
    """
    Point class
    """
    x: int = 0
    y: int = 0

    def __iter__(self):
        yield self.x
        yield self.y

    def __sub__(self, other: Point) -> Point:
        x = self.x - other.x
        y = self.y - other.y
        return Point(x, y)

    def __add__(self, other: Point) -> Point:
        x = self.x + other.x
        y = self.y + other.y
        return Point(x, y)

    def __eq__(self, other: Union[Point, tuple, list]) -> bool:
        if isinstance(other, (Point,)):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, (tuple, list)):
            return self.x == other[0] and self.y == other[1]

    def __ne__(self, other: Union[Point, tuple, list]) -> bool:
        if isinstance(other, (Point,)):
            return self.x != other.x or self.y != other.y
        elif isinstance(other, (tuple, list)):
            return self.x != other[0] or self.y != other[1]

    def __lt__(self, other: Point) -> bool:
        # I am closer to 0, 0 than the other
        return abs(self.x) < abs(other.x) or abs(self.y) < abs(other.y)

    def __iadd__(self, other: Point) -> Point:
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other: Point) -> Point:
        self.x -= other.x
        self.y -= other.y
        return self

    def __repr__(self):
        return f'<Point({self.x}, {self.y})>'
