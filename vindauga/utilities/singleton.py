# -*- coding: utf-8 -*-


class Singleton(type):
    def __init__(cls, name, bases, attrs, **_kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
