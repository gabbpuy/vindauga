# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class CollectionBase(list):

    def __init__(self, iterable=()):
        super().__init__(iterable)

    def indexOf(self, item):
        try:
            return self.index(item)
        except ValueError:
            return -1

    def pack(self):
        pass

    def setLimit(self, limit):
        pass

    def firstThat(self, testFunc, *args):
        """
        Return the first item that passes the 'testFunc'

        :param testFunc: Function to call
        :param args: Args to pass to `testFunc`
        :return: First Item or None
        """
        if any(testFunc((item := _item), *args) for _item in self):
            return item
        return None

    def lastThat(self, testFunc, *args):
        """
        Return the last item that passes the 'testFunc'

        :param testFunc: Function to call
        :param args: Args to pass to `testFunc`
        :return: First Item or None
        """
        if any(testFunc((item := _item), *args) for _item in reversed(self)):
            return item
        return None

    def forEach(self, action, *args):
        """
        Basically `map` that catches exceptions mid-stream and doesn't collect results

        :param action: Action to apply to each
        :param args: Args to pass to `action`
        """
        for item in self:
            try:
                action(item, *args)
            except:
                logger.exception('forEach(): %s(%s,%s)', action, item, args)

    def search(self, key):
        try:
            return self.index(key)
        except ValueError:
            return len(self) + 1
