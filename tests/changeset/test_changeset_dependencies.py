import pytest

from majormajor.document import Document
from majormajor.op import Op
from majormajor.changeset import Changeset


class TestChangesetDependencies:

    def setup_method(self, method):
        self.doc_id = 'doc_id'
        self.user1 = 'user1'
        self.user2 = 'user2'
        self.cs0 = Changeset(self.doc_id, self.user1, [])
        
    def test_get_dependency_chain(self):
        doc = self.doc_id
        user1 = self.user1
        user2 = self.user2
        a = self.cs0
        assert a.get_dependency_chain() == set([])

        b = Changeset(doc, user2, [a])
        assert b.get_dependency_chain() == set([a])
        
        c = Changeset(doc, user2, [b])
        assert c.get_dependency_chain() == set([a,b])
        
        d = Changeset(doc, user2, [c])
        assert d.get_dependency_chain() == set([a,b,c])

        #different cs with same dependencies has same chain
        e = Changeset(doc, user2, [c])
        assert e.get_dependency_chain() == set([a,b,c])
                
        f = Changeset(doc, user2, [e])
        assert f.get_dependency_chain() == set([a,b,c,e])
        
        g = Changeset(doc, user2, [f,d])
        assert g.get_dependency_chain() == set([a,b,c,d,e,f])

