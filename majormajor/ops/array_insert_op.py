
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


class ArrayInsertOp(Op):
    def is_array_insert(self):
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
        This op is being transformed by a previously unknown array insert. The
        result could be nothing, or some peice of the path must be shifted, or
        the offset must be shifted.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self.get_changeset())

        # when this path is shorter than the old one, nothing needs to be done.
        if len(self.t_path) < len(past_t_path):
            pass

        # when the paths are exactly equal, this offset may need to shift up
        elif past_t_path == self.t_path:
            if past_t_offset <= self.t_offset:
                self.t_offset += len(past_t_val)
        # otherwise the path may need to shift
        elif past_t_path == self.t_path[:len(past_t_path)]:
            if past_t_offset <= self.t_path[len(past_t_path)]:
                self.t_path[len(past_t_path)] += len(past_t_val)
        return False

    def array_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation did an
        array deletion. If this op happens within an element that was deleted,
        this becomes a noop. If they have the same path then this could be a
        noop if it is is the deletion range, or the offset needs to reduce if
        it is past the delete range. Lastly, it could just mean the path needs
        to shift at one point.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self.get_changeset())

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
            # this op could have been in delete range (avoid deleting if at all
            # possible)
            start = past_t_offset + 1
            stop = past_t_offset + past_t_val
            delete_range = xrange(start, stop)
            if self.t_offset in delete_range:
                self.t_offset = past_t_offset
                self.t_val = []
                self.noop = True
            elif self.t_offset > past_t_offset:
                self.t_offset -= past_t_val

        return False
