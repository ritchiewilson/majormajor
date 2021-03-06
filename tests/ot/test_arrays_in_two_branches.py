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
Tests Array opperations, inserts and deletes, in two branches which then
get synced together.
"""

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArraysInTwoBranches:

    def setup_method(self, method):
        s1 = ['ABCD',
              'EFGH',
              'IJKL',
              'MNOP',
              'QRST',
              'UVWX',
              'YZ']
        self.doc1 = Document(snapshot=s1)
        self.doc1.HAS_EVENT_LOOP = False
        self.root1 = self.doc1.get_root_changeset()

    def test_one_delete_in_first_branch(self):
        """
        There is one delete in the first branch, multiple in branch B, then
        each has more string inserts.
        """
        doc = self.doc1
        root = self.root1

        # construct branch A, which begins with a string delete, then
        # adds text
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('ad', [], offset=3, val=2))
        A0.set_id('A')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        v1 = ['0123', '4567']
        A1.add_op(Op('ai', [], offset=3, val=v1))
        doc.receive_changeset(A1)
        result = ['ABCD',
                  'EFGH',
                  'IJKL',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Branch B has common parent with A. B has three deletes, some of which
        # overlap the delete in branch A
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('ad', [], offset=2, val=2)
        B0.add_op(opB0)
        B0.set_id('B')
        doc.receive_changeset(B0)
        a_index = doc.get_ordered_changesets().index(A0)
        b_index = doc.get_ordered_changesets().index(B0)
        assert a_index < b_index
        assert opB0.t_offset == 2
        assert opB0.t_val == 1
        result = ['ABCD',
                  'EFGH',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Partially overlaping delete
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('ad', [], offset=2, val=1)
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        result = ['ABCD',
                  'EFGH',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result
        assert opB1.t_val == 0
        assert opB1.is_noop()

        # Delete Range unaffected by branch A
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        opB2 = Op('ad', [], offset=1, val=1)
        B2.add_op(opB2)
        B2.set_id('B2')
        doc.receive_changeset(B2)
        result = ['ABCD',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result
        assert opB2.t_offset == 1
        assert opB2.t_val == 1

        # Insert before the Delete Range
        B3 = Changeset(doc.get_id(), 'u2', [B2])
        vB3 = ['BBBBB', 'CCCCC']
        opB3 = Op('ai', [], offset=1, val=vB3)
        B3.add_op(opB3)
        B3.set_id('B3')
        doc.receive_changeset(B3)
        result = ['ABCD',
                  '0123',
                  '4567',
                  'BBBBB',
                  'CCCCC',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Insert After the Delete Range
        B4 = Changeset(doc.get_id(), 'u2', [B3])
        vB4 = ['DDDDD', 'EEEEE']
        opB4 = Op('ai', [], offset=3, val=vB4)
        B4.add_op(opB4)
        B4.set_id('B4')
        doc.receive_changeset(B4)
        result = ['ABCD',
                  '0123',
                  '4567',
                  'BBBBB',
                  'CCCCC',
                  'DDDDD',
                  'EEEEE',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

    def test_one_delete_in_first_branch_reversed(self):
        """
        Same test as above, except branch B gets applied before branch A.
        """
        doc = self.doc1
        root = self.root1

        # construct branch A, which begins with a string delete, then
        # adds text
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('ad', [], offset=3, val=2))
        A0.set_id('1A')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        v1 = ['0123', '4567']
        A1.add_op(Op('ai', [], offset=3, val=v1))
        doc.receive_changeset(A1)
        result = ['ABCD',
                  'EFGH',
                  'IJKL',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Branch B has common parent with A. B has three deletes, some of which
        # overlap the delete in branch A
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('ad', [], offset=2, val=2)
        B0.add_op(opB0)
        B0.set_id('0B')
        doc.receive_changeset(B0)
        a_index = doc.get_ordered_changesets().index(A0)
        b_index = doc.get_ordered_changesets().index(B0)
        assert a_index > b_index
        result = ['ABCD',
                  'EFGH',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Partially overlaping delete
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('ad', [], offset=2, val=1)
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        result = ['ABCD',
                  'EFGH',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Delete Range unaffected by branch A
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        opB2 = Op('ad', [], offset=1, val=1)
        B2.add_op(opB2)
        B2.set_id('B2')
        doc.receive_changeset(B2)
        result = ['ABCD',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B3 = Changeset(doc.get_id(), 'u2', [B2])
        vB3 = ['BBBBB', 'CCCCC']
        opB3 = Op('ai', [], offset=1, val=vB3)
        B3.add_op(opB3)
        B3.set_id('B3')
        doc.receive_changeset(B3)
        result = ['ABCD',
                  'BBBBB',
                  'CCCCC',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B4 = Changeset(doc.get_id(), 'u2', [B3])
        vB4 = ['DDDDD', 'EEEEE']
        opB4 = Op('ai', [], offset=3, val=vB4)
        B4.add_op(opB4)
        B4.set_id('B4')
        doc.receive_changeset(B4)
        result = ['ABCD',
                  'BBBBB',
                  'CCCCC',
                  'DDDDD',
                  'EEEEE',
                  '0123',
                  '4567',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

    def test_consecutive_inserts(self):
        doc = self.doc1
        root = self.root1

        # Branch A
        A0 = Changeset(doc.get_id(), 'u1', [root])
        vA0 = ['1', '2']
        A0.add_op(Op('ai', [], offset=2, val=vA0))
        A0.set_id('A')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        vA1 = ['3', '4']
        A1.add_op(Op('ai', [], offset=4, val=vA1))
        doc.receive_changeset(A1)

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        vA2 = ['8', '9']
        A2.add_op(Op('ai', [], offset=9, val=vA2))
        doc.receive_changeset(A2)

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        vA3 = ['0']
        A3.add_op(Op('ai', [], offset=11, val=vA3))
        doc.receive_changeset(A3)
        result = ['ABCD',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Now B has a series of inserts
        B0 = Changeset(doc.get_id(), 'u1', [root])
        vB0 = ['1b', '2b']
        B0.add_op(Op('ai', [], offset=1, val=vB0))
        B0.set_id('B')
        doc.receive_changeset(B0)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B1 = Changeset(doc.get_id(), 'u1', [B0])
        vB1 = ['3b', '4b']
        B1.add_op(Op('ai', [], offset=5, val=vB1))
        doc.receive_changeset(B1)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  '3b', '4b',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B2 = Changeset(doc.get_id(), 'u1', [B1])
        vB2 = ['8b', '9b', '0b']
        B2.add_op(Op('ai', [], offset=7, val=vB2))
        doc.receive_changeset(B2)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  '3b', '4b', '8b', '9b', '0b',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B3 = Changeset(doc.get_id(), 'u1', [B2])
        vB3 = ['BBBB']
        B3.add_op(Op('ai', [], offset=12, val=vB3))
        doc.receive_changeset(B3)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  '3b', '4b', '8b', '9b', '0b',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'BBBB',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

    def test_consecutive_inserts_reversed(self):
        """
        Same as the previous test except branch B gets applied before branch A.
        """
        doc = self.doc1
        root = self.root1

        # Branch A
        A0 = Changeset(doc.get_id(), 'u1', [root])
        vA0 = ['1', '2']
        A0.add_op(Op('ai', [], offset=2, val=vA0))
        A0.set_id('1A')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        vA1 = ['3', '4']
        A1.add_op(Op('ai', [], offset=4, val=vA1))
        doc.receive_changeset(A1)

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        vA2 = ['8', '9']
        A2.add_op(Op('ai', [], offset=9, val=vA2))
        doc.receive_changeset(A2)

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        vA3 = ['0']
        A3.add_op(Op('ai', [], offset=11, val=vA3))
        doc.receive_changeset(A3)
        result = ['ABCD',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Now B has a series of inserts
        B0 = Changeset(doc.get_id(), 'u1', [root])
        vB0 = ['1b', '2b']
        B0.add_op(Op('ai', [], offset=1, val=vB0))
        B0.set_id('0B')
        doc.receive_changeset(B0)
        a_index = doc.get_ordered_changesets().index(A0)
        b_index = doc.get_ordered_changesets().index(B0)
        assert a_index > b_index
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B1 = Changeset(doc.get_id(), 'u1', [B0])
        vB1 = ['3b', '4b']
        B1.add_op(Op('ai', [], offset=5, val=vB1))
        doc.receive_changeset(B1)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  '3b', '4b',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B2 = Changeset(doc.get_id(), 'u1', [B1])
        vB2 = ['8b', '9b', '0b']
        B2.add_op(Op('ai', [], offset=7, val=vB2))
        doc.receive_changeset(B2)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  '3b', '4b', '8b', '9b', '0b',
                  'MNOP',
                  'QRST',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        B3 = Changeset(doc.get_id(), 'u1', [B2])
        vB3 = ['BBBB']
        B3.add_op(Op('ai', [], offset=12, val=vB3))
        doc.receive_changeset(B3)
        result = ['ABCD',
                  '1b', '2b',
                  'EFGH',
                  '1', '2', '3', '4',
                  'IJKL',
                  '3b', '4b', '8b', '9b', '0b',
                  'MNOP',
                  'QRST',
                  'BBBB',
                  '8', '9', '0',
                  'UVWX',
                  'YZ']
        assert doc.get_snapshot() == result
