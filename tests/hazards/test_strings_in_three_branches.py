
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


from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestStringsInThreeBranches:

    def test_three_branches(self):
        doc = Document(snapshot='0123456789')
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=3, val=3))
        A0.set_id('A0')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [], offset=7, val='AAAAA'))
        A1.set_id('A1')
        doc.receive_changeset(A1)
        assert doc.get_snapshot() == '0126789AAAAA'

        B0 = Changeset(doc.get_id(), 'u1', [root])
        B0.add_op(Op('sd', [], offset=4, val=3))
        B0.set_id('B0')
        doc.receive_changeset(B0)

        B1 = Changeset(doc.get_id(), 'u1', [B0])
        B1.add_op(Op('si', [], offset=7, val='BBBBB'))
        B1.set_id('B1')
        doc.receive_changeset(B1)
        assert doc.get_snapshot() == '012789AAAAABBBBB'

        C0 = Changeset(doc.get_id(), 'u1', [root])
        C0.add_op(Op('sd', [], offset=5, val=3))
        C0.set_id('C0')
        doc.receive_changeset(C0)
        assert doc.get_snapshot() == '01289AAAAABBBBB'

        C1 = Changeset(doc.get_id(), 'u1', [C0])
        C1.add_op(Op('si', [], offset=7, val='CCCCC'))
        C1.set_id('C1')
        doc.receive_changeset(C1)
        assert doc.get_snapshot() == '01289AAAAABBBBBCCCCC'
