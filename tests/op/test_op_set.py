
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



from majormajor.ops.op import Op
from majormajor.changeset import Changeset

class TestOTSet:

    def test_set_root_preceding(self):
        """
        A preceding operation did a set at the root. Any following
        operations should be transformed to a noop.
        """
        op1 = Op('set', [], val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at root so should be affected
        op2 = Op('si', [], offset=2, val="XYZ")
        op2.ot(cs1)
        assert op2.is_noop() == True

        # op3 happens not at root. still should be affected
        op3 = Op('si', ['k',3,'j'], offset=3, val="XYZ")
        op3.ot(cs1)
        assert op3.is_noop() == True

    def test_set_root_after(self):
        """
        The set root occurs after other unknown operations. They should
        have no effect.
        """
        op1 = Op('si', [], offset=0, val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)


        op2 = Op('set', [], val="XYZ")
        op2.ot(cs1)
        assert op2.is_noop() == False
        assert op1.is_noop() == False

        # op3 happens not at root. still should be affected
        op3 = Op('set', ['k',3,'j'], offset=3, val="XYZ")
        op3.ot(cs1)
        assert op3.is_noop() == False

    def test_complex_path(self):
        op1 = Op('set', ['k',3,'j'], val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)


        op2 = Op('si', [], val="XYZ")
        op2.ot(cs1)
        assert op2.is_noop() == False
        assert op1.is_noop() == False

        op3 = Op('si', ['k',3,'j'], offset=3, val="XYZ")
        op3.ot(cs1)
        assert op3.is_noop() == True
        assert op1.is_noop() == False
        
        op4 = Op('si', ['k',3,'j','h'], offset=3, val="XYZ")
        op4.ot(cs1)
        assert op4.is_noop() == True
        assert op1.is_noop() == False
        
    def test_sequence_of_set_ops(self):
        op1 = Op('set', ['k',3,'j'], val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        op2 = Op('set', ['k',3,'j'], val="XYZ")
        op2.ot(cs1)
        assert op2.is_noop() == True
        assert op1.is_noop() == False

        cs2 = Changeset('doc_id', 'author', [cs1])
        cs2.add_op(op2)

        op3 = Op('set', ['k',3,'j'], val="XYZ")
        op3.ot(cs2)
        assert op2.is_noop() == True
        assert op3.is_noop() == False
