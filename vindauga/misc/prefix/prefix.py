# -*- coding: utf-8 -*-
"""
Unit prefix library for units for powers of 10. Handles multiplication and division and
returns super scripts for attaching to displays.
"""
import math


class MetaPrefix(type):
    powerIndex = {}
    prefixIndex = {}

    def __call__(cls, *args, **kwargs):
        obj = super(MetaPrefix, cls).__call__(*args, **kwargs)
        MetaPrefix.powerIndex[obj.power] = obj
        MetaPrefix.prefixIndex[obj.prefix] = obj
        return obj


def hasPrefix(prefix):
    """
    Is the prefix in the cache?
    :param prefix: prefix
    :return: presence of prefix
    """
    return prefix in MetaPrefix.prefixIndex


def hasPower(power):
    """
    Is this power in the cache?
    :param power: Power
    :return: presence of power
    """
    return power in MetaPrefix.powerIndex


def getPower(power):
    """
    Get the cached power index
    :param power:
    :return: Cached Power
    """
    return MetaPrefix.powerIndex[power]


def getPrefix(prefix):
    """
    Get the cached prefix object
    :param prefix: prefix
    :return: Cached prefix
    """
    return MetaPrefix.prefixIndex[prefix]


class Prefix(object, metaclass=MetaPrefix):
    """
    A SI power of 10 prefix.

    :param prefix: the abbreviated version
    :param name: the long form
    :param power: the power of 10 this refers to
    """
    supers = ['⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹']

    __slots__ = ("prefix", "name", "power", "fmt")

    def __init__(self, prefix, name, power):
        self.prefix = prefix
        self.name = name
        self.power = power
        self.fmt = self.generateFormat(power)

    def generateFormat(self, power):
        """
        Generate the format

        :param power: Power raised to
        :return: Formatted unicode string
        """
        # Prepare a pretty string
        pPrefix = ''
        if power < 0:
            pPrefix = '⁻'
            power = -power
        if power == 0:
            return ''
        elif power < 10:
            return '10{0}{1}'.format(pPrefix, self.supers[power])
        elif power < 100:
            t, u = divmod(power, 10)
            return '10{0}{1}{2}'.format(pPrefix, self.supers[t], self.supers[u])
        else:
            return '10^{0}{1}'.format(pPrefix, power)

    def __repr__(self):
        """
        Returns a long representation of this item
        """
        return self.fmt.encode('utf-8')

    def __str__(self):
        """
        Unicode version
        """
        return self.prefix

    def __rmul__(self, o):
        """
        Return a scalar multiplied by us.
        e.g. 5 * kilo returns 5000
        """
        return o * (10 ** self.power)

    def __mul__(self, o):
        """
        Return a scalar multiplied by us.
        e.g. 5 * kilo returns 5000
        """
        return o * (10 ** self.power)

    def __rdiv__(self, o):
        """
        Return a scalar divided by us.
        e.g. 5000 / kilo returns 5
        """
        return float(o) / (10 ** self.power)


def closestPrefix(i):
    """
    Reduce a number to a multiplier and a prefix.

    e.g `closestPrefix(1000)` returns (1.0, kilo)
    `closestPrefix(1024)` returns (1.024, kilo)

    :param i: the number to index
    :returns: a (coefficient, :mod:`prefix`) tuple.
    """
    if i == 0:
        return 0, getPower(0)

    coefficient = abs(float(i))

    mult = 1
    if i < 0:
        mult = -1

    exponent = int(math.floor(math.log(coefficient, 10) + 0.5))
    coefficient /= 10 ** exponent

    indices = sorted(MetaPrefix.powerIndex.keys())

    for j, i in enumerate(indices):
        if i >= exponent:
            if i > exponent:
                i = indices[j - 1]
                delta = exponent - i
                coefficient *= 10 ** delta
            break
    exponent = getPower(i)
    return coefficient * mult, exponent
