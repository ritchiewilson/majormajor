
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

"""
Testing simple operational transformation (ignoring hazards) for when a
String Insert is being transformed by a past opperations.
"""

from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestStringInsertOT:
    def test_ai_si(self):
        """
        A past opperations is an array insert which gets applied to this op.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('ai', array_path, offset=3, val=['X', 'Y'])
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('si', ['a', 'b', 3, 5], offset=2, val="XYZ")
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        op1.hazards = []

        # op3 happens at path, but lower offset, no change
        op3_path = array_path + [2]
        op3 = Op('si', op3_path, offset=2, val="XYZ")
        op3.ot(cs1)
        assert op3.t_path == op3_path
        op1.hazards = []

        # op4 happens in an array element being pushed forward (edge case)
        op4_path = array_path + [3]
        op4 = Op('si', op4_path, offset=8, val="XYZ")
        op4.ot(cs1)
        assert op4.t_path == array_path + [5]
        op1.hazards = []

        # op5 happens in an array element being pushed forward (not edge case)
        op5_path = array_path + [6]
        op5 = Op('si', op5_path, offset=8, val="XYZ")
        op5.ot(cs1)
        assert op5.t_path == array_path + [8]
        op1.hazards = []

        # op6 path is in an array element being pushed forward (edge case)
        op6_path = array_path + [3, 9, 'c']
        op6 = Op('si', op6_path, offset=8, val="XYZ")
        op6.ot(cs1)
        assert op6.t_path == array_path + [5, 9, 'c']
        op1.hazards = []

        # op7 path is in an array element being pushed forward (not edge case)
        op7_path = array_path + [5, 9, 'c']
        op7 = Op('si', op7_path, offset=8, val="XYZ")
        op7.ot(cs1)
        assert op7.t_path == array_path + [7, 9, 'c']
        op1.hazards = []

        # op8 path is shorter then array's path, so no change
        op8_path = array_path
        op8 = Op('si', op8_path, offset=8, val="XYZ")
        op8.ot(cs1)
        assert op8.t_path == array_path
        op1.hazards = []

    def Xtest_si_sd(self):
        op1 = Op('si', [], offset=3, val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # insertion was at a later index than this delete. No change
        op2 = Op('sd', [], offset=0, val=3)
        op2.ot(cs1)
        assert op2.t_offset == 0
        assert op2.t_val == 3
        op1.hazards = []

        # this deletion should expand to delete inserted text as well.
        op3 = Op('sd', [], offset=2, val=2)
        op3.ot(cs1)
        assert op3.t_offset == 2
        assert op3.t_val == 5
        op1.hazards = []

        # edge case, don't delete text if don't have have to. Shift
        # delete range.
        op4 = Op('sd', [], offset=3, val=2)
        op4.ot(cs1)
        assert op4.t_offset == 6
        assert op4.t_val == 2
        op1.hazards = []

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
        op1.hazards = []

        # The end of op3 overlaps the start of op 1
        #          |-- op1 --|
        #   |-- op3 --|
        op3 = Op('sd', [], offset=2, val=2)
        op3.ot(cs1)
        assert op3.t_offset == 2
        assert op3.t_val == 1
        op1.hazards = []

        # op1 range is encompased by op 4 range
        #     |-- op1 --|
        #   |---- op4 ----|
        op4 = Op('sd', [], offset=2, val=6)
        op4.ot(cs1)
        assert op4.t_offset == 2
        assert op4.t_val == 3
        op1.hazards = []

        # op5 range is encompased by op1 range
        #   |---- op1 ----|
        #     |-- op5 --|
        op5 = Op('sd', [], offset=4, val=1)
        op5.ot(cs1)
        assert op5.t_offset == 3
        assert op5.t_val == 0
        op1.hazards = []

        # start of op6 range overlaps end of op1 range
        #   |-- op1 --|
        #         |-- op6 --|
        op6 = Op('sd', [], offset=5, val=3)
        op6.ot(cs1)
        assert op6.t_offset == 3
        assert op6.t_val == 2
        op1.hazards = []

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
        op1.hazards = []

        # edge case. avoid deleting
        op3 = Op('si', [], offset=3, val="ABC")
        op3.ot(cs1)
        assert op3.t_offset == 3
        assert op3.t_val == "ABC"
        op1.hazards = []

        # text was put into delete range, so get rid of it.
        op4 = Op('si', [], offset=4, val="ABC")
        op4.ot(cs1)
        assert op4.t_offset == 3
        assert op4.t_val == ""
        op1.hazards = []

        # text is at edge after delete range
        op5 = Op('si', [], offset=6, val="ABC")
        op5.ot(cs1)
        assert op5.t_offset == 3
        assert op5.t_val == "ABC"
