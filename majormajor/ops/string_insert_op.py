
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

from string_transform_op import StringTransformOp

class StringInsertOp(StringTransformOp):
    def is_string_insert(self):
        return True
        
    def string_insert_transform(self, op, hazards):
        if self.t_path != op.t_path:
            return

        past_t_path, past_t_offset, past_t_val \
            = self.shift_past_op_by_hazards(op, hazards)
        
        if self.t_offset >= past_t_offset:
            self.t_offset += len(op.t_val)

    def string_delete_transform(self, op, hazards):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return

        past_t_path, past_t_offset, past_t_val = \
            self.shift_past_op_by_hazards(op, hazards)
                                                                               
        if self.t_offset >= past_t_offset + past_t_val:
            self.t_offset -= past_t_val
        elif self.t_offset > past_t_offset:
            self.t_offset = past_t_offset
            self.t_val = ''
 
