# -*- coding: utf-8 -*-


class DataRecord:
    """
    Generic container
    """
    def __init__(self, **kwargs):
        self.value = None
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f' <DataRecord@{id(self):x}: {" ".join(f"{k} = {v}" for k, v in self.__dict__.items())}>'
