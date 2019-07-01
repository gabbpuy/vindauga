# -*- coding: utf-8 -*-
from vindauga.types.vindauga_object import VindaugaObject


class TopicDefinition(VindaugaObject):
    def __init__(self, topic, value):
        self.topic = topic
        self.value = value
        self.next = None
