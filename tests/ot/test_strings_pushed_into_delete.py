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


from majormajor.document import _Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestStringsPushedIntoDeleteRange:
    """
    This demonstrates how a string may or may not be pushed into a delete range
    based on the order in which it is applied. This same principle is true for
    array elements which may be pushed into a delete range.

    In this case, branch A inserts 'ab' and branch B inserts 'cd' at the same
    location. Then branch A deletes a range which consistes of the 'b' and the
    next character, which it sees as '1'.

    In the case that the A branch is ordered first, the result of the two
    string insertions is '0abcd123'. Then when the A branch tries to delete the
    string 'b1', it must also effectively delete the 'cd' which branch B
    inserted. Through OT, the string 'cd' was pushed into the delete range.

    However, in the case that the B branch is ordered first, the result of the
    two string insertions is '0cdab123'. Now when the A branch tries to delete
    the string 'b1', it does not need to also delete 'cd'. After this OT, the
    string 'cs' was NOT pushed into the delete range.

    The following test :class:`TestAvoidPushingStringsIntoDeleteRange'
    demonstrates how to avoid this if the B branch's inserts must be preserved.
    """
    def setup_method(self, method):
        doc = _Document(snapshot='0123')
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        root = doc.get_root_changeset()

        #
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('si', [], offset=1, val='ab'))
        self.A0 = A0

        B0 = Changeset(doc.get_id(), 'u2', [root])
        B0.add_op(Op('si', [], offset=1, val='cd'))
        self.B0 = B0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('sd', [], offset=2, val=2))
        self.A1 = A1

    def test_string_pushed_into_delete_range(self):
        """
        Branch B inserts its string into an unknown delete range, and so gets
        deleted.
        """
        doc = self.doc
        # Force branch A to be ordered first
        self.A0.set_id('A')
        self.B0.set_id('B')

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0a23'

        doc.receive_changeset(self.B0)
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index
        assert doc.get_snapshot() == '0a23'

    def test_not_string_pushed_into_delete_range(self):
        """
        Branch B inserts its string before the delete range, and so does not
        need to get deleted.
        """
        doc = self.doc
        # Force branch B to be ordered first
        self.A0.set_id('A')
        self.B0.set_id('0B')

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0a23'

        doc.receive_changeset(self.B0)
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index
        assert doc.get_snapshot() == '0cda23'


class TestAvoidPushingStringsIntoDeleteRange:
    """
    This demonstrates how to defnitively avoid pushing a string insert into a
    deletion range as described in
    :class:`TestStringsPushedIntoDeleteRange`. This same principle is true for
    array elements which may be pushed into a delete range.

    The essential difference is that branch A does not delete a range in one
    op, but instead deletes the desired characters one at a time. In that case,
    through OT, the string deletes in branch A will delete exactly the
    originally intended characters, even if they are no longer side by side.

    This method works similarly for array transformations.
    """

    def setup_method(self, method):
        doc = _Document(snapshot='0123')
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        root = doc.get_root_changeset()

        #
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('si', [], offset=1, val='ab'))
        self.A0 = A0

        B0 = Changeset(doc.get_id(), 'u2', [root])
        B0.add_op(Op('si', [], offset=1, val='cd'))
        self.B0 = B0

        # instead of deleting range, A will delete character one at a time.
        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('sd', [], offset=2, val=1))
        A1.add_op(Op('sd', [], offset=2, val=1))
        self.A1 = A1

    def test_branch_A_ordered_first(self):
        """
        Branch B's string insert is preserved
        """
        doc = self.doc
        # Force branch A to be ordered first
        self.A0.set_id('A')
        self.B0.set_id('B')

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0a23'

        doc.receive_changeset(self.B0)
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index
        assert doc.get_snapshot() == '0acd23'

    def test_branch_B_ordered_first(self):
        """
        Branch B's string insert is preserved
        """
        doc = self.doc
        # Force branch B to be ordered first
        self.A0.set_id('A')
        self.B0.set_id('0B')

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0a23'

        doc.receive_changeset(self.B0)
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index
        assert doc.get_snapshot() == '0cda23'
