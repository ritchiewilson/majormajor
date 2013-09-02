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


class Hazard:
    """
    When two branches diverge for multiple opperations, those opperations could
    be considered to be applied to two different documents. A hazard is created
    when one opperation is applied to a later opperation, and it is determined
    that the prev op needs to be altered when being applied to all future ops
    in order to have it seem to be applied to the same document. The hazard
    only holds on to relevant data, but does no calcualtions. It holds on to
    how or how much the past op's path, offset, and val need to be shifted in
    order to bring it in line for a future op's opperational transformation.

    """
    def __init__(self, base_op, conflict_op, path_shift=None,
                 offset_shift=0, val_shift=0):
        self.base_op = base_op
        self.conflict_op = conflict_op
        self.path_shift = path_shift
        self.offset_shift = offset_shift
        self.val_shift = val_shift

        self.base_cs = base_op.get_changeset()
        self.conflict_cs = conflict_op.get_changeset()

        self._is_path_hazard = not path_shift is None
        self._is_offset_hazard = path_shift is None

    def get_conflict_op_index(self):
        return self.conflict_op_index

    def get_base_op_index(self):
        return self.conflict_op_index

    def get_path_shift(self):
        return self.path_shift

    def get_offset_shift(self):
        return self.offset_shift

    def get_val_shift(self):
        return self.val_shift

    def is_string_hazard(self):
        return self._is_string_hazard

    def is_array_hazard(self):
        return self._is_array_hazard

    def is_path_hazard(self):
        return self._is_path_hazard

    def is_offset_hazard(self):
        return self._is_offset_hazard
