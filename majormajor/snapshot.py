# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import copy


class Snapshot:
    def __init__(self):
        self.snapshot = {}

    def get_snapshot(self):
        """
        Returns a shallow copy of the document's snapshot.
        """
        return self.snapshot

    def get_snapshot_copy(self):
        """
        Returns a deep copy of the document's snapshot.
        """
        return copy.deepcopy(self.snapshot)

    def set_snapshot(self, snapshot):
        """
        """
        self.snapshot = snapshot

    def contains_path(self, path):
        """
        Checks if the given path is valid in this document's snapshot.
        """
        node = self.snapshot
        for i in path:
            if isinstance(i, str):
                if not isinstance(node, dict):
                    return False
                if not i in node:
                    return False
            elif isinstance(i, int):
                if not isinstance(node, list):
                    return False
                if i >= len(node):
                    return False
            node = node[i]
        return True

    def get_node(self, path):
        node = self.snapshot
        if len(path) != 0:
            for i in path[:-1]:
                node = node[i]
        return node

    def get_value(self, path):
        if len(path) == 0:
            return self.snapshot
        return self.get_node(path)[path[-1]]

    def apply_op(self, op):
        if not self.contains_path(op.t_path):
            return "ERROR!"

        if op.is_noop():
            return

        if op.is_string_move():
            self.string_move(op)
            return
        func_name = self.json_opperations[op.action]
        func = getattr(self, func_name)
        if len(op.t_path) == 0:
            self.snapshot = func(op)
        else:
            node = self.get_node(op.t_path)
            node[op.t_path[-1]] = func(op)

    # JSON Opperation - wholesale replacing value at a given path
    def set_value(self, op):
        return copy.deepcopy(op.t_val)

    # JSON Opperation - Flip the value of the boolean at the given path
    def boolean_negation(self, op):
        cur = self.get_value(op.t_path)
        return False if cur else True

    # JSON Opperation - Add some constant value to the number at the given path
    def number_add(self, op):
        return self.get_value(op.t_path) + op.val

    # JSON Opperation - Insert characters into a string at the given
    # path, and at the given offset within that string.
    def string_insert(self, op):
        cur = self.get_value(op.t_path)
        return  cur[:op.t_offset] + op.t_val + cur[op.t_offset:]

    # JSON Opperation - Delete given number of characters from a
    # string at the given path, and at the given offset within that
    # string.
    def string_delete(self, op):
        cur = self.get_value(op.t_path)
        return cur[:op.t_offset] + cur[op.t_offset + op.t_val:]

    def string_move(self, op):
        """
        A range of text is moved from one position in a document to another.
        The text can move within a string element, or from one string element
        to another.
        """
        cur = self.get_value(op.t_path)
        txt = cur[op.t_offset:op.t_offset + op.t_val]  # text to be moved.
        remaining_txt = cur[:op.t_offset] + cur[op.t_offset + op.t_val:]
        # first delete text where it was
        if op.t_path == []:
            self.snapshot = remaining_txt
        else:
            node = self.get_node(op.t_path)
            node[op.t_path[-1]] = remaining_txt
        # then insert it at the destination
        dest_v = self.get_value(op.t_dest_path)
        new_txt = dest_v[:op.t_dest_offset] + txt + dest_v[op.t_dest_offset:]
        if op.t_dest_path == []:
            self.snapshot = new_txt
        else:
            node = self.get_node(op.t_dest_path)
            node[op.t_dest_path[-1]] = new_txt

    def array_insert(self, op):
        cur = self.get_value(op.t_path)
        r = cur[:op.t_offset]
        r.extend(op.t_val)
        r.extend(cur[op.t_offset:])
        return r

    def array_delete(self, op):
        cur = self.get_value(op.t_path)
        r = cur[:op.t_offset]
        r.extend(cur[op.t_offset + op.t_val:])
        return r

    def array_move(self, op):
        cur = self.get_value(op.path)
        item = cur.pop(op.offset)
        r = cur[:op.val]
        r.append(item)
        r.extend(cur[op.val:])
        return r

    def object_insert(self, op):
        cur = self.get_value(op.t_path)
        cur[op.t_offset]  = op.t_val
        return cur

    def object_delete(self, op):
        cur = self.get_value(op.t_path)
        cur.pop(op.t_offset)
        return cur

    json_opperations = {
        'set': 'set_value',
        'bn': 'boolean_negation',
        'na': 'number_add',
        'si': 'string_insert',
        'sd': 'string_delete',
        'ai': 'array_insert',
        'ad': 'array_delete',
        'am': 'array_move',
        'oi': 'object_insert',
        'od': 'object_delete'
    }
