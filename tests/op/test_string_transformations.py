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
Testing simple operational transformation (ignoring hazards) for string
transformations -- String Insert and String Delete
"""

from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestStringTransformations:
    """
    Tests simple cases of string insertion and string deletes. These tests were
    created before hazards came about, so they were meant to be applied more
    simply. Thus, after each test, each hazard needs to be removed.
    """
    def test_si_si(self):
        op1 = Op('si', [], offset=3, val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a lower offset, so should not be affected
        op2 = Op('si', [], offset=2, val="XYZ")
        op2.ot(cs1)
        assert op2.t_offset == 2
        op1.remove_old_hazards(purge=True)

        # op3 happens at an equal offset, so should be pushed forward
        op2 = Op('si', [], offset=3, val="XYZ")
        op2.ot(cs1)
        assert op2.t_offset == 6
        op1.remove_old_hazards(purge=True)

        # op4 happens at a later offset, so should be pushed forward
        op2 = Op('si', [], offset=5, val="XYZ")
        op2.ot(cs1)
        assert op2.t_offset == 8

    def test_si_sd(self):
        op1 = Op('si', [], offset=3, val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # insertion was at a later index than this delete. No change
        op2 = Op('sd', [], offset=0, val=3)
        op2.ot(cs1)
        assert op2.t_offset == 0
        assert op2.t_val == 3
        op1.remove_old_hazards(purge=True)

        # this deletion should expand to delete inserted text as well.
        op3 = Op('sd', [], offset=2, val=2)
        op3.ot(cs1)
        assert op3.t_offset == 2
        assert op3.t_val == 5
        op1.remove_old_hazards(purge=True)

        # edge case, don't delete text if don't have have to. Shift
        # delete range.
        op4 = Op('sd', [], offset=3, val=2)
        op4.ot(cs1)
        assert op4.t_offset == 6
        assert op4.t_val == 2
        op1.remove_old_hazards(purge=True)

        # insertion was at lower index. shift delete range forward.
        op5 = Op('sd', [], offset=4, val=2)
        op5.ot(cs1)
        assert op5.t_offset == 7
        assert op5.t_val == 2

    def test_sd_sd(self):
        op1 = Op('sd', [], offset=3, val=3)
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op1 deletes a range after op2, so should not affect it
        #                |-- op1 --|
        # |-- op2 --|
        op2 = Op('sd', [], offset=1, val=2)
        op2.ot(cs1)
        assert op2.t_offset == 1
        assert op2.t_val == 2
        op1.remove_old_hazards(purge=True)

        # The end of op3 overlaps the start of op 1
        #          |-- op1 --|
        #   |-- op3 --|
        op3 = Op('sd', [], offset=2, val=2)
        op3.ot(cs1)
        assert op3.t_offset == 2
        assert op3.t_val == 1
        op1.remove_old_hazards(purge=True)

        # op1 range is encompased by op 4 range
        #     |-- op1 --|
        #   |---- op4 ----|
        op4 = Op('sd', [], offset=2, val=6)
        op4.ot(cs1)
        assert op4.t_offset == 2
        assert op4.t_val == 3
        op1.remove_old_hazards(purge=True)

        # op5 range is encompased by op1 range
        #   |---- op1 ----|
        #     |-- op5 --|
        op5 = Op('sd', [], offset=4, val=1)
        op5.ot(cs1)
        assert op5.t_offset == 3
        assert op5.t_val == 0
        op1.remove_old_hazards(purge=True)

        # start of op6 range overlaps end of op1 range
        #   |-- op1 --|
        #         |-- op6 --|
        op6 = Op('sd', [], offset=5, val=3)
        op6.ot(cs1)
        assert op6.t_offset == 3
        assert op6.t_val == 2
        op1.remove_old_hazards(purge=True)

        # start of op7 range is after start of op1 range
        #   |-- op1 --|
        #                |-- op7 --|
        op7 = Op('sd', [], offset=8, val=3)
        op7.ot(cs1)
        assert op7.t_offset == 5
        assert op7.t_val == 3

    def test_sd_si(self):
        op1 = Op('sd', [], offset=3, val=3)
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # delete range has greater index than this insert. Do nothing
        op2 = Op('si', [], offset=2, val="ABC")
        op2.ot(cs1)
        assert op2.t_offset == 2
        assert op2.t_val == "ABC"
        op1.remove_old_hazards(purge=True)

        # edge case. avoid deleting
        op3 = Op('si', [], offset=3, val="ABC")
        op3.ot(cs1)
        assert op3.t_offset == 3
        assert op3.t_val == "ABC"
        op1.remove_old_hazards(purge=True)

        # text was put into delete range, so get rid of it.
        op4 = Op('si', [], offset=4, val="ABC")
        op4.ot(cs1)
        assert op4.t_offset == 3
        assert op4.t_val == ""
        op1.remove_old_hazards(purge=True)

        # text is at edge after delete range
        op5 = Op('si', [], offset=6, val="ABC")
        op5.ot(cs1)
        assert op5.t_offset == 3
        assert op5.t_val == "ABC"
