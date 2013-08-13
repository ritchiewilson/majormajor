
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
Testing simple operational transformation (ignoring hazards) for array
transformations, Array Insert and Array Delete
"""

from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArrayTransformations:
    def test_ai_ai(self):
        """
        A past opperations is an array insert which gets applied to this op.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('ai', array_path, offset=3, val=['X', 'Y'])
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('ai', ['a', 'b', 3, 5], offset=2, val=["XYZ"])
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        op1.hazards = []

        # op3 happens at same path, but lower offset, no change
        op3 = Op('ai', array_path, offset=2, val=["XYZ"])
        op3.ot(cs1)
        assert op3.t_path == array_path
        assert op3.t_offset == 2
        op1.hazards = []

        # op4 is at same path with offset to get pushed forward (edge case)
        op4 = Op('ai', array_path, offset=3, val=["XYZ"])
        op4.ot(cs1)
        assert op4.t_path == array_path
        assert op4.t_offset == 5
        op1.hazards = []

        # op5 is at same path with offset to get pushed forward (not edge case)
        op5 = Op('ai', array_path, offset=8, val=["XYZ"])
        op5.ot(cs1)
        assert op5.t_path == array_path
        assert op5.t_offset == 10
        op1.hazards = []

        # op6 path is in an array element being pushed forward (edge case)
        op6_path = array_path + [3, 9, 'c']
        op6 = Op('ai', op6_path, offset=8, val=["XYZ"])
        op6.ot(cs1)
        assert op6.t_path == array_path + [5, 9, 'c']
        assert op6.t_offset == 8
        op1.hazards = []

        # op7 path is in an array element being pushed forward (not edge case)
        op7_path = array_path + [5, 9, 'c']
        op7 = Op('ai', op7_path, offset=8, val=["XYZ"])
        op7.ot(cs1)
        assert op7.t_path == array_path + [7, 9, 'c']
        op1.hazards = []

        # op8 path is shorter then array's path, so no change
        op8_path = ['a', 'b', 3]
        op8 = Op('ai', op8_path, offset=8, val=["XYZ"])
        op8.ot(cs1)
        assert op8.t_path == op8_path
        assert op8.t_offset == 8
        op1.hazards = []

    def test_ad_ai(self):
        """
        A past opperations is an array delete which gets applied to this op.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('ad', array_path, offset=3, val=3)
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected

        op2 = Op('ai', ['a', 'b', 3, 5], offset=2, val=['XYZ'])
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        assert op2.t_offset == 2
        op1.hazards = []

        # op3 happens at path, but lower offset, no change (edge case)
        op3 = Op('ai', array_path, offset=2, val=['XYZ'])
        op3.ot(cs1)
        assert op3.t_path == array_path
        assert op3.t_offset == 2
        assert not op3.is_noop()
        op1.hazards = []

        # op4 happens at path and in deletion range (edge case)
        op4 = Op('ai', array_path, offset=4, val=['XYZ'])
        op4.ot(cs1)
        assert op4.t_path == array_path
        assert op4.t_offset == 3
        assert op4.is_noop()
        op1.hazards = []

        # op5 happens at path and after deletion range (edge case)
        op5 = Op('ai', array_path, offset=6, val=['XYZ'])
        op5.ot(cs1)
        assert op5.t_path == array_path
        assert op5.t_offset == 3
        assert not op5.is_noop()
        op1.hazards = []

        # op5 happens within an array element being deleted (edge case)
        op5_path = array_path + [3]
        op5 = Op('ai', op5_path, offset=8, val=['XYZ'])
        op5.ot(cs1)
        assert op5.is_noop()
        op1.hazards = []

        # op6 is within an array element being deleted (other edge case)
        op6_path = array_path + [5]
        op6 = Op('ai', op6_path, offset=8, val=['XYZ'])
        op6.ot(cs1)
        assert op6.is_noop()
        op1.hazards = []

        # op7 path is far in an array element being deleted
        op7_path = array_path + [4, 9, 'c']
        op7 = Op('ai', op7_path, offset=8, val=['XYZ'])
        op7.ot(cs1)
        assert op7.is_noop()
        op1.hazards = []

        # op8 path is in an array element being pulled back (edge case)
        op8_path = array_path + [6, 9, 'c']
        op8 = Op('ai', op8_path, offset=8, val=['XYZ'])
        op8.ot(cs1)
        assert op8.t_path == array_path + [3, 9, 'c']
        op1.hazards = []

        # op9 path is in an array element NOT being pulled back (edge case)
        op9_path = array_path + [2, 9, 'c']
        op9 = Op('ai', op9_path, offset=8, val=['XYZ'])
        op9.ot(cs1)
        assert op9.t_path == array_path + [2, 9, 'c']
        op1.hazards = []

        # op10 path is shorter than past path, so no change
        op10_path = ['a', 'b', 3]
        op10 = Op('ai', op10_path, offset=8, val=['XYZ'])
        op10.ot(cs1)
        assert op10.t_path == ['a', 'b', 3]
        assert op10.t_offset == 8
        op1.hazards = []

    def test_ai_ad(self):
        """
        A past opperation is an array insert which gets applied to these array
        deletes.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('ai', array_path, offset=3, val=['X', 'Y'])
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('ad', ['a', 'b', 3, 5], offset=2, val=3)
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        assert op2.t_offset == 2
        assert op2.t_val == 3
        op1.hazards = []

        # op3 happens at same path, but past insert is before delete range, so
        # delete moves. (edge case)
        op3 = Op('ad', array_path, offset=3, val=3)
        op3.ot(cs1)
        assert op3.t_path == array_path
        assert op3.t_offset == 5
        op1.hazards = []

        # op4 is at same path and will expand delete range to include past
        # op. (edge case)
        op4 = Op('ad', array_path, offset=2, val=3)
        op4.ot(cs1)
        assert op4.t_path == array_path
        assert op4.t_val == 5
        assert op4.t_offset == 2
        op1.hazards = []

        # op5 is at same path and will expand delete range to include past
        # op. (other edge case)
        op5 = Op('ad', array_path, offset=1, val=3)
        op5.ot(cs1)
        assert op5.t_path == array_path
        assert op5.t_val == 5
        assert op5.t_offset == 1
        op1.hazards = []

        # op6 is at same path with delete range at lower index than
        # insert. (edge case)
        op6 = Op('ad', array_path, offset=1, val=2)
        op6.ot(cs1)
        assert op6.t_path == array_path
        assert op6.t_val == 2
        assert op6.t_offset == 1
        op1.hazards = []

        # op7 path is in an array element being pushed forward (edge case)
        op7_path = array_path + [3, 9, 'c']
        op7 = Op('ad', op7_path, offset=8, val=3)
        op7.ot(cs1)
        assert op7.t_path == array_path + [5, 9, 'c']
        assert op7.t_offset == 8
        op1.hazards = []

        # op8 path is in an array element being pushed forward (not edge case)
        op8_path = array_path + [5, 9, 'c']
        op8 = Op('ad', op8_path, offset=8, val=3)
        op8.ot(cs1)
        assert op8.t_path == array_path + [7, 9, 'c']
        op1.hazards = []

        # op9 path is shorter then array's path, so no change
        op9_path = ['a', 'b', 3]
        op9 = Op('ad', op9_path, offset=8, val=3)
        op9.ot(cs1)
        assert op9.t_path == op9_path
        assert op9.t_offset == 8
        op1.hazards = []
