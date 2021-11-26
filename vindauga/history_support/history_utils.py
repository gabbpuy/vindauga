# -*- coding: utf-8 -*-
import logging
from collections import defaultdict


logger = logging.getLogger(__name__)

histories = defaultdict(list)


def historyAdd(historyId, historyString):
    if not historyString:
        return

    history = histories[historyId]
    try:
        history.remove(historyString)
    except ValueError:
        pass

    if historyString not in history:
        history.append(historyString)


def historyCount(historyId):
    history = histories[historyId]
    return len(history)


def historyStr(historyId, index):
    history = histories[historyId]
    if index > len(history):
        return ''
    return history[index]


def getHistory(historyId):
    return histories[historyId]


def initHistory():
    global histories
    histories = defaultdict(list)


def doneHistory():
    global histories
    del histories
