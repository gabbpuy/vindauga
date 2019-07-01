# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class ColorItem:
    """
    Stores information about a color item. `ColorItem` defines a list of
    color names and indexes.
       
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`, `ColorItemList` and
    `ColorDialog` provide viewers and dialog boxes from which the user can
    select and change the color assignments from available palettes with
    immediate effect on the screen.
    """
    name: str
    index: int
