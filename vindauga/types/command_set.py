# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Union


class CommandSet:

    def __init__(self, tc: Optional[CommandSet] = None):
        if not tc:
            self.cmds = set()
        else:
            self.cmds = set(tc.cmds)

    def __contains__(self, cmd) -> bool:
        return cmd in self.cmds

    has = __contains__

    def __iadd__(self, other: CommandSet) -> CommandSet:
        """
        Enables all commands in the `other` set (or a single command) to this command set

        :param other:
        :return:
        """
        self.enableCmd(other)
        return self

    def __isub__(self, other: CommandSet) -> CommandSet:
        """
        Removes all commands in the `other` set (or a single command) from this command set

        :param other:
        :return:
        """
        self.disableCmd(other)
        return self

    def __iand__(self, other: CommandSet) -> CommandSet:
        """
        Calculates the intersection of this and the `other` set

        :param other:
        :return:
        """
        self.cmds.intersection_update(other.cmds)
        return self

    def __ior__(self, other: CommandSet) -> CommandSet:
        """
        Calculates the union of this set and the `other` set

        :param other:
        :return:
        """
        self.cmds = self.cmds.union(other.cmds)
        return self

    def __and__(self, other: CommandSet) -> CommandSet:
        """
        Calculates the intersection of this set and the `other` set

        :param other:
        :return:
        """
        temp = CommandSet(self)
        temp &= other
        return temp

    def __or__(self, other: CommandSet) -> CommandSet:
        """
        Calculates the union of this set and the `other` set.

        :param other:
        :return:
        """
        temp = CommandSet(self)
        temp |= other
        return temp

    def __eq__(self, other: CommandSet) -> bool:
        return self.cmds == other.cmds

    def __ne__(self, other: CommandSet) -> bool:
        return self.cmds != other.cmds

    def __bool__(self) -> bool:
        return len(self.cmds) != 0

    def __iter__(self):
        yield from self.cmds

    def __repr__(self):
        return f'CommandSet: {self.cmds}'

    def disableCmd(self, cmd: Union[int,  CommandSet]):
        """
        Removes cmd from the set
        :param cmd:
        :return:
        """
        if isinstance(cmd, CommandSet):
            self.cmds.difference_update(cmd.cmds)
        else:
            try:
                self.cmds.remove(cmd)
            except KeyError:
                pass

    def enableCmd(self, cmd: Union[int, CommandSet]):
        """
        Adds cmd to the set
        :param cmd:
        :return:
        """
        if isinstance(cmd, CommandSet):
            self.cmds = self.cmds.union(cmd.cmds)
        else:
            self.cmds.add(cmd)

    def isEmpty(self) -> bool:
        return not self.cmds
