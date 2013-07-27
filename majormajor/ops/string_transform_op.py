
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

from op import Op

class StringTransformOp(Op):
    def is_string_transform(self):
        return True

    def shift_past_string_insert_by_hazards(self, op, hazards):
        past_t_offset = op.t_offset
        for hazard in hazards:
            if past_t_offset >= hazard.get_min_offset_for_hazard_application():
                past_t_offset -= hazard.get_string_insert_offset_shift()
        return op.t_path, past_t_offset, op.t_val

    def shift_past_string_delete_by_hazards(self, op, hazards):
        past_t_val = op.t_val
        past_t_offset = op.t_offset
        for hazard in hazards:
            if past_t_offset > hazard.get_min_offset_for_hazard_application():
                past_t_offset -= hazard.get_delete_overlap_range_size()
            if hazard.base_op == op:
                past_t_val -= hazard.get_delete_overlap_range_size()
        return op.t_path, past_t_offset, past_t_val
        
