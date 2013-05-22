from collaborator.document import Document
from collaborator.op import Op
from collaborator.changeset import Changeset


class TestDocumentDependencyTreeToList:

    def test_initial_dependency(self):
        doc = Document(snapshot='')
        assert doc.get_open_changeset() == None
        assert doc.get_ordered_changesets() == [doc.get_root_changeset()]

        assert doc.get_dependencies() == [doc.get_root_changeset()]

    def test_sequential_changeset(self):
        doc = Document(snapshot='')
        root = doc.get_root_changeset()
        cs0 = Changeset(doc.get_id(), "dummyuser", [root])
        rid = root.get_id()
        assert doc.receive_changeset(cs0)
        assert rid == doc.get_root_changeset().get_id()
        assert root.get_children() == [cs0]
        assert doc.get_dependencies() == [cs0]
        assert doc.get_ordered_changesets() == [root, cs0]


        cs1 = Changeset(doc.get_id(), "user1", [cs0])
        assert doc.receive_changeset(cs1)
        assert doc.get_ordered_changesets() == [root, cs0, cs1]
        assert doc.get_dependencies() == [cs1]

        cs2 = Changeset(doc.get_id(), "user1", [cs1])
        assert doc.receive_changeset(cs2)
        assert doc.get_ordered_changesets() == [root, cs0, cs1, cs2]
        assert doc.get_dependencies() == [cs2]

        

    def test_multiple_dependencies(self):
        doc = Document(snapshot='')
        root = doc.get_root_changeset()
        cs0 = Changeset(doc.get_id(), "user0", [root])
        cs0.set_id('b')
        doc.receive_changeset(cs0)

        cs1 = Changeset(doc.get_id(), "user1", [root])
        cs1.set_id('a')
        doc.receive_changeset(cs1)
        assert set(doc.get_dependencies()) == set([cs0,cs1])
        assert doc.get_ordered_changesets() == [root, cs1, cs0]

        cs2 = Changeset(doc.get_id(), "user2", [root])
        cs2.set_id('c')
        doc.receive_changeset(cs2)
        assert set(doc.get_dependencies()) == set([cs0,cs1,cs2])
        assert doc.get_ordered_changesets() == [root, cs1, cs0, cs2]


        # test_multiple_dependencies_common_base
        cs3 = Changeset(doc.get_id(), "user0", [cs2,cs1])
        cs3.set_id('d')
        doc.receive_changeset(cs3)
        assert set(doc.get_dependencies()) == set([cs0,cs3])
        assert doc.get_ordered_changesets() == [root, cs1, cs2, cs3, cs0]

        cs4 = Changeset(doc.get_id(), 'user1', [cs0, cs3])
        cs4.set_id('e')
        doc.receive_changeset(cs4)
        assert doc.get_dependencies() == [cs4]
        assert doc.get_ordered_changesets() == [root, cs1, cs2, cs3, cs0, cs4]


    def test_multiple_css_with_same_multiple_dependencies(self):
        """
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
        assert doc.get_ordered_changesets() == [root, A]
        
        B = Changeset(doc.get_id(), "user1", [A])
        B.set_id('b')
        doc.receive_changeset(B)
        assert doc.get_ordered_changesets() == [root, A, B]
        
        C = Changeset(doc.get_id(), "user3", [B])
        C.set_id('c')
        doc.receive_changeset(C)
        assert doc.get_ordered_changesets() == [root, A, B, C]

        D = Changeset(doc.get_id(), "user4", [B])
        D.set_id('d')
        doc.receive_changeset(D)
        assert doc.get_ordered_changesets() == [root, A, B, C, D]

        E = Changeset(doc.get_id(), "user5", [C, D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert doc.get_ordered_changesets() == [root, A, B, C, D, E]

        F = Changeset(doc.get_id(), "user6", [C, D])
        F.set_id('f')
        doc.receive_changeset(F)
        assert set(doc.get_dependencies()) == set([E,F])
        assert doc.get_ordered_changesets() == [root, A,B,C,D,E,F]

        G = Changeset(doc.get_id(), "user5", [E,F])
        doc.receive_changeset(G)
        assert doc.get_dependencies() == [G]
        assert doc.get_ordered_changesets() == [root, A, B, C, D, E, F, G]
        # HA FUCKING HA!

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
        assert doc.get_ordered_changesets() == [root, A]
        
        B = Changeset(doc.get_id(),"user1",[A])
        B.set_id('b')
        doc.receive_changeset(B)
        assert doc.get_ordered_changesets() == [root,A,B]
        
        C = Changeset(doc.get_id(),"user3",[B])
        C.set_id('c')
        doc.receive_changeset(C)
        assert doc.get_ordered_changesets() == [root,A,B,C]

        D = Changeset(doc.get_id(),"user4",[B])
        D.set_id('d')
        doc.receive_changeset(D)
        assert doc.get_ordered_changesets() == [root,A,B,C,D]

        E = Changeset(doc.get_id(),"user5",[D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert doc.get_ordered_changesets() == [root,A,B,C,D,E]

        F = Changeset(doc.get_id(),"user6",[D])
        F.set_id('f')
        doc.receive_changeset(F)
        assert doc.get_ordered_changesets() == [root,A,B,C,D,E,F]

        G = Changeset(doc.get_id(),"user5",[C])
        doc.receive_changeset(G)
        G.set_id('g')
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,F]

        H = Changeset(doc.get_id(),"user5",[G,F])
        E.set_id('h')
        doc.receive_changeset(H)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,F,H]

        I = Changeset(doc.get_id(),"user6",[E])
        F.set_id('i')
        doc.receive_changeset(I)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H]

        J = Changeset(doc.get_id(),"user5",[I,F])
        J.set_id('j')
        doc.receive_changeset(J)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,J,H]

        K = Changeset(doc.get_id(),"user5",[H])
        K.set_id('k')
        doc.receive_changeset(K)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,J,H,K]

        L = Changeset(doc.get_id(),"user5",[J])
        L.set_id('l')
        doc.receive_changeset(L)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,J,L,H,K]

        M = Changeset(doc.get_id(),"user5",[K,L])
        M.set_id('m')
        doc.receive_changeset(M)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,J,L,H,K,M]
