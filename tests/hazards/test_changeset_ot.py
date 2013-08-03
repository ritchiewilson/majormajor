
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

import pytest

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset

class TestChangesetOT:

    def test_hazard_on_multiple_deletes(self):
        """
        A Hazard is applied to a branch with multiple deletes. The hazard
        should affect one delete but not the other.
        """
        doc = Document(snapshot='123abcde789')
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        # construct branch A, which begins with a string delete, then
        # adds text
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=3, val=5))
        A0.set_id('A')
        doc.receive_changeset(A0)

        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [], offset=3, val='456'))
        doc.receive_changeset(A1)
        assert doc.get_snapshot() == '123456789'

        # Branch B has common parent with A. B has three deletes. The
        # first creates a hazard, the second should be affected by it,
        # the third should not.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('sd', [], offset=4, val=2)
        B0.add_op(opB0)
        B0.set_id('B')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == '123456789'
        assert opB0.t_offset == 6
        assert opB0.t_val == 0

        # Delete range affected by hazard
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('sd', [], offset=6, val=2)
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        assert doc.get_snapshot() == '1234569'
        assert opB1.t_offset == 6
        assert opB1.t_val == 2

        # Delete Range unaffected by hazzard
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        opB2 = Op('sd', [], offset=1, val=1)
        B2.add_op(opB2)
        B2.set_id('B2')
        doc.receive_changeset(B2)
        assert doc.get_snapshot() == '134569'
        assert opB2.t_offset == 1
        assert opB2.t_val == 1

        # combine these braches again
        C = Changeset(doc.get_id(), 'u2', [A1, B2])
        C.add_op(Op('si', [], offset=1, val='2'))
        C.add_op(Op('si', [], offset=6, val='78'))
        doc.receive_changeset(C)
        assert doc.get_snapshot() == '123456789'


    def test_hazard_base_branch_contains_multiple_deletes(self):
        """

        """
        """  01234567890123456 """
        s = 'ab123cd456gh789ik'
        doc = Document(snapshot=s)
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        # construct branch A, which begins with a string delete, then
        # adds text
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=7, val=2))
        A0.set_id('A')
        doc.receive_changeset(A0)
        
        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('sd', [], offset=10, val=3))
        doc.receive_changeset(A1)
        
        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [], offset=7, val='ef'))
        doc.receive_changeset(A2)
        assert doc.get_snapshot() == 'ab123cdef6ghik'

        # Branch B has common parent with A. First it deletes a
        # partialy overlaping range to create a hazard.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('sd', [], offset=8, val=2)
        B0.add_op(opB0)
        B0.set_id('B')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == 'ab123cdefghik'
        assert opB0.t_offset == 9
        assert opB0.t_val == 1

        # Delete range affected by hazard
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('sd', [], offset=10, val=2)
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        assert doc.get_snapshot() == 'ab123cdefghik'
        assert opB1.t_offset == 11
        assert opB1.t_val == 0

        # Delete Range unaffected by hazzard
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        opB2 = Op('sd', [], offset=2, val=3)
        B2.add_op(opB2)
        B2.set_id('B2')
        doc.receive_changeset(B2)
        assert doc.get_snapshot() == 'abcdefghik'
        assert opB2.t_offset == 2
        assert opB2.t_val == 3

        # combine these braches again
        C = Changeset(doc.get_id(), 'u2', [A2, B2])
        C.add_op(Op('si', [], offset=9, val='j'))
        doc.receive_changeset(C)
        assert doc.get_snapshot() == 'abcdefghijk'


    def test_multiple_delete_hazards(self):
        """

        """
        s = '0123456789'
        doc = Document(snapshot=s)
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        # construct branch A, which deletes all but the first three
        # and last three characters.
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=4, val=2))
        A0.set_id('A')
        doc.receive_changeset(A0)
        assert doc.get_snapshot() == '01236789'
        
        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('sd', [], offset=3, val=2))
        doc.receive_changeset(A1)
        assert doc.get_snapshot() == '012789'

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('sd', [], offset=2, val=2))
        doc.receive_changeset(A2)
        assert doc.get_snapshot() == '0189'

        # Branch B has common parent with A. It deletes all but 'xyz'

        # User saw '0123456789' and deleted '3456', which was already
        # deleted in branch A.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('sd', [], offset=3, val=4)
        B0.add_op(opB0)
        B0.set_id('B')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == '0189'
        assert opB0.t_offset == 2
        assert opB0.t_val == 0

        # User saw '012789' and deleted '27', which was already
        # deleted in branch A.
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('sd', [], offset=2, val=2)
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        assert doc.get_snapshot() == '0189'
        assert opB1.t_offset == 2
        assert opB1.t_val == 0

        # Delete Range unaffected by hazzard
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        opB2 = Op('sd', [], offset=1, val=2)
        B2.add_op(opB2)
        B2.set_id('B2')
        doc.receive_changeset(B2)
        assert doc.get_snapshot() == '09'
        assert opB2.t_offset == 1
        assert opB2.t_val == 2

        # combine these braches again
        C = Changeset(doc.get_id(), 'u2', [A2, B2])
        C.add_op(Op('si', [], offset=1, val='12345678'))
        doc.receive_changeset(C)
        assert doc.get_snapshot() == '0123456789'

    def test_multiple_delete_hazards2(self):
        """

        """
        s = '0123456789TARGET'
        doc = Document(snapshot=s)
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        # construct branch A, which deletes the '234567' in three ops.

        # first delete '45'
        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=4, val=2))
        A0.set_id('A0')
        doc.receive_changeset(A0)
        assert doc.get_snapshot() == '01236789TARGET'

        # delete '36'
        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('sd', [], offset=3, val=2))
        A1.set_id('A1')
        doc.receive_changeset(A1)
        assert doc.get_snapshot() == '012789TARGET'

        # delete '27'
        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('sd', [], offset=2, val=2))
        A2.set_id('A2')
        doc.receive_changeset(A2)
        assert doc.get_snapshot() == '0189TARGET'

        # Branch B has common parent with A. It deletes all but
        # 'TARGET' in three ops.

        # User Saw '0123456789TARGET', deleted '234', which branch A
        # already did.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('sd', [], offset=2, val=3)
        B0.add_op(opB0)
        B0.set_id('B0')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == '0189TARGET'
        assert opB0.t_offset == 2
        assert opB0.t_val == 0

        # User Saw '0156789TARGET', deleted '567', which branch A
        # already did.
        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('sd', [], offset=2, val=3)
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)

        assert doc.get_snapshot() == '0189TARGET'
        assert opB1.t_offset == 2
        assert opB1.t_val == 0

        # User Saw '0189TARGET', deleted '0189', which branch A has
        # NOT done.
        B2 = Changeset(doc.get_id(), 'u2', [B1])
        opB2 = Op('sd', [], offset=0, val=4)
        B2.add_op(opB2)
        B2.set_id('B2')
        doc.receive_changeset(B2)
        assert doc.get_snapshot() == 'TARGET'
        assert opB2.t_offset == 0
        assert opB2.t_val == 4

    def test_overlaping_deletes_then_string_insert(self):

        s = 'ZZZZZZZAAAAAAAAAAAAAAAAAAAAAAAAAXXXXX'
        doc = Document(snapshot=s)
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=0, val=32))
        A0.add_op(Op('si', [], offset=0, val='T'))
        A0.set_id('A0')
        doc.receive_changeset(A0)
        
        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [], offset=1, val="h"))
        A1.add_op(Op('si', [], offset=2, val="e"))
        A1.add_op(Op('si', [], offset=3, val=" "))
        A1.set_id('A1')
        doc.receive_changeset(A1)

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [], offset=4, val="Q"))
        A2.add_op(Op('si', [], offset=5, val="u"))
        A2.add_op(Op('si', [], offset=6, val="i"))
        A2.set_id('A2')
        doc.receive_changeset(A2)

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        A3.add_op(Op('si', [], offset=7, val="c"))
        A3.add_op(Op('si', [], offset=8, val="k"))
        A3.add_op(Op('si', [], offset=9, val=" "))
        A3.set_id('A3')
        doc.receive_changeset(A3)
        assert doc.get_snapshot() == 'The Quick XXXXX'


        # Branch B has common parent with A. It deletes all but
        # '789', then inserts 'Hello' at the start.
        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('sd', [], offset=7, val=30)
        B0.add_op(opB0)
        B0.set_id('B0')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == 'The Quick '
        assert opB0.t_offset == 10
        assert opB0.t_val == 5

        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('si', [], offset=7, val='Brown Fox.')
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        assert doc.get_snapshot() == 'The Quick Brown Fox.'
        assert opB1.t_offset == 10

    def test_overlaping_deletes_then_string_insert2(self):

        s = 'ZZZZZZZAAAAAAAAAAAAAAAAAAAAAAAAAXXXXX'
        doc = Document(snapshot=s)
        doc.HAS_EVENT_LOOP = False
        root = doc.get_root_changeset()

        A0 = Changeset(doc.get_id(), 'u1', [root])
        A0.add_op(Op('sd', [], offset=0, val=32))
        A0.add_op(Op('si', [], offset=0, val='T'))
        A0.set_id('2')
        doc.receive_changeset(A0)
        
        A1 = Changeset(doc.get_id(), 'u1', [A0])
        A1.add_op(Op('si', [], offset=1, val="h"))
        A1.add_op(Op('si', [], offset=2, val="e"))
        A1.add_op(Op('si', [], offset=3, val=" "))
        A1.set_id('A1')
        doc.receive_changeset(A1)

        A2 = Changeset(doc.get_id(), 'u1', [A1])
        A2.add_op(Op('si', [], offset=4, val="Q"))
        A2.add_op(Op('si', [], offset=5, val="u"))
        A2.add_op(Op('si', [], offset=6, val="i"))
        A2.set_id('A2')
        doc.receive_changeset(A2)

        A3 = Changeset(doc.get_id(), 'u1', [A2])
        A3.add_op(Op('si', [], offset=7, val="c"))
        A3.add_op(Op('si', [], offset=8, val="k"))
        A3.add_op(Op('si', [], offset=9, val=" "))
        A3.set_id('A3')
        doc.receive_changeset(A3)
        assert doc.get_snapshot() == 'The Quick XXXXX'

        B0 = Changeset(doc.get_id(), 'u2', [root])
        opB0 = Op('sd', [], offset=7, val=30)
        B0.add_op(opB0)
        B0.set_id('1')
        doc.receive_changeset(B0)
        assert doc.get_snapshot() == 'The Quick '
        assert opB0.t_offset == 7
        assert opB0.t_val == 30

        B1 = Changeset(doc.get_id(), 'u2', [B0])
        opB1 = Op('si', [], offset=7, val='Brown Fox.')
        B1.add_op(opB1)
        B1.set_id('B1')
        doc.receive_changeset(B1)
        assert doc.get_snapshot() == 'Brown Fox.The Quick '
        assert opB1.t_offset == 7
