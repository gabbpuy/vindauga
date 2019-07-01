# -*- coding: utf-8 -*-
import gettext
import logging

logger = logging.getLogger('vindauga.types.vindauga_object')

gettext.install('vindauga')


class VindaugaObject:

    _registry = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        try:
            VindaugaObject._registry[cls.name] = cls
            logger.info('New Type: %s', cls.name)
        except AttributeError:
            logger.info('A class has no name: %s', cls)
            pass

    @staticmethod
    def destroy(o):
        if o:
            o.shutdown()
        del o

    def shutdown(self):
        pass
