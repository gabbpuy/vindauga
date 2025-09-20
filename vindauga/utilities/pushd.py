# -*- coding: utf-8 -*-
from contextlib import contextmanager
import os


@contextmanager
def pushd(path):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)
