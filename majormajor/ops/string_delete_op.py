
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


class StringDeleteOp(Op):
    def is_string_delete(self):
        return True

    def get_properties_shifted_by_hazards(self, cs):
        """
        Calculate how this op should be handled by a future op, accounting
        for any hazards that need to be applied. If this op's offset
        is further in the text than the hazard, then this offset is
        off by the size of hazard. If this op is the base of the
        hazard, then it is telling a future op to delete too much.
        """
        hazards = self.get_relevant_hazards(cs)
        past_t_val = self.t_val
        past_t_offset = self.t_offset
        for hazard in hazards:
            past_t_val += hazard.get_val_shift()
            past_t_offset += hazard.get_offset_shift()
        return self.t_path, past_t_offset, past_t_val

    def string_insert_transform(self, op):
        if self.t_path != op.t_path:
            return

        past_t_path, past_t_offset, past_t_val \
            = op.get_properties_shifted_by_hazards(self.get_changeset())

        hazard = False

        # if text was inserted into the deletion range, expand the
        # range to delete that text as well.
        if self.t_offset + self.t_val > past_t_offset \
                and self.t_offset < past_t_offset:
            self.t_val += len(op.t_val)
        # if the insertion comes before deletion range, shift
        # deletion range forward
        elif self.t_offset >= past_t_offset:
            self.t_offset += len(op.t_val)
        # Otherwise the past insertion has a higher index, so should be shifted
        # to come in line with current document.
        else:
            shift = self.t_val * -1
            hazard = Hazard(op, self, offset_shift=shift)

        return hazard

    def string_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return

        past_t_path, past_t_offset, past_t_val \
            = op.get_properties_shifted_by_hazards(self.get_changeset())

        hazard = self.transform_delete_by_previous_delete(op, past_t_offset,
                                                          past_t_val)

        return hazard
