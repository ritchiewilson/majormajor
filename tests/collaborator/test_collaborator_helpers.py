from collaborator.collaborator import Collaborator
from collaborator.document import Document



class TestCollaboratorHelpers:

    def setup_method(self, method):
        self.collab0 = Collaborator()
        
    def test_new_document(self):
        # leaving nothing specified
        doc = self.collab0.new_document()
        assert isinstance(doc, Document)
        assert doc.get_snapshot() == {}

