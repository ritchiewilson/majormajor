
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
from string_transform_op import StringTransformOp
        
class StringDeleteOp(StringTransformOp):
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
        hazards = self.hazards
        if not cs is None:
            hazards = [h for h in self.hazards
                       if cs is h.conflict_cs or
                       cs.has_ancestor(h.conflict_cs)]
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

        hazard = False

        srs = self.t_offset # self range start
        sre = self.t_offset + self.t_val # self range end
        oprs = past_t_offset # prev op range start
        opre = past_t_offset + past_t_val # prev op range end
        # there are six ways two delete ranges can overlap and
        # each one is a different case.

        # case 1
        #                |-- prev op --|
        # |-- self --|
        if sre <= oprs:
            shift = self.t_val * -1
            hazard = Hazard(op, self, offset_shift=shift)
        # case 2
        #   |-- prev op --|
        #                   |-- self --|
        elif srs >= opre:
            self.t_offset -= past_t_val
        # case 3
        #   |-- prev op --|
        #           |-- self --|
        elif srs >= oprs and sre > opre:
            overlap = srs - opre
            hazard = Hazard(op, self, val_shift=overlap)
            self.t_val += (self.t_offset - (past_t_offset + past_t_val))
            self.t_val = max(0, self.t_val)
            self.t_offset = past_t_offset
        # case 4
        #   |--- prev op ---|
        #     |-- self --|
        elif srs >= oprs and sre <= opre:
            overlap = srs - sre
            hazard = Hazard(op, self, val_shift=overlap)
            self.t_offset = past_t_offset
            self.t_val = 0
        # case 5
        #     |-- prev op --|
        #   |----- self ------|
        elif sre >= opre:
            overlap = past_t_val * -1
            hazard = Hazard(op, self, val_shift=overlap)
            self.t_val -= past_t_val
        # case 6
        #      |-- prev op --|
        #   |-- self --|
        else:
            overlap = oprs - sre
            offset_shift = srs - oprs
            hazard = Hazard(op, self, offset_shift=offset_shift,
                            val_shift=overlap)
            self.t_val = past_t_offset - self.t_offset

        return hazard
