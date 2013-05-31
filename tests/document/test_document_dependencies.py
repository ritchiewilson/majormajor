from collaborator.document import Document
from collaborator.op import Op
from collaborator.changeset import Changeset
import random
import string

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
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        

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
        assert set(doc.get_dependencies()) == set([B,A])
        assert doc.get_ordered_changesets() == [root, A, B]

        C = Changeset(doc.get_id(), "user2", [root])
        C.set_id('c')
        doc.receive_changeset(C)
        assert set(doc.get_dependencies()) == set([B,A,C])
        assert doc.get_ordered_changesets() == [root, A, B, C]
        assert doc.get_ordered_changesets() == doc.tree_to_list()


        # test_multiple_dependencies_common_base
        D = Changeset(doc.get_id(), "user0", [C,A])
        D.set_id('d')
        doc.receive_changeset(D)
        assert set(doc.get_dependencies()) == set([B,D])
        assert doc.get_ordered_changesets() == [root, A, B, C, D]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        E = Changeset(doc.get_id(), 'user1', [B, D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert doc.get_dependencies() == [E]
        assert doc.get_ordered_changesets() == [root, A, B, C, D, E]
        assert doc.get_ordered_changesets() == doc.tree_to_list()


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
        assert doc.get_ordered_changesets() == doc.tree_to_list()
        
        B = Changeset(doc.get_id(), "user1", [A])
        B.set_id('b')
        doc.receive_changeset(B)
        assert doc.get_ordered_changesets() == [root, A, B]
        assert doc.get_ordered_changesets() == doc.tree_to_list()
        
        C = Changeset(doc.get_id(), "user3", [B])
        C.set_id('c')
        doc.receive_changeset(C)
        assert doc.get_ordered_changesets() == [root, A, B, C]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        D = Changeset(doc.get_id(), "user4", [B])
        D.set_id('d')
        doc.receive_changeset(D)
        assert doc.get_ordered_changesets() == [root, A, B, C, D]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        E = Changeset(doc.get_id(), "user5", [C, D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert doc.get_ordered_changesets() == [root, A, B, C, D, E]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        F = Changeset(doc.get_id(), "user6", [C, D])
        F.set_id('f')
        doc.receive_changeset(F)
        assert set(doc.get_dependencies()) == set([E,F])
        assert doc.get_ordered_changesets() == [root, A,B,C,D,E,F]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        G = Changeset(doc.get_id(), "user5", [E,F])
        doc.receive_changeset(G)
        assert doc.get_dependencies() == [G]
        assert doc.get_ordered_changesets() == [root, A, B, C, D, E, F, G]
        assert doc.get_ordered_changesets() == doc.tree_to_list()
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
        assert doc.get_ordered_changesets() == doc.tree_to_list()
        
        B = Changeset(doc.get_id(),"user1",[A])
        B.set_id('b')
        doc.receive_changeset(B)
        assert doc.get_ordered_changesets() == [root,A,B]
        assert doc.get_ordered_changesets() == doc.tree_to_list()
        
        C = Changeset(doc.get_id(),"user3",[B])
        C.set_id('c')
        doc.receive_changeset(C)
        assert doc.get_ordered_changesets() == [root,A,B,C]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        D = Changeset(doc.get_id(),"user4",[B])
        D.set_id('d')
        doc.receive_changeset(D)
        assert doc.get_ordered_changesets() == [root,A,B,C,D]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        E = Changeset(doc.get_id(),"user5",[D])
        E.set_id('e')
        doc.receive_changeset(E)
        assert doc.get_ordered_changesets() == [root,A,B,C,D,E]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        F = Changeset(doc.get_id(),"user6",[D])
        F.set_id('f')
        doc.receive_changeset(F)
        assert doc.get_ordered_changesets() == [root,A,B,C,D,E,F]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        G = Changeset(doc.get_id(),"user5",[C])
        G.set_id('g')
        doc.receive_changeset(G)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,F]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        H = Changeset(doc.get_id(),"user5",[G,F])
        H.set_id('h')
        doc.receive_changeset(H)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,F,H]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        I = Changeset(doc.get_id(),"user6",[E])
        I.set_id('i')
        doc.receive_changeset(I)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        J = Changeset(doc.get_id(),"user5",[I,F])
        J.set_id('j')
        doc.receive_changeset(J)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,J]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        K = Changeset(doc.get_id(),"user5",[H])
        K.set_id('k')
        doc.receive_changeset(K)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,K,J]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        L = Changeset(doc.get_id(),"user5",[J])
        L.set_id('l')
        doc.receive_changeset(L)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,K,J,L]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

        M = Changeset(doc.get_id(),"user5",[K,L])
        M.set_id('m')
        doc.receive_changeset(M)
        assert doc.get_ordered_changesets() == [root,A,B,C,G,D,E,I,F,H,K,J,L,M]
        assert doc.get_ordered_changesets() == doc.tree_to_list()

    def test_random_changesets(self):
        doc = Document(snapshot='')
        assert doc.get_ordered_changesets() == doc.tree_to_list()
        i = 1
        while i < 1000:
            doc = add_random_changeset(doc)
            i += 1
        assert len(doc.get_ordered_changesets()) == i
        assert doc.get_ordered_changesets() == doc.tree_to_list()
            
def add_random_changeset(doc):
    deps = []
    if random.random() > .5:
        number_of_deps = random.randrange(0,len(doc.get_dependencies()), 1) + 1
        deps = random.sample(doc.get_dependencies(), number_of_deps)
    else:
        deps = [random.choice(doc.get_ordered_changesets())]
    # Need to randomize user names here, otherwise lots of CSs with same hashcode
    user = ''.join(random.choice(string.ascii_letters + string.digits)
                          for x in range(5))
    cs = Changeset(doc.get_id(), user, deps)
    doc.receive_changeset(cs)
    return doc
