# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class FindDialogRecord:
    find: str
    options: int
