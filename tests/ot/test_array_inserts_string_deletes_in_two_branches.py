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
Set up two branches to do array insertions and string deletes. Each branch 1)
inserts array elements, 2) Deletes strings from their now private elements and
3) deletes strings from the original array elements known by both branches.
"""

from majormajor.document import _Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArrayInsertsAndStringDeletesInTwoBranches:

    def setup_method(self, method):
        s1 = ['ABCD',
              'EFGH',
              'IJKL',
              'MNOP',
              'QRST',
              'UVWX',
              'YZ']
        doc = _Document(snapshot=s1)
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        self.root = self.doc.get_root_changeset()

        # establish the reusable changesets

        # Branch A inserts new array elements, and deletes text from them.
        # It also deletes text from three existing elements, before any array
        # insert, in the middle, and after the last array insert.
        A0 = Changeset(doc.get_id(), 'u1', [self.root])
        vA0 = ['01234', '56789']
        A0.add_op(Op('ai', [], offset=2, val=vA0))
        A0.set_id('A')
        self.A0 = A0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        vA1 = ['abcde', 'fghij']
        A1.add_op(Op('ai', [], offset=6, val=vA1))
        self.A1 = A1

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('sd', [2], offset=1, val=4))
        A2.add_op(Op('sd', [3], offset=0, val=3))
        self.A2 = A2

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        A3.add_op(Op('sd', [6], offset=3, val=1))
        self.A3 = A3

        A4 = Changeset(doc.get_id(), 'u1', [A3])
        A4.add_op(Op('sd', [0], offset=0, val=3))
        A4.add_op(Op('sd', [4], offset=2, val=2))
        self.A4 = A4

        A5 = Changeset(doc.get_id(), 'u1', [A4])
        A5.add_op(Op('sd', [9], offset=1, val=2))
        self.A5 = A5

        # Branch B performs similar actions to branch A.
        # First inserts array elements
        B0 = Changeset(doc.get_id(), 'u2', [self.root])
        vB0a, vB0b = ['lorem', 'ipsum'], ['dolor', 'sit']
        opB0a = Op('ai', [], offset=2, val=vB0a)
        B0.add_op(opB0a)
        opB0b = Op('ai', [], offset=6, val=vB0b)
        B0.add_op(opB0b)
        B0.set_id('B')
        self.B0 = B0

        # Now B deletes parts of strings in the elements it created
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        B1.add_op(Op('sd', [2], offset=3, val=2))
        B1.add_op(Op('sd', [3], offset=2, val=2))
        B1.add_op(Op('sd', [6], offset=1, val=1))
        B1.add_op(Op('sd', [7], offset=0, val=3))
        B1.set_id('B1')
        self.B1 = B1

        # B deletes strings from each original element, including elements A
        # had edited
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        B2.add_op(Op('sd', [0], offset=1, val=3))
        B2.add_op(Op('sd', [1], offset=2, val=2))
        B2.add_op(Op('sd', [4], offset=0, val=1))
        B2.add_op(Op('sd', [5], offset=1, val=2))
        B2.add_op(Op('sd', [8], offset=2, val=1))
        B2.add_op(Op('sd', [9], offset=3, val=1))
        B2.add_op(Op('sd', [10], offset=0, val=1))
        B2.set_id('B2')
        self.B2 = B2

    def test_receive_A_first_with_A_ordered_first(self):
        """
        The document receives all of branch A before any of branch B, and
        branch A should get ordered first.
        """
        doc = self.doc

        # Insert some array elements
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)

        # Delete strings from the new elements
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)

        # Delete strings from the existing elements
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)

        result = ['D',
                  'EFGH',
                  '0',
                  '89',
                  'IJ',
                  'MNOP',
                  'abce',
                  'fghij',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Branch B inserts array elements
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index
        result = ['D',
                  'EFGH',
                  '0',
                  '89',
                  'lorem',
                  'ipsum',
                  'IJ',
                  'MNOP',
                  'abce',
                  'fghij',
                  'dolor',
                  'sit',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B deletes strings from elements it created
        doc.receive_changeset(self.B1)
        result = ['D',
                  'EFGH',
                  '0',
                  '89',
                  'lor',
                  'ipm',
                  'IJ',
                  'MNOP',
                  'abce',
                  'fghij',
                  'dlor',
                  '',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B Deletes strings from all elements known to A and B
        doc.receive_changeset(self.B2)
        result = ['',
                  'EF',
                  '0',
                  '89',
                  'lor',
                  'ipm',
                  'J',
                  'MP',
                  'abce',
                  'fghij',
                  'dlor',
                  '',
                  'QRT',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result

    def test_receive_A_first_with_B_ordered_first(self):
        """
        The document receives all of branch A before any of branch B, and
        branch B should get ordered first.
        """
        doc = self.doc

        # Insert some array elements
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)

        # Delete strings from the new elements
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)

        # Delete strings from the existing elements
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)

        # Force Branch B to be ordered before Branch A
        self.B0.set_id('0B0')
        doc.receive_changeset(self.B0)

        # Check that branch B gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index
        result = ['D',
                  'EFGH',
                  'lorem',
                  'ipsum',
                  '0',
                  '89',
                  'IJ',
                  'MNOP',
                  'dolor',
                  'sit',
                  'abce',
                  'fghij',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B deletes strings from elements it created
        doc.receive_changeset(self.B1)
        result = ['D',
                  'EFGH',
                  'lor',
                  'ipm',
                  '0',
                  '89',
                  'IJ',
                  'MNOP',
                  'dlor',
                  '',
                  'abce',
                  'fghij',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B deletes strings from all elements known to A and B
        doc.receive_changeset(self.B2)
        result = ['',
                  'EF',
                  'lor',
                  'ipm',
                  '0',
                  '89',
                  'J',
                  'MP',
                  'dlor',
                  '',
                  'abce',
                  'fghij',
                  'QRT',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result

    def test_receive_B_first_with_A_ordered_first(self):
        """
        The document receives all of branch B before any of branch A, and
        branch A should get ordered first.
        """
        doc = self.doc

        # Branch B inserts some array elements
        doc.receive_changeset(self.B0)

        # B deletes strings from elements it created
        doc.receive_changeset(self.B1)

        # B deletes strings from all elements known to A and B
        doc.receive_changeset(self.B2)
        result = ['A',
                  'EF',
                  'lor',
                  'ipm',
                  'JKL',
                  'MP',
                  'dlor',
                  '',
                  'QRT',
                  'UVW',
                  'Z']
        assert doc.get_snapshot() == result

        # Insert some array elements
        doc.receive_changeset(self.A0)
        result = ['A',
                  'EF',
                  '01234',
                  '56789',
                  'lor',
                  'ipm',
                  'JKL',
                  'MP',
                  'dlor',
                  '',
                  'QRT',
                  'UVW',
                  'Z']
        assert doc.get_snapshot() == result

        # Insert two more Array elements
        doc.receive_changeset(self.A1)
        result = ['A',
                  'EF',
                  '01234',
                  '56789',
                  'lor',
                  'ipm',
                  'JKL',
                  'MP',
                  'abcde',
                  'fghij',
                  'dlor',
                  '',
                  'QRT',
                  'UVW',
                  'Z']
        assert doc.get_snapshot() == result

        # Delete strings from the new elements
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)
        result = ['A',
                  'EF',
                  '0',
                  '89',
                  'lor',
                  'ipm',
                  'JKL',
                  'MP',
                  'abce',
                  'fghij',
                  'dlor',
                  '',
                  'QRT',
                  'UVW',
                  'Z']
        assert doc.get_snapshot() == result

        # Delete strings from the existing elements
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)
        result = ['',
                  'EF',
                  '0',
                  '89',
                  'lor',
                  'ipm',
                  'J',
                  'MP',
                  'abce',
                  'fghij',
                  'dlor',
                  '',
                  'QRT',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result
