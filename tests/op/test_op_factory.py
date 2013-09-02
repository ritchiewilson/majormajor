# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Testing operational transformation with each combination of
possible opperations.
"""

from majormajor.ops.op import Op, SetOp
from majormajor.ops.string_insert_op import StringInsertOp
from majormajor.ops.string_delete_op import StringDeleteOp
from majormajor.changeset import Changeset

class TestOT:

    def test_inheritance(self):
        si_op = Op('si', [], offset=3, val="ABC")
        assert isinstance(si_op, Op)
        assert isinstance(si_op, StringInsertOp)

        sd_op = Op('sd', [], offset=3, val=2)
        assert isinstance(sd_op, Op)
        assert isinstance(sd_op, StringDeleteOp)
        assert not isinstance(sd_op, StringInsertOp)

        set_op = Op('set', [], val="ABC")
        assert isinstance(set_op, Op)
        assert isinstance(set_op, SetOp)
        assert not isinstance(set_op, StringDeleteOp)
        assert not isinstance(set_op, StringInsertOp)
