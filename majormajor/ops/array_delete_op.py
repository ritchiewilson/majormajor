
# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ..hazards.hazard import Hazard
from .op import Op


class ArrayDeleteOp(Op):
    def is_array_delete(self):
        return True

    def get_properties_shifted_by_hazards(self, cs):
        """
        Calculate how this op should be handled by a future op, accounting
        for any hazards that need to be applied.
        """
        hazards = self.get_relevant_hazards(cs)
        past_t_val = self.t_val
        past_t_offset = self.t_offset
        for hazard in hazards:
            past_t_val += hazard.get_val_shift()
            past_t_offset += hazard.get_offset_shift()
        return self.t_path, past_t_offset, past_t_val

    def array_insert_transform(self, op):
        """
        A Previously unknown op did an array insert. If their paths do not
        cross, do nothing. If the two ops have identical paths, this delete's
        offset may need to be shifted forward to accomidate. It could also need
        to expand to delete the elements previously inserted. If their path's
        cross, this delete's path may need to be shifted at one point.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self.get_changeset())

        hazard = False
        # if this path is smaller than the old one, there's no conflict
        if len(self.t_path) < len(past_t_path):
            pass
        elif past_t_path == self.t_path:
            if past_t_offset <= self.t_offset:
                #shift out of the way of a previous insertion
                self.t_offset += len(past_t_val)
            elif past_t_offset < self.t_offset + self.t_val:
                # expand deletion to include past insertion
                self.t_val += len(past_t_val)
            else:
                shift = self.t_val * -1
                hazard = Hazard(op, self, offset_shift=shift)
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
            op.get_properties_shifted_by_hazards(self.get_changeset())

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
            hazard = self.shift_from_overlaping_delete_ranges(op,
                                                              past_t_offset,
                                                              past_t_val)
        return hazard
