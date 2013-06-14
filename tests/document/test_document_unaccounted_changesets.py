from collaborator.document import Document
from collaborator.changeset import Changeset


class TestDocumentUnaccountedChangesets:
    def test_linear(self):
        doc = Document(snapshot='')
        root = doc.get_root_changeset()
        cs0 = Changeset(doc.get_id(), "dummyuser", [root])
        doc.add_to_known_changesets(cs0)
        doc.insert_changeset_into_ordered_list(cs0)
        doc.update_unaccounted_changesets(cs0)

        assert root.get_unaccounted_changesets() == []
        assert cs0.get_unaccounted_changesets() == []

        
        cs1 = Changeset(doc.get_id(), "user1", [cs0])
        doc.add_to_known_changesets(cs1)
        doc.insert_changeset_into_ordered_list(cs1)
        doc.update_unaccounted_changesets(cs1)

        assert root.get_unaccounted_changesets() == []
        assert cs0.get_unaccounted_changesets() == []
        assert cs1.get_unaccounted_changesets() == []

        cs2 = Changeset(doc.get_id(), "user1", [cs1])
        doc.add_to_known_changesets(cs2)
        doc.insert_changeset_into_ordered_list(cs2)
        doc.update_unaccounted_changesets(cs2)

        assert root.get_unaccounted_changesets() == []
        assert cs0.get_unaccounted_changesets() == []
        assert cs1.get_unaccounted_changesets() == []
        assert cs2.get_unaccounted_changesets() == []

    def test_multiple_dependencies(self):
        """
             -- B ---- E
            /         /
        root -- A -- D
            \       /
             -- C --
        """
        doc = Document(snapshot='')
        root = doc.get_root_changeset()
        B = Changeset(doc.get_id(), "user0", [root])
        B.set_id('b')
        doc.receive_changeset(B)

        A = Changeset(doc.get_id(), "user1", [root])
        A.set_id('a')
        doc.receive_changeset(A)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A]
        
        C = Changeset(doc.get_id(), "user2", [root])
        C.set_id('c')
        doc.receive_changeset(C)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A]
        assert C.get_unaccounted_changesets() == [A,B]


        # test_multiple_dependencies_common_base
        D = Changeset(doc.get_id(), "user0", [C,A])
        D.set_id('d')
        doc.receive_changeset(D)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A]
        assert C.get_unaccounted_changesets() == [A,B]
        assert D.get_unaccounted_changesets() == [B]

        E = Changeset(doc.get_id(), 'user1', [B, D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A]
        assert C.get_unaccounted_changesets() == [A,B]
        assert D.get_unaccounted_changesets() == [B]
        assert E.get_unaccounted_changesets() == []


    def test_multiple_css_with_same_multiple_dependencies(self):
        """
          A1        D1
         /         /
        A -- B -- D--F -- G
              \    \/   /
               \   /\  /
                - C--E-
        Both F and E depend on D and C
        """
        doc = Document(snapshot='')
        root = doc.get_root_changeset()
        A = Changeset(doc.get_id(), "user0", [root])
        A.set_id('a')
        doc.receive_changeset(A)
        
        B = Changeset(doc.get_id(), "user1", [A])
        B.set_id('b')
        doc.receive_changeset(B)
        
        C = Changeset(doc.get_id(), "user3", [B])
        C.set_id('c')
        doc.receive_changeset(C)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []

        D = Changeset(doc.get_id(), "user4", [B])
        D.set_id('d')
        doc.receive_changeset(D)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C]

        E = Changeset(doc.get_id(), "user5", [C, D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C]
        assert E.get_unaccounted_changesets() == []

        
        F = Changeset(doc.get_id(), "user6", [C, D])
        F.set_id('f')
        doc.receive_changeset(F)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C]
        assert E.get_unaccounted_changesets() == []
        assert F.get_unaccounted_changesets() == [E]

        A1 = Changeset(doc.get_id(), "user5", [A])
        A1.set_id('1a')
        doc.receive_changeset(A1)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A1]
        assert C.get_unaccounted_changesets() == [A1]
        assert D.get_unaccounted_changesets() == [A1,C]
        assert E.get_unaccounted_changesets() == [A1]
        assert F.get_unaccounted_changesets() == [A1,E]
        assert A1.get_unaccounted_changesets() == []

        D1 = Changeset(doc.get_id(), "user5", [D])
        D1.set_id('1d')
        doc.receive_changeset(D1)
        assert doc.get_ordered_changesets() == [root, A,A1,B,C,D,D1,E,F]
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A1]
        assert C.get_unaccounted_changesets() == [A1]
        assert D.get_unaccounted_changesets() == [A1,C]
        assert E.get_unaccounted_changesets() == [A1,D1]
        assert F.get_unaccounted_changesets() == [A1,D1,E]
        assert A1.get_unaccounted_changesets() == []
        assert D1.get_unaccounted_changesets() == [A1,C]

        G = Changeset(doc.get_id(), "user5", [E,F])
        doc.receive_changeset(G)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == [A1]
        assert C.get_unaccounted_changesets() == [A1]
        assert D.get_unaccounted_changesets() == [A1,C]
        assert E.get_unaccounted_changesets() == [A1,D1]
        assert F.get_unaccounted_changesets() == [A1,D1,E]
        assert A1.get_unaccounted_changesets() == []
        assert D1.get_unaccounted_changesets() == [A1,C]
        assert G.get_unaccounted_changesets() == [A1,D1]

    def test_complex_tree(self):
        """
        Some complex tree.
        
               C -- G -- H -------- K
              /         /            \
        A -- B -- D -- F -- J -- L -- M--
                   \       /
                    E --- I

        Should be:
        A B C G H K D E I J L M
        """
        
        doc = Document(snapshot='')
        root = doc.get_root_changeset()
        A = Changeset(doc.get_id(), "user0", [root])
        A.set_id('A')
        doc.receive_changeset(A)
        
        B = Changeset(doc.get_id(),"user1",[A])
        B.set_id('b')
        doc.receive_changeset(B)
        
        C = Changeset(doc.get_id(),"user3",[B])
        C.set_id('c')
        doc.receive_changeset(C)

        D = Changeset(doc.get_id(),"user4",[B])
        D.set_id('d')
        doc.receive_changeset(D)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C]

        E = Changeset(doc.get_id(),"user5",[D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C]
        assert E.get_unaccounted_changesets() == [C]

        F = Changeset(doc.get_id(),"user6",[D])
        F.set_id('f')
        doc.receive_changeset(F)
        assert doc.get_ordered_changesets() == [root,A,B,C,D,E,F]

        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C]
        assert E.get_unaccounted_changesets() == [C]
        assert F.get_unaccounted_changesets() == [C,E]

        G = Changeset(doc.get_id(),"user5",[C])
        G.set_id('g')
        doc.receive_changeset(G)
        # just a reminder of order now
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,F]

        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E]

        H = Changeset(doc.get_id(),"user5",[G,F])
        H.set_id('h')
        doc.receive_changeset(H)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,F,H]

        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E]
        assert G.get_unaccounted_changesets() == []
        assert H.get_unaccounted_changesets() == [E]

        I = Changeset(doc.get_id(),"user6",[E])
        I.set_id('i')
        doc.receive_changeset(I)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H]

        assert A.get_unaccounted_changesets() == []
        assert B.get_unaccounted_changesets() == []
        assert C.get_unaccounted_changesets() == []
        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E,I]
        assert G.get_unaccounted_changesets() == []
        assert H.get_unaccounted_changesets() == [E,I]
        assert I.get_unaccounted_changesets() == [C,G]

        J = Changeset(doc.get_id(),"user5",[I,F])
        J.set_id('j')
        doc.receive_changeset(J)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,J]

        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E,I]
        assert G.get_unaccounted_changesets() == []
        assert H.get_unaccounted_changesets() == [E,I]
        assert I.get_unaccounted_changesets() == [C,G]
        assert J.get_unaccounted_changesets() == [C,G,H]

        K = Changeset(doc.get_id(),"user5",[H])
        K.set_id('k')
        doc.receive_changeset(K)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,K,J]

        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E,I]
        assert G.get_unaccounted_changesets() == []
        assert H.get_unaccounted_changesets() == [E,I]
        assert I.get_unaccounted_changesets() == [C,G]
        assert J.get_unaccounted_changesets() == [C,G,H,K]
        assert K.get_unaccounted_changesets() == [E,I]

        L = Changeset(doc.get_id(),"user5",[J])
        L.set_id('l')
        doc.receive_changeset(L)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,K,J,L]

        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E,I]
        assert G.get_unaccounted_changesets() == []
        assert H.get_unaccounted_changesets() == [E,I]
        assert I.get_unaccounted_changesets() == [C,G]
        assert J.get_unaccounted_changesets() == [C,G,H,K]
        assert K.get_unaccounted_changesets() == [E,I]
        assert L.get_unaccounted_changesets() == [C,G,H,K]

        M = Changeset(doc.get_id(),"user5",[K,L])
        M.set_id('m')
        doc.receive_changeset(M)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,K,J,L,M]

        assert D.get_unaccounted_changesets() == [C,G]
        assert E.get_unaccounted_changesets() == [C,G]
        assert F.get_unaccounted_changesets() == [C,G,E,I]
        assert G.get_unaccounted_changesets() == []
        assert H.get_unaccounted_changesets() == [E,I]
        assert I.get_unaccounted_changesets() == [C,G]
        assert J.get_unaccounted_changesets() == [C,G,H,K]
        assert K.get_unaccounted_changesets() == [E,I]
        assert L.get_unaccounted_changesets() == [C,G,H,K]
        assert M.get_unaccounted_changesets() == []
