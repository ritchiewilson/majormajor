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

from ..hazards.hazard import Hazard
from .op import Op


class ArrayInsertOp(Op):
    def is_array_insert(self):
        return True

    def get_properties_shifted_by_hazards(self, op):
        """
        Calculate how this op should be handled by a future op, accounting
        for any hazards that need to be applied.
        """
        hazards = self.get_relevant_hazards(op)
        past_t_offset = self.t_offset
        for hazard in hazards:
            past_t_offset += hazard.get_offset_shift()
        return self.t_path, past_t_offset, self.t_val

    def string_insert_transform(self, op):
        """
        This is being transformed by a past String Insert. There is no way for
        a string insert to transform this op. This only needs to determine if a
        Hazard is created for the past Op.
        """
        hazard = self._get_path_hazard_for_past_op(op)
        return hazard

    def string_delete_transform(self, op):
        """
        This is being transformed by a past String Delete. There is no way for
        a string delete to transform this op. This only needs to determine if a
        Hazard is created for the past Op.
        """
        hazard = self._get_path_hazard_for_past_op(op)
        return hazard

    def _get_path_hazard_for_past_op(self, op):
        """
        Construct and return the path Hazard this Op creates when this is being
        transformed by the given Op. If no Hazard is needed, return False.

        :param op: Previous :class:`Op` this op is being transformed by
        :returns: path :class:`Hazard` or False
        """
        hazard = False
        past_t_path = op.past_t_path[:]

        if len(past_t_path) < len(self.t_path):
            pass
        elif self.t_path == past_t_path[:len(self.t_path)]:
            index = past_t_path[len(self.t_path)]
            if index >= self.t_offset:
                past_t_path[len(self.t_path)] = index + len(self.t_val)
                hazard = Hazard(op, self, path_shift=past_t_path)

        return hazard

    def array_insert_transform(self, op):
        """
        This op is being transformed by a previously unknown array insert. The
        result could be nothing, or some peice of the path must be shifted, or
        the offset must be shifted.
        """
        hazard = False
        past_t_path, past_t_offset, past_t_val = \
            op.past_t_path, op.past_t_offset, op.past_t_val

        # when this path is shorter than the old one, nothing needs to be done.
        if len(self.t_path) < len(past_t_path):
            pass

        # when the paths are exactly equal, this offset may need to shift up
        elif past_t_path == self.t_path:
            hazard = self.transform_insert_by_previous_insert(op,
                                                              past_t_offset,
                                                              past_t_val)
        # otherwise the path may need to shift
        elif past_t_path == self.t_path[:len(past_t_path)]:
            if past_t_offset <= self.t_path[len(past_t_path)]:
                self.t_path[len(past_t_path)] += len(past_t_val)
        return hazard

    def array_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation did an
        array deletion. If this op happens within an element that was deleted,
        this becomes a noop. If they have the same path then this could be a
        noop if it is is the deletion range, or the offset needs to reduce if
        it is past the delete range. Lastly, it could just mean the path needs
        to shift at one point.
        """
        hazard = False
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self)

        # when this path is shorter than the old one, nothing needs to be done.
        if len(self.t_path) < len(past_t_path):
            pass
        elif not past_t_path == self.t_path[:len(past_t_path)]:
            pass
        elif len(past_t_path) < len(self.t_path):
            # this op could have been within a deleted element
            delete_range = xrange(past_t_offset, past_t_offset + past_t_val)
            if self.t_path[len(past_t_path)] in delete_range:
                self.noop = True
            # or the path needs to shift
            elif self.t_path[len(past_t_path)] > past_t_offset:
                self.t_path[len(past_t_path)] -= past_t_val
        # lastly, if they have the same path, offsets may need to shift
        elif past_t_path == self.t_path:
            hazard = self.transform_insert_by_previous_delete(op,
                                                              past_t_offset,
                                                              past_t_val)
        return hazard
