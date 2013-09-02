# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

