
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

    def string_insert_transform(self, op):
        """
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self.get_changeset())
        return False

    def string_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        return False
