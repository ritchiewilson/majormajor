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


class ArrayDeleteOp(Op):
    def is_array_delete(self):
        return True

    def set_value_to_nil(self):
        self.t_val = 0

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
        Construct and return the Hazard this Op creates when this is being
        transformed by the given Op. If no Hazard is needed, return False.

        If the past op is beyond the delete range, a path hazard is created. If
        the past op happens within the delete range, the past op gets a noop
        hazard.

        :param op: Previous :class:`Op` this op is being transformed by
        :returns: :class:`Hazard` or False
        """
        hazard = False
        past_t_path = op.past_t_path[:]

        # when this path is shorter, there are no potential Hazards
        if len(past_t_path) < len(self.t_path):
            pass
        elif self.t_path == past_t_path[:len(self.t_path)]:
            index = past_t_path[len(self.t_path)]
            if index >= self.t_offset + self.t_val:
                # the past op was beyond the delete range, so the path shifts
                past_t_path[len(self.t_path)] = index - self.t_val
                hazard = Hazard(op, self, path_shift=past_t_path)
            elif index >= self.t_offset:
                # the past op was in the delete range, so does not need to be
                # applied anymore.
                hazard = Hazard(op, self, noop_shift=True)
        return hazard

    def array_insert_transform(self, op):
        """
        A Previously unknown op did an array insert. If their paths do not
        cross, do nothing. If the two ops have identical paths, this delete's
        offset may need to be shifted forward to accomidate. It could also need
        to expand to delete the elements previously inserted. If their path's
        cross, this delete's path may need to be shifted at one point.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.past_t_path, op.past_t_offset, op.past_t_val

        hazard = False
        # if this path is smaller than the old one, there's no conflict
        if len(self.t_path) < len(past_t_path):
            pass
        elif past_t_path == self.t_path:
            hazard = self.transform_delete_by_previous_insert(op,
                                                              past_t_offset,
                                                              past_t_val)
        elif past_t_path == self.t_path[:len(past_t_path)]:
            # path may need to shift at one point
            if past_t_offset <= self.t_path[len(past_t_path)]:
                self.t_path[len(past_t_path)] += len(past_t_val)
        return hazard

    def array_delete_transform(self, op):
        """
        Transform this op when a previously unknown opperation did a string
        deletion. If the past delete happened partially along this path, this
        path may need to shift back at one point, or this whole op becomes a
        noop, or nothing happens. When the two delete ops happen in the same
        array, only their offsets and vals needs to be compared for possible
        overlapping delete ranges (just like string deletes).
        """
        past_t_path, past_t_offset, past_t_val = \
            op.past_t_path, op.past_t_offset, op.past_t_val

        hazard = False
        # if this path is smaller than the old one, there's no conflict
        if len(self.t_path) < len(past_t_path):
            pass
        # if they are along the same path, there may need to be a
        # transformation, shift path or noop
        elif len(self.t_path) > len(past_t_path) and \
                past_t_path == self.t_path[:len(past_t_path)]:
            delete_range = xrange(past_t_offset, past_t_offset + past_t_val)
            if self.t_path[len(past_t_path)] in delete_range:
                # when one of the elements in this path was previously deleted,
                # this becomes a noop
                self.noop = True
            elif self.t_path[len(past_t_path)] > past_t_offset:
                # along this path was an array that had elements deleted and
                # that point in the path needs to shift back.
                self.t_path[len(past_t_path)] -= past_t_val
        elif self.t_path == past_t_path:
            # if the paths are identical, only delete ranges need to be
            # considered, just like overlapping string deletes.
            hazard = self.transform_delete_by_previous_delete(op,
                                                              past_t_offset,
                                                              past_t_val)
        return hazard
