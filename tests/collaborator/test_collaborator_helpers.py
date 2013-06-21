from majormajor.majormajor import MajorMajor
from majormajor.document import Document



class TestMajorMajorHelpers:

    def setup_method(self, method):
        self.collab0 = MajorMajor()
        
    def test_new_document(self):
        # leaving nothing specified
        doc = self.collab0.new_document()
        assert isinstance(doc, Document)
        assert doc.get_snapshot() == {}

