# -*- coding: utf-8 -*-
from typing import Union


def clamp(val: Union[int, float], minVal: Union[int, float], maxVal: Union[int, float]) -> Union[int, float]:
    """
    Clamp a value between minVal and maxVal

    :param val: Incoming value
    :param minVal: bottom of range
    :param maxVal: top of range
    :return: clamped value
    """
    return max(minVal, min(val, maxVal))