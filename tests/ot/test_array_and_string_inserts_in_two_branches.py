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
Set up two branches to do array and string insertions. Each branch 1)
inserts array elements, 2) Inserts strings into their now private elements and
3) inserts strings into the original array elements known by both branches.
"""

from majormajor.document import _Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArrayAndStringInsertsInTwoBranches:

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

        # Branch A inserts two new array elements, and add text to those two.
        # It also inserts text into three existing elements, before any array
        # insert, in the middle, and after the last array insert.
        A0 = Changeset(doc.get_id(), 'u1', [self.root])
        vA0 = ['02', '4']
        A0.add_op(Op('ai', [], offset=2, val=vA0))
        A0.set_id('A')
        self.A0 = A0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        vA1 = ['5', '89']
        A1.add_op(Op('ai', [], offset=6, val=vA1))
        self.A1 = A1

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [2], offset=1, val='1'))
        A2.add_op(Op('si', [3], offset=0, val='3'))
        self.A2 = A2

        A3 = Changeset(doc.get_id(), 'u1', [self.A2])
        A3.add_op(Op('si', [6], offset=1, val='67'))
        self.A3 = A3

        A4 = Changeset(doc.get_id(), 'u1', [A3])
        A4.add_op(Op('si', [0], offset=0, val='a'))
        A4.add_op(Op('si', [4], offset=0, val='b'))
        self.A4 = A4

        A5 = Changeset(doc.get_id(), 'u1', [A4])
        A5.add_op(Op('si', [9], offset=0, val='c'))
        self.A5 = A5

        # Branch B performs similar actions to branch A.
        B0 = Changeset(doc.get_id(), 'u2', [self.root])
        vB0a, vB0b = ['lm', 'ipsm'], ['or', 't']
        opB0a = Op('ai', [], offset=2, val=vB0a)
        B0.add_op(opB0a)
        opB0b = Op('ai', [], offset=6, val=vB0b)
        B0.add_op(opB0b)
        B0.set_id('B')
        self.B0 = B0

        # Now B inserts strings into the elements it created
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        B1.add_op(Op('si', [2], offset=1, val='ore'))
        B1.add_op(Op('si', [3], offset=3, val='u'))
        B1.add_op(Op('si', [6], offset=0, val='dol'))
        B1.add_op(Op('si', [7], offset=0, val='si'))
        B1.set_id('B1')
        self.B1 = B1

        # B inserts strings into each original element, including elements A
        # had edited
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        B2.add_op(Op('si', [0], offset=0, val='t'))
        B2.add_op(Op('si', [1], offset=0, val='u'))
        B2.add_op(Op('si', [4], offset=0, val='v'))
        B2.add_op(Op('si', [5], offset=0, val='w'))
        B2.add_op(Op('si', [8], offset=0, val='x'))
        B2.add_op(Op('si', [9], offset=0, val='y'))
        B2.add_op(Op('si', [10], offset=0, val='z'))
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

        # Insert strings into the new elements
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)

        # Insert strings into the existing elements
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)

        result = ['aABCD',
                  'EFGH',
                  '012',
                  '34',
                  'bIJKL',
                  'MNOP',
                  '567',
                  '89',
                  'QRST',
                  'cUVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Branch B inserts array elements
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index

        result = ['aABCD',
                  'EFGH',
                  '012',
                  '34',
                  'lm',
                  'ipsm',
                  'bIJKL',
                  'MNOP',
                  '567',
                  '89',
                  'or',
                  't',
                  'QRST',
                  'cUVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B inserts strings into elements it created
        doc.receive_changeset(self.B1)
        result = ['aABCD',
                  'EFGH',
                  '012',
                  '34',
                  'lorem',
                  'ipsum',
                  'bIJKL',
                  'MNOP',
                  '567',
                  '89',
                  'dolor',
                  'sit',
                  'QRST',
                  'cUVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B inserts strings into all elements known to A and B
        doc.receive_changeset(self.B2)
        result = ['atABCD',
                  'uEFGH',
                  '012',
                  '34',
                  'lorem',
                  'ipsum',
                  'bvIJKL',
                  'wMNOP',
                  '567',
                  '89',
                  'dolor',
                  'sit',
                  'xQRST',
                  'cyUVWX',
                  'zYZ']
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

        # Insert strings into the new elements
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)

        # Insert strings into the existing elements
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)

        # Force Branch B to be ordered before Branch A
        self.B0.set_id('0B0')
        doc.receive_changeset(self.B0)

        # Check that branch B gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index

        result = ['aABCD',
                  'EFGH',
                  'lm',
                  'ipsm',
                  '012',
                  '34',
                  'bIJKL',
                  'MNOP',
                  'or',
                  't',
                  '567',
                  '89',
                  'QRST',
                  'cUVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B inserts strings into elements it created
        doc.receive_changeset(self.B1)
        result = ['aABCD',
                  'EFGH',
                  'lorem',
                  'ipsum',
                  '012',
                  '34',
                  'bIJKL',
                  'MNOP',
                  'dolor',
                  'sit',
                  '567',
                  '89',
                  'QRST',
                  'cUVWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B inserts strings into all elements known to A and B
        doc.receive_changeset(self.B2)
        result = ['taABCD',
                  'uEFGH',
                  'lorem',
                  'ipsum',
                  '012',
                  '34',
                  'vbIJKL',
                  'wMNOP',
                  'dolor',
                  'sit',
                  '567',
                  '89',
                  'xQRST',
                  'ycUVWX',
                  'zYZ']
        assert doc.get_snapshot() == result

    def test_receive_B_first_with_A_ordered_first(self):
        """
        The document receives all of branch B before any of branch A, and
        branch A should get ordered first.
        """
        doc = self.doc

        # Branch B inserts some array elements
        doc.receive_changeset(self.B0)

        # B inserts strings into elements it created
        doc.receive_changeset(self.B1)

        # B inserts strings into all elements known to A and B
        doc.receive_changeset(self.B2)
        result = ['tABCD',
                  'uEFGH',
                  'lorem',
                  'ipsum',
                  'vIJKL',
                  'wMNOP',
                  'dolor',
                  'sit',
                  'xQRST',
                  'yUVWX',
                  'zYZ']
        assert doc.get_snapshot() == result

        # Insert some array elements
        doc.receive_changeset(self.A0)
        result = ['tABCD',
                  'uEFGH',
                  '02',
                  '4',
                  'lorem',
                  'ipsum',
                  'vIJKL',
                  'wMNOP',
                  'dolor',
                  'sit',
                  'xQRST',
                  'yUVWX',
                  'zYZ']
        assert doc.get_snapshot() == result

        # Insert two more Array elements
        doc.receive_changeset(self.A1)
        result = ['tABCD',
                  'uEFGH',
                  '02',
                  '4',
                  'lorem',
                  'ipsum',
                  'vIJKL',
                  'wMNOP',
                  '5',
                  '89',
                  'dolor',
                  'sit',
                  'xQRST',
                  'yUVWX',
                  'zYZ']
        assert doc.get_snapshot() == result

        # Insert strings into the new elements
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)
        result = ['tABCD',
                  'uEFGH',
                  '012',
                  '34',
                  'lorem',
                  'ipsum',
                  'vIJKL',
                  'wMNOP',
                  '567',
                  '89',
                  'dolor',
                  'sit',
                  'xQRST',
                  'yUVWX',
                  'zYZ']
        assert doc.get_snapshot() == result

        # Insert strings into the existing elements
        doc.receive_changeset(self.A4)
        doc.receive_changeset(self.A5)
        result = ['atABCD',
                  'uEFGH',
                  '012',
                  '34',
                  'lorem',
                  'ipsum',
                  'bvIJKL',
                  'wMNOP',
                  '567',
                  '89',
                  'dolor',
                  'sit',
                  'xQRST',
                  'cyUVWX',
                  'zYZ']
        assert doc.get_snapshot() == result
