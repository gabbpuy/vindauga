# -*- coding: utf-8 -*-
from typing import Union, List, Optional
from .color_item import ColorItem


class ColorGroup:
    """
    The interrelated classes `ColorItem`, `ColorGroup`, `ColorSelector`,
    `MonoSelector`, `ColorDisplay`, `ColorGroupList`,
    `ColorItemList` and `ColorDialog` provide viewers and dialog boxes
    from which the user can select and change the color assignments from
    available palettes with immediate effect on the screen.
       
    The `ColorGroup` class defines a list of `ColorItem` objects. Each member
    of a color group consists of a set of color names and their associated color codes.
    """
    def __init__(self, name: str):
        self.items: List[ColorItem] = []
        self.groups: List[ColorGroup] = [self]
        self.name = name
        self.index = 0

    def __add__(self, other: Union['ColorGroup', ColorItem]) -> Optional[Union['ColorGroup', ColorItem]]:
        if isinstance(other, ColorGroup):
            return self.__addColorGroup(other)
        elif isinstance(other, ColorItem):
            return self.__addColorItem(other)
        return None

    add = __add__

    def __addColorGroup(self, other: 'ColorGroup') -> 'ColorGroup':
        self.groups.append(other)
        return self

    def __addColorItem(self, other: ColorItem) -> 'ColorGroup':
        self.groups[-1].items.append(other)
        return self

    def __len__(self) -> int:
        return len(self.groups)
