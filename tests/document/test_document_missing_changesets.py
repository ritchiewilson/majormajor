
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

class TestDocumentMissingChangesets:

    def test_missing_changesets(self):
        doc = Document(snapshot='')
        doc.HAS_EVENT_LOOP = False
        assert doc.missing_changesets == set([])
        assert doc.pending_new_changesets == []
        
        root = doc.get_root_changeset()
        A = Changeset(doc.get_id(), "dummyuser", [root])
        doc.receive_changeset(A)
        assert doc.missing_changesets == set([])
        assert doc.pending_new_changesets == []

        # Just one Changeset gets put in pending list
        B = Changeset(doc.get_id(), "user1", ["C"])
        B.set_id("B")
        doc.receive_changeset(B)
        assert doc.get_ordered_changesets() == [root, A]
        assert doc.missing_changesets == set(["C"])
        assert doc.pending_new_changesets == [B]

        C = Changeset(doc.get_id(), "user1", [A])
        C.set_id("C")
        doc.receive_changeset(C)
        assert doc.missing_changesets == set([])
        assert doc.pending_new_changesets == []
        assert B.get_parents() == [C]
        assert doc.get_ordered_changesets() == [root, A, C, B]

        # Now a string of changesets put on pending list
        D = Changeset(doc.get_id(), "user1", ["G"])
        D.set_id("D")
        doc.receive_changeset(D)
        assert doc.missing_changesets == set(["G"])
        assert doc.pending_new_changesets == [D]
        assert doc.get_ordered_changesets() == [root, A, C, B]

        E = Changeset(doc.get_id(), "user1", ["D"])
        E.set_id("E")
        doc.receive_changeset(E)
        assert E.get_parents() == [D]
        assert doc.missing_changesets == set(["G"])
        assert doc.pending_new_changesets == [D, E]
        assert doc.get_ordered_changesets() == [root, A, C, B]

        F = Changeset(doc.get_id(), "user1", ["E"])
        F.set_id("F")
        doc.receive_changeset(F)
        assert doc.missing_changesets ==set( ["G"])
        assert doc.pending_new_changesets == [D, E, F]
        assert doc.get_ordered_changesets() == [root, A, C, B]

        G = Changeset(doc.get_id(), "user1", ["C"])
        G.set_id("G")
        doc.receive_changeset(G)
        assert doc.missing_changesets == set([])
        assert doc.pending_new_changesets == []
        assert doc.get_ordered_changesets() == [root, A, C, B, G, D, E, F]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        
