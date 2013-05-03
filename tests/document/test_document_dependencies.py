from collaborator.document import Document
from collaborator.op import Op
from collaborator.changeset import Changeset


class TestDocumentInsertChangeset:

    def test_no_dependencies(self):
        doc = Document()
        assert doc.get_open_changeset() == None
        assert doc.changesets == []

        assert doc.get_dependencies() == []

    def test_one_changeset(self):
        doc = Document()
        cs0 = Changeset(doc.get_id(), "dummyuser", [])
        doc.insert_changeset_into_changsets(cs0)
        assert doc.changesets == [cs0]
        assert doc.get_dependencies() == [cs0]


    def test_insert_sequential_changesets(self):
        doc = Document()        
        cs0 = Changeset(doc.get_id(), "user0", [])
        doc.insert_changeset_into_changsets(cs0)
        assert doc.get_dependencies() == [cs0]

        cs1 = Changeset(doc.get_id(), "user1", [cs0])
        doc.insert_changeset_into_changsets(cs1)
        assert doc.changesets == [cs0, cs1]
        assert doc.get_dependencies() == [cs1]

        

    def test_multiple_dependencies(self):
        doc = Document()
        cs0 = Changeset(doc.get_id(), "user0", [])
        doc.insert_changeset_into_changsets(cs0)
        assert doc.get_dependencies() == [cs0]

        cs1 = Changeset(doc.get_id(), "user1", [])
        doc.insert_changeset_into_changsets(cs1)
        assert set(doc.get_dependencies()) == set([cs0,cs1])

        cs2 = Changeset(doc.get_id(), "user2", [])
        doc.insert_changeset_into_changsets(cs2)
        assert set(doc.get_dependencies()) == set([cs0,cs1,cs2])

        cs3 = Changeset(doc.get_id(), "user3", [])
        doc.insert_changeset_into_changsets(cs3)
        assert set(doc.changesets) == set([cs2, cs0, cs3, cs1])

        assert set(doc.get_dependencies()) == set([cs2, cs0, cs3, cs1])

    def test_multiple_dependencies_common_base(self):
        doc = Document()
        cs0 = Changeset(doc.get_id(), "user0", [])
        doc.insert_changeset_into_changsets(cs0)
        cs1 = Changeset(doc.get_id(), "user1", [])
        doc.insert_changeset_into_changsets(cs1)

        cs2 = Changeset(doc.get_id(), "user2", [cs0])
        doc.insert_changeset_into_changsets(cs2)
        assert set(doc.get_dependencies()) == set([cs1,cs2])

    def test_multiple_dependencies_multiple_divergences(self):
        doc = Document()
        cs0 = Changeset(doc.get_id(), "user0", [])
        doc.insert_changeset_into_changsets(cs0)
        cs1 = Changeset(doc.get_id(), "user1", [])
        doc.insert_changeset_into_changsets(cs1)
        cs2 = Changeset(doc.get_id(), "user3", [cs0])
        doc.insert_changeset_into_changsets(cs2)
        cs3 = Changeset(doc.get_id(), "user4", [cs2])
        doc.insert_changeset_into_changsets(cs3)
        cs4 = Changeset(doc.get_id(), "user5", [cs3])
        doc.insert_changeset_into_changsets(cs4)

        assert set(doc.get_dependencies()) == set([cs4, cs1])

        # now tie those changesets together, so back to one dependency
        cs5 = Changeset(doc.get_id(), "user6", [cs4, cs1])
        doc.insert_changeset_into_changsets(cs5)
        assert set(doc.get_dependencies()) == set([cs5])
