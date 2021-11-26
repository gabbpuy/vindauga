# -*- coding: utf-8 -*-
import gettext
import logging

logger = logging.getLogger(__name__)

gettext.install('vindauga')


class VindaugaObject:

    _registry = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        try:
            VindaugaObject._registry[cls.name] = cls
        except AttributeError:
            logger.info('A class has no name: %s', cls)

    def destroy(self, o):
        if o:
            o.shutdown()
        del o

    def shutdown(self):
        pass
