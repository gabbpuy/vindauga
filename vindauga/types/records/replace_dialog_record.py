# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class ReplaceDialogRecord:
    find: str
    replace: str
    options: int
