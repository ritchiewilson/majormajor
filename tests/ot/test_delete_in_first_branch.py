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

import pytest

from majormajor.document import _Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestOTDelteInOneBranch:

    def test_delete_in_first_branch(self):
        """
        """
        doc = _Document(snapshot='abcdefghij')
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        # construct branch A, which begins with a string delete
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=5, val=5))
        A0.set_id('A')
        doc.receive_changeset(A0)
        assert doc.get_snapshot() == 'abcde'

        # Branch B has common parent with A. It inserts strings at the end
        # which should not be deleted.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        for i in xrange(10):
            op = Op('si', [], offset=i, val=str(i))
            B0.add_op(op)
        B0.set_id('B')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == '0123456789abcde'

    def test_delete_in_second_branch(self):
        """
        """
        doc = _Document(snapshot='abcdefghij')
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        # construct branch A, which begins with a string delete
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=5, val=5))
        A0.set_id('2A')
        doc.receive_changeset(A0)
        assert doc.get_snapshot() == 'abcde'

        # Branch B has common parent with A. It inserts strings at the end
        # which should not be deleted.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        for i in xrange(10):
            op = Op('si', [], offset=10 + i, val=str(i))
            B0.add_op(op)
        B0.set_id('1B')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == 'abcde0123456789'
