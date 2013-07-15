
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


class Hazard:
    STRING_DELETE_RANGE_OVERLAP = 0

    def __init__(self, base_op, conflict_op):
        self.base_op = base_op
        self.conflict_op = conflict_op
        self.base_cs = base_op.get_changeset()
        self.conflict_cs = conflict_op.get_changeset()
        self.conflict_op_index = None
        if self.conflict_cs:
            self.conflict_op_index = self.conflict_cs.get_ops().index(conflict_op)
        self.base_op_index = None
        if self.base_cs:
            self.base_op_index = self.base_cs.get_ops().index(base_op)
        self.hazard_type = None
        self.calculate_hazard_info()

    def calculate_hazard_info(self):
        if self.base_op.is_string_delete() and self.conflict_op.is_string_delete():
            self.base_op_t_offset = self.base_op.t_offset
            self.base_op_t_val = self.base_op.t_val
            self.conflict_op_t_offset = self.conflict_op.t_offset
            self.conflict_op_t_val = self.conflict_op.t_val
            
            bre = self.base_op.t_offset + self.base_op.t_val # base range end
            cre = self.conflict_op.t_offset + self.conflict_op.t_val # conflict op range end
            self.delete_overlap_range_end = min(bre, cre)

            brs = self.base_op.t_offset  # base range start
            crs = self.conflict_op.t_offset  # conflict op range start
            self.delete_overlap_range_start = max(brs, crs)

            self.delete_overlap_range_size = min(bre, cre) - max(brs,crs)

            self.min_offset_for_hazard_application = self.conflict_op.t_offset

            self.string_insert_offset_shift = self.conflict_op_t_val - \
                                            self.get_delete_overlap_range_size()

    def get_string_insert_offset_shift(self):
        return self.string_insert_offset_shift
    
    def get_delete_overlap_end(self):
        return self.delete_overlap_range_end

    def get_delete_overlap_start(self):
        return self.delete_overlap_range_start

    def get_conflict_op_index(self):
        return self.conflict_op_index

    def get_base_op_index(self):
        return self.conflict_op_index

    def get_delete_overlap_range_size(self):
        return self.delete_overlap_range_size

    def get_min_offset_for_hazard_application(self):
        return self.min_offset_for_hazard_application

    def is_string_delete_range_overlap_hazard(self):
        return self.base_op.t_path == self.conflict_op.t_path and  \
            self.base_op.is_string_delete() and self.conflict_op.is_string_delete()
        
