
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
from op import Op


class ArrayDeleteOp(Op):
    def is_array_delete(self):
        return True

    def get_properties_shifted_by_hazards(self, cs):
        """
        Calculate how this op should be handled by a future op, accounting
        for any hazards that need to be applied.
        """
        #hazards = self.get_relevant_hazards(cs)
        return self.t_path, self.t_offset, self.t_val

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
                # otherwise the path may need to shift
        elif past_t_path == self.t_path[:len(past_t_path)]:
            # path may need to shift at one point
            if past_t_offset <= self.t_path[len(past_t_path)]:
                self.t_path[len(past_t_path)] += len(past_t_val)
        return False

    def array_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self.get_changeset())
        return False
