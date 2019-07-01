# -*- coding: utf-8 -*-
from .collection_base import CollectionBase


class Collection(CollectionBase):
    """
    `Collection` implements a collection of arbitrary items, including other objects.
       
    Its main purpose is to provide a base class for more useful collection classes.
    `CollectionBase` is a virtual base class for `Collection`, providing the functions
    for adding, accessing, and removing items from a collection.

    `Collection` offers a base for more specialized derived classes such as `SortedCollection`,
    `StringCollection`, and `ResourceCollection`.
       
    `Collection` inherits from `CollectionBase` the member functions for
    adding and deleting items, as well as several iterator routines that call
    a function for each item in the collection.
    """
    name = 'Collection'
