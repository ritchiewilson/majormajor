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
Set up two branches to do array and string deletes. Each branch 1) deletes
parts of the text, 2) deletes elements from the array and 3) deletes more text
from the remaining elements
"""

from majormajor.document import _Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArrayAndStringDeletesInTwoBranches:

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

        # Branch A 1) deletes some from three strings in the array, 2) deletes
        # array elements and 3) deletes more partial strings
        A0 = Changeset(doc.get_id(), 'u1', [self.root])
        A0.add_op(Op('sd', [1], offset=2, val=2))  # deletes 'GH'
        A0.set_id('A')
        self.A0 = A0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('sd', [3], offset=0, val=3))  # deletes 'MNO'
        self.A1 = A1

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('sd', [5], offset=1, val=1))  # 'V'
        self.A2 = A2

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        A3.add_op(Op('ad', [], offset=1, val=2))  # ['EF', 'IJKL']
        self.A3 = A3

        A4 = Changeset(doc.get_id(), 'u1', [A3])
        A4.add_op(Op('ad', [], offset=2, val=1))  # ['QRST']
        A4.add_op(Op('sd', [2], offset=2, val=1))  # 'X'
        A4.set_id('A4')
        self.A4 = A4

        A5 = Changeset(doc.get_id(), 'u1', [A4])
        A5.add_op(Op('sd', [3], offset=0, val=1))  # Deletes 'Y'
        self.A5 = A5

        # Branch B performs similar actions to branch A. It deletes text, some
        # of which is overlapping, 2) deletes elements, some overlap, and 3)
        # deletes more text
        B0 = Changeset(doc.get_id(), 'u2', [self.root])
        B0.add_op(Op('sd', [3], offset=1, val=2))  # Deletes 'NO'
        B0.add_op(Op('sd', [5], offset=1, val=2))  # Deletes 'VW'
        B0.add_op(Op('sd', [2], offset=2, val=1))  # 'K'
        B0.set_id('B')
        self.B0 = B0

        # Now B deletes strings
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        B1.add_op(Op('sd', [4], offset=0, val=2))  # 'QR'
        B1.add_op(Op('sd', [0], offset=2, val=1))  # 'C'
        B1.add_op(Op('sd', [6], offset=0, val=1))  # 'Y'
        B1.set_id('B1')
        self.B1 = B1

        # B deletes elements
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        B2.add_op(Op('ad', [], offset=0, val=2))  # ['ABD', 'EFGH']
        B2.add_op(Op('ad', [], offset=4, val=1))  # ['Z']
        B2.set_id('B2')
        self.B2 = B2

        # B deletes a bit more text
        B3 = Changeset(doc.get_id(), 'u2', [B2])
        B3.add_op(Op('sd', [2], offset=0, val=1))  # 'S'
        B3.add_op(Op('sd', [3], offset=0, val=2))  # 'UX'
        B3.set_id('B3')
        self.B3 = B3

    def test_receive_A_first_with_A_ordered_first(self):
        """
        The document receives all of branch A before any of branch B, and
        branch A should get ordered first.
        """
        doc = self.doc

        # Delete strings
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)

        # Delete elements and strings
        doc.receive_changeset(self.A3)
        doc.receive_changeset(self.A4)

        # Delete Strings
        doc.receive_changeset(self.A5)
        result = ['ABCD',
                  'P',
                  'UW',
                  'Z']

        assert doc.get_snapshot() == result

        # Branch B Deletes strings
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index
        result = ['ABCD',
                  'P',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result

        # B deletes strings
        doc.receive_changeset(self.B1)
        result = ['ABD',
                  'P',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result

        # B deletes elemetns
        doc.receive_changeset(self.B2)
        result = ['P',
                  'U']
        assert doc.get_snapshot() == result

        # B deletes strings
        doc.receive_changeset(self.B3)
        result = ['P',
                  '']
        assert doc.get_snapshot() == result

    def test_receive_A_first_with_B_ordered_first(self):
        """
        The document receives all of branch A before any of branch B, and
        branch B should get ordered first.
        """
        doc = self.doc

        # Delete strings
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)

        # Delete elements and strings
        doc.receive_changeset(self.A3)
        doc.receive_changeset(self.A4)

        # Delete Strings
        doc.receive_changeset(self.A5)
        result = ['ABCD',
                  'P',
                  'UW',
                  'Z']

        assert doc.get_snapshot() == result

        # Branch B Deletes strings
        # Force Branch B to be ordered before Branch A
        self.B0.set_id('0B0')
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index
        result = ['ABCD',
                  'P',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result

        # B deletes strings
        doc.receive_changeset(self.B1)
        result = ['ABD',
                  'P',
                  'U',
                  'Z']
        assert doc.get_snapshot() == result

        # B deletes elemetns
        doc.receive_changeset(self.B2)
        result = ['P',
                  'U']
        assert doc.get_snapshot() == result

        # B deletes strings
        doc.receive_changeset(self.B3)
        result = ['P',
                  '']
        assert doc.get_snapshot() == result

    def test_mixed_changesets_with_A_ordered_first(self):
        """
        The document will receive the changesets interleaved with each other,
        but the A branch must be ordered first.
        """
        doc = self.doc

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.B0)
        result = ['ABCD',
                  'EF',
                  'IJL',
                  'MP',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)
        result = ['ABCD',
                  'EF',
                  'IJL',
                  'P',
                  'QRST',
                  'UX',
                  'YZ']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.B1)
        doc.receive_changeset(self.B2)
        result = ['IJL',
                  'P',
                  'ST',
                  'UX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A3)
        doc.receive_changeset(self.A4)
        result = ['P',
                  'U']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A5)
        doc.receive_changeset(self.B3)
        result = ['P',
                  '']
        assert doc.get_snapshot() == result
