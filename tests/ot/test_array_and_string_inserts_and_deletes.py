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
This plays through a mix of array/string inserts and deletes in three
branches. Each test in the class just mixed up the order of how branches A, B,
and C are applied to the document.

NOTE: these are far from simple unit tests. This was mostly a fishing
expidition for bugs.
"""

from majormajor.document import _Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestArrayAndStringInsertsAndDeletes:

    def setup_method(self, method):
        s1 = ['ABC',
              'DEF',
              'GHI',
              'JKL',
              'MNO',
              'PQR',
              'STU',
              'VWX',
              'YZ']
        doc = _Document(snapshot=s1)
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        self.root = self.doc.get_root_changeset()

        # establish the reusable changesets

        # Branch A does 1) Array inserts 2) Array deletes 3) string inserts,
        # including into elements it created, 4) string deletes, including into
        # elements it created.
        A0 = Changeset(doc.get_id(), 'u1', [self.root])
        A0.add_op(Op('ai', [], offset=1, val=['012']))
        A0.add_op(Op('ai', [], offset=5, val=['345', '678']))
        A0.set_id('A')
        self.A0 = A0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('ad', [], offset=2, val=1))  # Deletes ['DEF']
        A1.add_op(Op('ad', [], offset=3, val=2))  # Deletes ['JKL', '345']
        self.A1 = A1

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [3], offset=3, val='90'))  # to create '67890'
        A2.add_op(Op('si', [4], offset=1, val='abc'))   # to create 'MabcNo'
        self.A2 = A2

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        A3.add_op(Op('sd', [1], offset=1, val=1))  # to create '02'
        A3.add_op(Op('sd', [6], offset=0, val=2))  # to create 'U'
        self.A3 = A3

        # Branch B makes different edits, but of the same type and order as
        # branch A
        B0 = Changeset(doc.get_id(), 'u1', [self.root])
        B0.add_op(Op('ai', [], offset=0, val=['ghi', 'jkl']))
        B0.add_op(Op('ai', [], offset=5, val=['lmn', 'opq']))
        B0.set_id('B')
        self.B0 = B0

        B1 = Changeset(doc.get_id(), 'u1', [B0])
        B1.add_op(Op('ad', [], offset=1, val=2))  # Deletes ['jkl', 'ABC']
        B1.add_op(Op('ad', [], offset=10, val=1))  # Deletes ['YZ']
        self.B1 = B1

        B2 = Changeset(doc.get_id(), 'u1', [B1])
        B2.add_op(Op('sd', [4], offset=0, val=2))
        B2.add_op(Op('si', [4], offset=1, val='rst'))
        B2.add_op(Op('si', [4], offset=0, val='op'))  # to create 'opqrst'
        B2.add_op(Op('si', [5], offset=0, val='xyz'))  # to create 'xyzJKL'
        B2.add_op(Op('si', [6], offset=1, val='uvw'))  # to create 'MuvwNo'
        self.B2 = B2

        B3 = Changeset(doc.get_id(), 'u1', [B2])
        B3.add_op(Op('sd', [0], offset=2, val=1))  # to create 'gh'
        B3.add_op(Op('sd', [8], offset=1, val=1))  # to create 'SU'
        self.B3 = B3

        # Branch C does a different mix of ops. 1) string insert, 2) array
        # delete 3) array insert, 4) string delete
        C0 = Changeset(doc.get_id(), 'u1', [self.root])
        C0.add_op(Op('si', [2], offset=1, val='XXX'))  # create 'GXXXHI'
        C0.add_op(Op('si', [4], offset=2, val='YYY'))  # create 'MNYYYO'
        C0.set_id('C')
        self.C0 = C0

        C1 = Changeset(doc.get_id(), 'u1', [C0])
        C1.add_op(Op('ad', [], offset=4, val=2))  # Deletes ['MNYYYO', 'PQR']
        C1.add_op(Op('ad', [], offset=6, val=1))  # Deletes ['YZ']
        self.C1 = C1

        C2 = Changeset(doc.get_id(), 'u1', [C1])
        C2.add_op(Op('ai', [], offset=0, val=['lorem']))
        C2.add_op(Op('ai', [], offset=6, val=['ipsum']))
        self.C2 = C2

        C3 = Changeset(doc.get_id(), 'u1', [C2])
        C3.add_op(Op('sd', [5], offset=1, val=2))  # to delete 'TU'
        C3.add_op(Op('sd', [6], offset=0, val=2))  # to create 'sum'
        C3.add_op(Op('sd', [7], offset=2, val=1))  # to create 'VW'
        self.C3 = C3

    def test_order_branches_A_B_C(self):
        """
        Document will order the branches ABC
        """
        doc = self.doc

        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)
        result = ['ABC',
                  '02',
                  'GHI',
                  '67890',
                  'MabcNO',
                  'PQR',
                  'U',
                  'VWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # Branch B array inserts
        doc.receive_changeset(self.B0)

        # Check that branch A gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index < b_index
        result = ['ghi',
                  'jkl',
                  'ABC',
                  '02',
                  'GHI',
                  'lmn',
                  'opq',
                  '67890',
                  'MabcNO',
                  'PQR',
                  'U',
                  'VWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B deletes from array
        doc.receive_changeset(self.B1)
        result = ['ghi',
                  '02',
                  'GHI',
                  'lmn',
                  'opq',
                  '67890',
                  'MabcNO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        # B inserts strings
        doc.receive_changeset(self.B2)
        result = ['ghi',
                  '02',
                  'GHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'MabcuvwNO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        # B deletes strings
        doc.receive_changeset(self.B3)
        result = ['gh',
                  '02',
                  'GHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'MabcuvwNO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        # APPLY branch C
        doc.receive_changeset(self.C0)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'MabcuvwNYYYO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.C1)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.C2)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'U',
                  'ipsum',
                  'VWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.C3)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  '',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

    def test_order_branches_B_A_C(self):
        """
        """
        doc = self.doc

        # Force Branch A to be Second
        self.A0.set_id('1A0')
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        doc.receive_changeset(self.A2)
        doc.receive_changeset(self.A3)

        # Force Branch B to be first
        self.B0.set_id('0B0')
        doc.receive_changeset(self.B0)

        # Check that branch B gets ordered first
        a_index = doc.get_ordered_changesets().index(self.A0)
        b_index = doc.get_ordered_changesets().index(self.B0)
        assert a_index > b_index
        result = ['ghi',
                  'jkl',
                  'ABC',
                  '02',
                  'GHI',
                  'lmn',
                  'opq',
                  '67890',
                  'MabcNO',
                  'PQR',
                  'U',
                  'VWX',
                  'YZ']
        assert doc.get_snapshot() == result

        # B deletes from array
        doc.receive_changeset(self.B1)
        result = ['ghi',
                  '02',
                  'GHI',
                  'lmn',
                  'opq',
                  '67890',
                  'MabcNO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        # B inserts strings
        doc.receive_changeset(self.B2)
        result = ['ghi',
                  '02',
                  'GHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'MuvwabcNO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        # B deletes strings
        doc.receive_changeset(self.B3)
        result = ['gh',
                  '02',
                  'GHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'MuvwabcNO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        # Branch C is applied third
        doc.receive_changeset(self.C0)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'MuvwabcNYYYO',
                  'PQR',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.C1)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'U',
                  'VWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.C2)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'U',
                  'ipsum',
                  'VWX']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.C3)
        result = ['gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  '',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

    def test_order_branches_C_B_A(self):
        """
        The document receives changesets from the two branches in a mixed
        order, and branch A should get ordered first.
        """
        doc = self.doc

        # force branch C to be ordered first
        self.C0.set_id('0C0')
        doc.receive_changeset(self.C0)
        doc.receive_changeset(self.C1)
        doc.receive_changeset(self.C2)
        doc.receive_changeset(self.C3)
        result = ['lorem',
                  'ABC',
                  'DEF',
                  'GXXXHI',
                  'JKL',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        # force branch B to be ordered second
        self.B0.set_id('1B0')
        doc.receive_changeset(self.B0)
        result = ['lorem',
                  'ghi',
                  'jkl',
                  'ABC',
                  'DEF',
                  'GXXXHI',
                  'lmn',
                  'opq',
                  'JKL',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.B1)
        result = ['lorem',
                  'ghi',
                  'DEF',
                  'GXXXHI',
                  'lmn',
                  'opq',
                  'JKL',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.B2)
        result = ['lorem',
                  'ghi',
                  'DEF',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  'xyzJKL',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.B3)
        result = ['lorem',
                  'gh',
                  'DEF',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  'xyzJKL',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        # force branch A to be last
        self.A0.set_id('2A0')
        doc.receive_changeset(self.A0)
        result = ['lorem',
                  'gh',
                  '012',
                  'DEF',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  'xyzJKL',
                  '345',
                  '678',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A1)
        result = ['lorem',
                  'gh',
                  '012',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '678',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A2)
        result = ['lorem',
                  'gh',
                  '012',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  'S',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result

        doc.receive_changeset(self.A3)
        result = ['lorem',
                  'gh',
                  '02',
                  'GXXXHI',
                  'lmn',
                  'opqrst',
                  '67890',
                  '',
                  'sum',
                  'VW']
        assert doc.get_snapshot() == result
