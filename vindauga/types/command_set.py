# -*- coding: utf-8 -*-


class CommandSet:

    def __init__(self, tc=None):
        if not tc:
            self.cmds = set()
        else:
            self.cmds = tc.cmds.copy()

    def __contains__(self, cmd):
        return cmd in self.cmds

    has = __contains__

    def __iadd__(self, other):
        """
        Emables all commands in the `other` set (or a single command) to this command set

        :param other:
        :return:
        """
        self.enableCmd(other)
        return self

    def __isub__(self, other):
        """
        Removes all commands in the `other` set (or a single command) from this command set

        :param other:
        :return:
        """
        self.disableCmd(other)
        return self

    def __iand__(self, other):
        """
        Calculates the intersection of this and the `other` set

        :param other:
        :return:
        """
        self.cmds.intersection_update(other.cmds)
        return self

    def __ior__(self, other):
        """
        Calculates the union of this set and the `other` set

        :param other:
        :return:
        """
        self.cmds = self.cmds.union(other.cmds)
        return self

    def __and__(self, other):
        """
        Calculates the intersection of this set and the `other` set

        :param other:
        :return:
        """
        temp = CommandSet(self)
        temp &= other
        return temp

    def __or__(self, other):
        """
        Calculates the union of this set and the `other` set.

        :param other:
        :return:
        """
        temp = CommandSet(self)
        temp |= other
        return temp

    def __eq__(self, other):
        return self.cmds == other.cmds

    def __ne__(self, other):
        return self.cmds != other.cmds

    def __bool__(self):
        return len(self.cmds) != 0

    def __iter__(self):
        yield from self.cmds

    def __repr__(self):
        return 'CommandSet: {}'.format(self.cmds)

    def disableCmd(self, cmd):
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

    def enableCmd(self, cmd):
        """
        Adds cmd to the set
        :param cmd:
        :return:
        """
        if isinstance(cmd, CommandSet):
            self.cmds = self.cmds.union(cmd.cmds)
        else:
            self.cmds.add(cmd)

    def isEmpty(self):
        return not self.cmds

