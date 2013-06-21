import pytest

from majormajor.document import Document
from majormajor.op import Op
from majormajor.changeset import Changeset


class TestChangesetHelpers:

    def setup_method(self, method):
        self.cs0 = Changeset('doc_id', 'user_id', [])
        
    def test_is_empty(self):
        cs = Changeset('doc_id', 'user_id', [])
        assert cs.is_empty()

        cs.add_op(Op('set',[],val=''))
        assert not cs.is_empty()

    def Xtest_has_full_dependency_info(self):
        # should always pass when it has no dependencies
        cs0 = Changeset('doc_id', 'user_id', [])
        assert cs0.has_full_dependency_info()

        cs1 = Changeset('doc_id', 'user_id', ['randomid'])
        assert not cs1.has_full_dependency_info()

        cs2 = Changeset('doc_id', 'user_id', [cs1])
        assert cs2.has_full_dependency_info()

        cs3 = Changeset('doc_id', 'user_id', [cs2, 'otherrandomid'])
        assert not cs3.has_full_dependency_info()

        cs4 = Changeset('doc_id', 'user_id', [cs1])
        cs5 = Changeset('doc_id', 'user_id', [cs4, cs3])
        assert cs5.has_full_dependency_info()

        cs6 = Changeset('doc_id', 'user_id', [cs5, 'otherid'])
        assert not cs6.has_full_dependency_info()

    def Xtest_get_dependency_ids(self):
        cs0 = Changeset('doc_id', 'user_id', [])
        assert cs0.get_dependency_ids() == []
        
        cs1 = Changeset('doc_id', 'user_id', ['randomid'])
        assert cs1.get_dependency_ids() == ['randomid']
        
        cs2 = Changeset('doc_id', 'user_id', [cs1])
        assert cs2.get_dependency_ids() == [cs1.get_id()]
        
        cs3 = Changeset('doc_id', 'user_id', [cs2, 'otherrandomid'])
        assert cs3.get_dependency_ids() == [cs2.get_id(), 'otherrandomid']

    def test_set_id(self):
        cs0 = Changeset('doc_id', 'user_id', [])
        assert cs0.set_id('randomid')
        assert cs0.get_id() == 'randomid'

    def test_add_op(self):
        op = Op('set', [],val='')
        assert self.cs0.add_op(op)
        assert self.cs0.get_ops() == [op]

        # cannot add same op twice
        with pytest.raises(Exception):
            self.cs0.add_op(op)
            
        # add a differant op and it goes through
        op2 = Op('set', [],val='')
        assert self.cs0.add_op(op2)
        assert self.cs0.get_ops() == [op, op2]

        # once id is set, cannot add more ops
        self.cs0.get_id()
        op3 = Op('set', [],val='')
        with pytest.raises(Exception):
            self.cs0.add_op(op3)

    def xtest_relink_dependency(self):
        dep = Changeset('doc_id', 'user_id', [])
        dep.set_id('defined_id')

        # a cs with no dependencies should never relink
        assert not self.cs0.relink_changesets(dep)

        # cs does not need given dep
        cs1 = Changeset('doc_id', 'user_id', [self.cs0])
        assert not cs1.relink_changesets(dep)
        assert cs1.get_dependencies() == [self.cs0]

        # cs already has given dep info
        cs2 = Changeset('doc_id', 'user_id', [self.cs0, dep])
        assert not cs2.relink_changesets(dep)
        assert cs2.get_dependencies() == [self.cs0, dep]

        # cs needed and relinked given dep
        cs3 = Changeset('doc_id', 'user_id', [self.cs0, 'defined_id'])
        assert cs3.relink_changesets(dep)
        assert cs3.get_dependencies() == [self.cs0, dep]

    def test_has_ancestor(self):

        """
        Some complex tree.
        
               C -- G -- H -------- K
              /         /            \
        A -- B -- D -- F -- J -- L -- M--
                   \       /
                    E --- I

        """

        doc_id = 'dummy'
        root = Changeset(doc_id, "user0", [])
        assert not root.has_ancestor(self.cs0)

        A = Changeset(doc_id, "user0", [root])
        assert A.has_ancestor(root)
        assert not A.has_ancestor(self.cs0)
        
        B = Changeset(doc_id,"user1",[A])
        assert B.has_ancestor(A)
        assert B.has_ancestor(root)
        
        C = Changeset(doc_id,"user3",[B])
        assert C.has_ancestor(root)
        assert C.has_ancestor(A)
        assert C.has_ancestor(B)

        D = Changeset(doc_id,"user4",[B])
        assert D.has_ancestor(root)
        assert D.has_ancestor(A)
        assert D.has_ancestor(B)
        assert not D.has_ancestor(C)

        E = Changeset(doc_id,"user5",[D])
        assert E.has_ancestor(root)
        assert E.has_ancestor(A)
        assert E.has_ancestor(B)
        assert E.has_ancestor(D)
        assert not E.has_ancestor(C)

        F = Changeset(doc_id,"user6",[D])
        assert F.has_ancestor(root)
        assert F.has_ancestor(A)
        assert F.has_ancestor(B)
        assert F.has_ancestor(D)
        assert not F.has_ancestor(C)
        assert not F.has_ancestor(E)

        G = Changeset(doc_id,"user5",[C])
        assert G.has_ancestor(root)
        assert G.has_ancestor(A)
        assert G.has_ancestor(B)
        assert G.has_ancestor(C)
        assert not G.has_ancestor(D)
        assert not G.has_ancestor(E)
        assert not G.has_ancestor(F)

        H = Changeset(doc_id,"user5",[G,F])
        assert H.has_ancestor(root)
        assert H.has_ancestor(A)
        assert H.has_ancestor(B)
        assert H.has_ancestor(C)
        assert H.has_ancestor(G)
        assert H.has_ancestor(D)
        assert not H.has_ancestor(E)
        assert H.has_ancestor(F)

        I = Changeset(doc_id,"user6",[E])
        assert I.has_ancestor(root)
        assert I.has_ancestor(A)
        assert I.has_ancestor(B)
        assert not I.has_ancestor(C)
        assert I.has_ancestor(D)
        assert I.has_ancestor(E)
        assert not I.has_ancestor(F)
        assert not I.has_ancestor(G)
        assert not I.has_ancestor(H)

        J = Changeset(doc_id,"user5",[I,F])
        assert J.has_ancestor(root)
        assert J.has_ancestor(A)
        assert J.has_ancestor(B)
        assert not J.has_ancestor(C)
        assert J.has_ancestor(D)
        assert J.has_ancestor(E)
        assert J.has_ancestor(F)
        assert not J.has_ancestor(G)
        assert not J.has_ancestor(H)
        assert J.has_ancestor(I)

        K = Changeset(doc_id,"user5",[H])
        assert K.has_ancestor(root)
        assert K.has_ancestor(A)
        assert K.has_ancestor(B)
        assert K.has_ancestor(C)
        assert K.has_ancestor(D)
        assert not K.has_ancestor(E)
        assert K.has_ancestor(F)
        assert K.has_ancestor(G)
        assert K.has_ancestor(H)
        assert not K.has_ancestor(I)
        assert not K.has_ancestor(J)

        L = Changeset(doc_id,"user5",[J])
        assert L.has_ancestor(root)
        assert L.has_ancestor(A)
        assert L.has_ancestor(B)
        assert not L.has_ancestor(C)
        assert L.has_ancestor(D)
        assert L.has_ancestor(E)
        assert L.has_ancestor(F)
        assert not L.has_ancestor(G)
        assert not L.has_ancestor(H)
        assert L.has_ancestor(I)
        assert L.has_ancestor(J)
        assert not L.has_ancestor(K)

        M = Changeset(doc_id,"user5",[K,L])
        assert M.has_ancestor(root)
        assert M.has_ancestor(A)
        assert M.has_ancestor(B)
        assert M.has_ancestor(C)
        assert M.has_ancestor(D)
        assert M.has_ancestor(E)
        assert M.has_ancestor(F)
        assert M.has_ancestor(G)
        assert M.has_ancestor(H)
        assert M.has_ancestor(I)
        assert M.has_ancestor(J)
        assert M.has_ancestor(K)
        assert M.has_ancestor(L)
