
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
    def is_string_transform(self):
        return True

    def is_string_delete(self):
        return True
    
    def string_insert_transform(self, op, hazards):
        if self.t_path != op.t_path:
            return

        past_t_path, past_t_offset, past_t_val \
            = self.shift_past_op_by_hazards(op, hazards)

        # if text was inserted into the deletion range, expand the
        # range to delete that text as well.
        if self.t_offset + self.t_val > past_t_offset and self.t_offset < past_t_offset:
            self.t_val += len(op.t_val)
        # if the insertion comes before deletion range, shift
        # deletion range forward
        elif self.t_offset >= past_t_offset:
            self.t_offset += len(op.t_val)

    def string_delete_transform(self, op, hazards):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return


        past_t_path, past_t_offset, past_t_val \
            = self.shift_past_op_by_hazards(op, hazards)

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
            pass
        # case 2
        #   |-- prev op --|
        #                   |-- self --|
        elif srs >= opre:
            self.t_offset -= past_t_val
        # case 3
        #   |-- prev op --|
        #           |-- self --|
        elif srs >= oprs and sre > opre:
            hazard = Hazard(op, self, past_t_offset, past_t_val)
            self.t_val += (self.t_offset - (past_t_offset + past_t_val))
            self.t_val = max(0, self.t_val)
            self.t_offset = past_t_offset
        # case 4
        #   |--- prev op ---|
        #     |-- self --|
        elif srs >= oprs and sre <= opre:
            hazard = Hazard(op, self, past_t_offset, past_t_val)
            self.t_offset = past_t_offset
            self.t_val = 0
        # case 5
        #     |-- prev op --|
        #   |----- self ------|
        elif sre >= opre:
            hazard = Hazard(op, self, past_t_offset, past_t_val)
            self.t_val -= past_t_val
        # case 6
        #      |-- prev op --|
        #   |-- self --|
        else:
            hazard = Hazard(op, self, past_t_offset, past_t_val)
            self.t_val = past_t_offset - self.t_offset

        return hazard
