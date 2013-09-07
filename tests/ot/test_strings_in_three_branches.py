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

import random

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestStringsInThreeBranches:

    def setup_method(self, method):
        doc = Document(snapshot='0123456789')
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        self.create_changesets(doc)

    def create_changesets(self, doc):
        root = doc.get_root_changeset()

        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=3, val=3))
        self.A0 = A0

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [], offset=7, val='AAAAA'))
        self.A1 = A1

        B0 = Changeset(doc.get_id(), 'u1', [root])
        B0.add_op(Op('sd', [], offset=4, val=3))
        self.B0 = B0

        B1 = Changeset(doc.get_id(), 'u1', [B0])
        B1.add_op(Op('si', [], offset=7, val='BBBBB'))
        self.B1 = B1

        C0 = Changeset(doc.get_id(), 'u1', [root])
        C0.add_op(Op('sd', [], offset=5, val=3))
        self.C0 = C0

        C1 = Changeset(doc.get_id(), 'u1', [C0])
        C1.add_op(Op('si', [], offset=7, val='CCCCC'))
        self.C1 = C1

    def test_three_branches(self):
        """
        Three branches, A B and C, delete part of the document then insert
        their own text.
        """
        doc = self.doc

        self.A0.set_id('A')
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0126789AAAAA'

        self.B0.set_id('B')
        doc.receive_changeset(self.B0)
        doc.receive_changeset(self.B1)
        assert doc.get_snapshot() == '012789AAAAABBBBB'

        self.C0.set_id('C')
        doc.receive_changeset(self.C0)
        assert doc.get_snapshot() == '01289AAAAABBBBB'

        doc.receive_changeset(self.C1)
        assert doc.get_snapshot() == '01289AAAAABBBBBCCCCC'

    def test_three_branches_change_order_1(self):
        """
        Same test as above, but changing the order in which the branches are
        applied to B A C.
        """
        doc = self.doc

        self.A0.set_id('1A0')
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0126789AAAAA'

        self.B0.set_id('0B0')
        doc.receive_changeset(self.B0)

        doc.receive_changeset(self.B1)
        assert doc.get_snapshot() == '012789BBBBBAAAAA'

        self.C0.set_id('2C0')
        doc.receive_changeset(self.C0)
        assert doc.get_snapshot() == '01289BBBBBAAAAA'

        doc.receive_changeset(self.C1)
        assert doc.get_snapshot() == '01289BBBBBAAAAACCCCC'

    def test_three_branches_change_order_2(self):
        """
        Again, same test, but changing the order in which the branches are
        applied to C B A.
        """
        doc = self.doc

        self.A0.set_id('2A0')
        doc.receive_changeset(self.A0)
        doc.receive_changeset(self.A1)
        assert doc.get_snapshot() == '0126789AAAAA'

        self.B0.set_id('1B0')
        doc.receive_changeset(self.B0)

        doc.receive_changeset(self.B1)
        assert doc.get_snapshot() == '012789BBBBBAAAAA'

        self.C0.set_id('0C0')
        doc.receive_changeset(self.C0)
        assert doc.get_snapshot() == '01289BBBBBAAAAA'

        doc.receive_changeset(self.C1)
        assert doc.get_snapshot() == '01289CCCCCBBBBBAAAAA'

    def test_random(self):
        """
        Randomly insert the changsets into new documents.
        """
        NUMBER_OF_ITERATIONS = 40

        iteration = 0
        while iteration < NUMBER_OF_ITERATIONS:
            doc = Document(snapshot='0123456789')
            self.create_changesets(doc)
            css = [self.A1, self.A0,
                   self.B1, self.B0,
                   self.C1, self.C0]
            while css:
                cs = random.choice(css)
                doc.receive_changeset(cs)
                css.remove(cs)
                # this document will not pull automaticly. flip a coin to see
                # if it should be pulled on this loop
                if random.random() > .5:
                    doc.pull_from_pending_list()
            # pull any remaining changesets from pending list
            doc.pull_from_pending_list()

            # This is the base of the resulting document. Then build up the A's
            # B's and C's.
            result = '01289'
            for cs in doc.get_ordered_changesets():
                if cs is self.A1:
                    result += 'AAAAA'
                elif cs is self.B1:
                    result += 'BBBBB'
                elif cs is self.C1:
                    result += 'CCCCC'
            assert doc.get_snapshot() == result
            iteration += 1
