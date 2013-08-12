
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

    def test_ad_si(self):
        """
        A past opperations is an array delete which gets applied to this op.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('ad', array_path, offset=3, val=3)
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

        # op4 happens in an array element being deleted (edge case)
        op4_path = array_path + [3]
        op4 = Op('si', op4_path, offset=8, val="XYZ")
        op4.ot(cs1)
        assert op4.is_noop()
        op1.hazards = []

        # op5 happens in an array element being deleted (other edge case)
        op5_path = array_path + [5]
        op5 = Op('si', op5_path, offset=8, val="XYZ")
        op5.ot(cs1)
        assert op5.is_noop()
        op1.hazards = []

        # op6 path is far in an array element being deleted
        op6_path = array_path + [4, 9, 'c']
        op6 = Op('si', op6_path, offset=8, val="XYZ")
        op6.ot(cs1)
        assert op6.is_noop()
        op1.hazards = []

        # op7 path is in an array element being pulled back (edge case)
        op7_path = array_path + [6, 9, 'c']
        op7 = Op('si', op7_path, offset=8, val="XYZ")
        op7.ot(cs1)
        assert op7.t_path == array_path + [3, 9, 'c']
        op1.hazards = []

        # op8 path is shorter then array's path, so no change
        op8_path = array_path
        op8 = Op('si', op8_path, offset=8, val="XYZ")
        op8.ot(cs1)
        assert op8.t_path == array_path
        op1.hazards = []
