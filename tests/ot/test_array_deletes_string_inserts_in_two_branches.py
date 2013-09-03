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
Set up two branches to do array deletes and string insertions. Each branch
1) inserts text, 2) deletes array elements, and 3) inserts strings
"""

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArrayDeletesAndStringInsertsInTwoBranches:

    def setup_method(self, method):
        s1 = ['ABCD',
              'EFGH',
              'IJKL',
              'MNOP',
              'QRST',
              'UVWX',
              'YZ']
        doc = Document(snapshot=s1)
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        self.root = self.doc.get_root_changeset()

        # establish the reusable changesets

        # Branch A does 1) String inserts 2) Array deletes, and 3) string
        # inserts
        A0 = Changeset(doc.get_id(), 'u1', [self.root])
        A0.add_op(Op('si', [0], offset=2, val='0123'))
        A0.set_id('A')
        self.A0 = A0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [0], offset=6, val='4'))
        self.A1 = A1

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [4], offset=1, val='567'))
        A2.add_op(Op('si', [6], offset=0, val='89'))
        self.A2 = A2

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        A3.add_op(Op('ad', [], offset=1, val=2))
        self.A3 = A3

        A4 = Changeset(doc.get_id(), 'u1', [A3])
        A4.add_op(Op('ad', [], offset=3, val=1))
        A4.add_op(Op('si', [1], offset=1, val='ab'))
        self.A4 = A4

        A5 = Changeset(doc.get_id(), 'u1', [A4])
        A5.add_op(Op('si', [3], offset=4, val='c'))
        self.A5 = A5

        # Branch B Also does string inserts, then array delets, then string
        # inserts
        B0 = Changeset(doc.get_id(), 'u2', [self.root])
        B0.add_op(Op('si', [4], offset=2, val='fg'))
        B0.add_op(Op('si', [6], offset=0, val='h'))
        B0.add_op(Op('si', [1], offset=4, val='ij'))
        B0.add_op(Op('si', [2], offset=2, val='k'))
        B0.add_op(Op('si', [5], offset=1, val='l'))
        B0.add_op(Op('si', [0], offset=3, val='m'))
        B0.add_op(Op('si', [3], offset=0, val='nop'))
        B0.set_id('B')
        self.B0 = B0

        # Now B deletes array elements
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        B1.add_op(Op('ad', [], offset=0, val=2))
        B1.add_op(Op('ad', [], offset=4, val=1))
        B1.set_id('B1')
        self.B1 = B1

        # B inserts strings into each original element, including elements A
        # had edited
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        B2.add_op(Op('si', [0], offset=3, val='qr'))
        B2.add_op(Op('si', [1], offset=4, val='st'))
        B2.add_op(Op('si', [2], offset=5, val='uv'))
        B2.add_op(Op('si', [3], offset=0, val='wxyz'))
        B2.set_id('B2')
        self.B2 = B2

    def test_receive_A_first_with_A_ordered_first(self):
        """
        The document receives all of branch A before any of branch B, and
        branch A should get ordered first.
        """
        doc = self.doc

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)
        result = ['AB01234CD',
                  'MabNOP',
                  'Q567RST',
                  '89YZc']
        assert doc.get_snapshot() == result

        # Branch B inserts strings, including into elements which have been
        # deleted
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index
        result = ['AB01234CmD',
                  'nopMabNOP',
                  'Q567RfgST',
                  '89hYZc']
        assert doc.get_snapshot() == result

        # B deletes from array
        doc.receive_changeset(self.B1)
        result = ['nopMabNOP',
                  'Q567RfgST']
        assert doc.get_snapshot() == result

        # B inserts strings
        doc.receive_changeset(self.B2)
        result = ['nopMabstNOP',
                  'Q567RfgSuvT']
        assert doc.get_snapshot() == result

    def test_receive_A_first_with_B_ordered_first(self):
        """
        The document receives all of branch A before any of branch B, and
        branch B should get ordered first.
        """
        doc = self.doc

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)

        # Branch B inserts strings, including into elements which have been
        # deleted
        self.B0.set_id('0B0')
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index
        result = ['AB01234CmD',
                  'nopMabNOP',
                  'Q567RfgST',
                  'h89YZc']
        assert doc.get_snapshot() == result

        # B deletes from array
        doc.receive_changeset(self.B1)
        result = ['nopMabNOP',
                  'Q567RfgST']
        assert doc.get_snapshot() == result

        # B inserts strings
        doc.receive_changeset(self.B2)
        result = ['nopMstabNOP',
                  'Q567RfgSuvT']
        assert doc.get_snapshot() == result

    def test_interleave_branches_with_A_ordered_first(self):
        """
        The document receives changesets from the two branches in a mixed
        order, and branch A should get ordered first.
        """
        doc = self.doc

        doc.receive_changeset(self.B0)
        doc.receive_changeset(self.A0)
        result = ['AB0123CmD',
                  'EFGHij',
                  'IJkKL',
                  'nopMNOP',
                  'QRfgST',
                  'UlVWX',
                  'hYZ']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.B1)
        result = ['IJkKL',
                  'nopMNOP',
                  'QRfgST',
                  'UlVWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)
        result = ['nopMNOP',
                  'Q567RfgST',
                  'UlVWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A4)
        result = ['nopMabNOP',
                  'Q567RfgST']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.B2)
        doc.receive_changeset(self.A5)
        result = ['nopMabstNOP',
                  'Q567RfgSuvT']
        assert doc.get_snapshot() == result
