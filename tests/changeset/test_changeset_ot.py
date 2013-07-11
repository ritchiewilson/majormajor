
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

import pytest

from majormajor.document import Document
from majormajor.op import Op
from majormajor.changeset import Changeset

class TestChangesetOT:

    def test_overlaping_deletes(self):
        """
        At the same time, two users delete the same text, then insert
        different text. The union of the deletion ranges should be
        deleted and the two sets of inserted text should appear in
        full, side by side.
        """
        doc = Document(snapshot='')
        root = doc.get_root_changeset()

        # create a common parrent for two divergent branches
        common_parent = Changeset(doc.get_id(), 'u1', [root])
        common_parent.add_op(Op('si', [], offset=0, val='12345678'))
        doc.receive_changeset(common_parent)
        assert doc.get_snapshot() == '12345678'

        # construct branch A, which begins with a string delete, then
        # inserts 'abcde' in three changesets.
        A0 = Changeset(doc.get_id(), 'u1', [common_parent])
        A0.add_op(Op('sd', [], offset=0, val=8))
        A0.add_op(Op('si', [], offset=0, val='abc'))
        A0.set_id('A')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [], offset=3, val='d'))
        doc.receive_changeset(A1)

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [], offset=4, val='e'))
        doc.receive_changeset(A2)
        assert doc.get_snapshot() == 'abcde'

        # Branch B has common parent with A. Insert some text at the
        # end, delete the same range branch A deleted, then insert
        # more text
        B0 = Changeset(doc.get_id(), 'u2', [common_parent])
        B0.add_op(Op('si', [], offset=8, val='f'))
        B0.set_id('B')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == 'abcdef'
        op = B0.get_ops()[0]
        assert op.t_offset == 5

        # CS with overlapping delete range
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        B1.add_op(Op('sd', [], offset=0, val=8))
        B1.add_op(Op('si', [], offset=1, val='ghi'))
        B1.set_id('B1')
        doc.receive_changeset(B1)
        op0, op1 = B1.get_ops()
        assert op0.t_offset == 5
        assert op0.t_val == 0
        assert op1.t_offset == 6
        assert op1.t_val == 'ghi'
        assert doc.get_snapshot() == 'abcdefghi'

        B2 = Changeset(doc.get_id(), 'u2', [B1])
        B2.add_op(Op('si', [], offset=4, val='jkl'))
        B2.set_id('B2')
        doc.receive_changeset(B2)
        op = B2.get_ops()[0]
        assert op.t_offset == 9
        assert op.t_val == 'jkl'
        assert doc.get_snapshot() == 'abcdefghijkl'

        # combine these braches again
        C = Changeset(doc.get_id(), 'u2', [A2, B2])
        C.add_op(Op('si', [], offset=6, val=' XYZ '))
        doc.receive_changeset(C)
        assert doc.get_snapshot() == 'abcdef XYZ ghijkl'
