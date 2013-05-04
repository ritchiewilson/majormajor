import pytest

from collaborator.document import Document
from collaborator.op import Op
from collaborator.changeset import Changeset


class TestChangesetHelpers:

    def setup_method(self, method):
        self.cs0 = Changeset('doc_id', 'user_id', [])
        
    def test_is_empty(self):
        cs = Changeset('doc_id', 'user_id', [])
        assert cs.is_empty()

        cs.add_op(Op('set',[],val=''))
        assert not cs.is_empty()

    def test_has_full_dependency_info(self):
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

    def test_get_dependency_ids(self):
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

    def test_relink_changeset(self):
        dep = Changeset('doc_id', 'user_id', [])
        dep.set_id('defined_id')

        # a cs with no dependencies should never relink
        assert not self.cs0.relink_changeset(dep)

        # cs does not need given dep
        cs1 = Changeset('doc_id', 'user_id', [self.cs0])
        assert not cs1.relink_changeset(dep)
        assert cs1.get_dependencies() == [self.cs0]

        # cs already has given dep info
        cs2 = Changeset('doc_id', 'user_id', [self.cs0, dep])
        assert not cs2.relink_changeset(dep)
        assert cs2.get_dependencies() == [self.cs0, dep]

        # cs needed and relinked given dep
        cs3 = Changeset('doc_id', 'user_id', [self.cs0, 'defined_id'])
        assert cs3.relink_changeset(dep)
        assert cs3.get_dependencies() == [self.cs0, dep]

