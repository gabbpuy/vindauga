# -*- coding: utf-8 -*-
import gettext
import logging

logger = logging.getLogger(__name__)

gettext.install('vindauga')


class VindaugaObject:

    _registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        try:
            if name := getattr(cls, 'name', None):
                VindaugaObject._registry[name] = cls
        except AttributeError:
            logger.info('A class has no name: %s', cls)

    def destroy(self, o):
        if o:
            o.shutdown()
        del o

    def shutdown(self):
        pass
