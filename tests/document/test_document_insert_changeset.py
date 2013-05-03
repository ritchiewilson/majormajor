from collaborator.document import Document
from collaborator.op import Op
from collaborator.changeset import Changeset


class TestDocumentInsertChangeset:

    def test_insert_into_empty(self):
        doc = Document()
        assert doc.get_open_changeset() == None
        assert doc.changesets == []

        cs = Changeset(doc.get_id(), "dummyuser", [])
        assert doc.insert_changeset_into_changsets(cs) == 0
        assert doc.get_last_changeset() == cs
        assert len(doc.changesets) == 1

    def test_insert_sequential_changesets(self):
        doc = Document()
        cs0 = Changeset(doc.get_id(), "user1", [])
        assert doc.insert_changeset_into_changsets(cs0) == 0
        
        cs1 = Changeset(doc.get_id(), "user1", [cs0])
        assert doc.insert_changeset_into_changsets(cs1) == 1

        cs2 = Changeset(doc.get_id(), "user1", [cs1])
        assert doc.insert_changeset_into_changsets(cs2) == 2

        assert doc.changesets == [cs0, cs1, cs2]


    def test_insert_with_same_dependency(self):
        doc = Document()        
        cs0 = Changeset(doc.get_id(), "user0", [])
        cs0.set_id('b')
        assert doc.insert_changeset_into_changsets(cs0) == 0

        cs1 = Changeset(doc.get_id(), "user1", [])
        cs1.set_id('d')
        assert doc.insert_changeset_into_changsets(cs1) == 1

        cs2 = Changeset(doc.get_id(), "user2", [])
        cs2.set_id('a')
        assert doc.insert_changeset_into_changsets(cs2) == 0

        cs3 = Changeset(doc.get_id(), "user3", [])
        cs3.set_id('c')
        assert doc.insert_changeset_into_changsets(cs3) == 2

        assert doc.changesets == [cs2, cs0, cs3, cs1]

        #
