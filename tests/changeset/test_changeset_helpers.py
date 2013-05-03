from collaborator.document import Document
from collaborator.op import Op
from collaborator.changeset import Changeset


class TestChangesetHelpers:

    def setup_method(self, method):
        pass
        
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

    def test_get_dependency_chain(self):
        cs0 = Changeset('doc_id', 'user_id', [])
        assert cs0.get_dependency_chain() == []

        cs1 = Changeset('doc_id', 'user_id', [cs0])
        assert cs1.get_dependency_chain() == [cs0]

        # there is no garuntee for order, so just check that the sets
        # are equal moving forward
        cs2 = Changeset('doc_id', 'user_id', [cs1])
        assert set(cs2.get_dependency_chain()) == set([cs1, cs0])

        cs3 = Changeset('doc_id', 'user_id', [cs2])
        assert set(cs3.get_dependency_chain()) == set([cs2, cs1, cs0])
        assert len(cs3.get_dependency_chain()) == 3

        cs4 = Changeset('doc_id', 'user_id', [cs1])
        cs5 = Changeset('doc_id', 'user_id', [cs4, cs3])
        assert set(cs5.get_dependency_chain()) == set([cs4, cs3, cs2, cs1, cs0])

        cs6 = Changeset('doc_id', 'user_id', [cs3])
        assert set(cs6.get_dependency_chain()) == set([cs3, cs2, cs1, cs0])
        assert len(cs6.get_dependency_chain()) == 4

        cs7 = Changeset('doc_id', 'user_id', [cs6, cs5])
        assert set(cs7.get_dependency_chain()) == set([cs6, cs5, cs4, cs3, cs2, cs1, cs0])
        assert len(cs7.get_dependency_chain()) == 7

    def test_set_id(self):
        cs0 = Changeset('doc_id', 'user_id', [])
        cs0.set_id('randomid')
        assert cs0.get_id() == 'randomid'
