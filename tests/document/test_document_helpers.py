
# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestDocumentHelpers:

    def setup_method(self, method):
        self.doc0 = Document(snapshot={})
        self.doc0.HAS_EVENT_LOOP = False

        s1 = {'first': 'some string',
              'second': {'third':'more string',
                         'fourth':{'numb':55}},
              'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}
        self.doc1 = Document(snapshot=s1)
        self.doc1.HAS_EVENT_LOOP = False
        
        s2 = [{'name':'value'},
              [1,2,3,4],
              'normal, ol string',
              [['multi'],['dimen'],['array']],
              True,
              None,
              42]
        self.doc2 = Document(snapshot=s2)
        self.doc2.HAS_EVENT_LOOP = False
        self.doc3 = Document(snapshot = "ABCDEFG")
        self.doc3.HAS_EVENT_LOOP = False
        
    def test_get_id(self):
        doc = Document('abc456')
        assert doc.get_id() == 'abc456'
        
    # Testing that Document can tell if a path is valid in its
    # snapshot without throwing any exceptions
    def test_contains_path(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2
        doc3 = self.doc3

        # all documents have a root (empty path)
        path1 = []
        assert doc0.contains_path(path1)
        assert doc1.contains_path(path1)
        assert doc2.contains_path(path1)

        path2 = ['first']
        assert doc0.contains_path(path2) == False
        assert doc1.contains_path(path2)

        path3 = ['second','fourth','numb']
        assert doc1.contains_path(path3)
        
        path4 = ['fifth',2,'sixth']
        assert doc1.contains_path(path4)

        # final key is not valid
        path5 = ['fifth',2,'deep string']
        assert doc1.contains_path(path5) == False

        # middle key is not valid
        path6 = ['second','first','numb']
        assert doc1.contains_path(path6) == False

        # 4 is one out of path
        path7 = ['second','fifth',4]
        assert doc1.contains_path(path7) == False
        
        # path can only be number when looking at list
        path8 = [0]
        assert doc0.contains_path(path8) == False
        assert doc1.contains_path(path8) == False
        assert doc2.contains_path(path8) == True

        path9 = [3,2]
        assert doc2.contains_path(path9)

        # This snapshot is just a string. Should have no path but
        # root.
        path10 = [3]
        assert doc3.contains_path(path10) == False

    # Testing the a document can get the value at the given
    # path. First some tests on deep nesting, then testing weirder
    # values like True or None (null in json)
    def test_get_value(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2

        path1 = []
        assert doc0.get_node(path1) == {}
        assert doc1.get_node(path1) == doc1.get_snapshot()
        assert doc2.get_node(path1) == doc2.get_snapshot()
        
        path2 = ['first']
        assert doc1.get_value(path2) == 'some string'

        path3 = ['second']
        assert doc1.get_value(path3) == \
                         {'third':'more string',
                          'fourth':{'numb':55}}

        path4 = ['second','fourth','numb']
        assert doc1.get_value(path4) == 55

        path5 = ['fifth',2,'sixth']
        assert doc1.get_value(path5) == 'deep string'

        path6 = [0, 'name']
        assert doc2.get_value(path6) == 'value'

        path7 = [3,1,0]
        assert doc2.get_value(path7) == 'dimen'

        path8 = [1,3]
        assert doc2.get_value(path8) == 4

        path9 = [4]
        assert doc2.get_value(path9) == True

        path10 = [5]
        assert doc2.get_value(path10) == None

    def test_has_needed_dependencies(self):
        doc = self.doc0

        cs1 = Changeset(doc.get_id(), 'user', [doc.get_root_changeset()])
        assert doc.has_needed_dependencies(cs1)

        cs2 = Changeset(doc.get_id(), 'user', [cs1])
        assert not doc.has_needed_dependencies(cs2)

        doc.receive_changeset(cs1)
        assert doc.has_needed_dependencies(cs2)

        cs3 = Changeset(doc.get_id(), 'user', [cs1, cs2])
        assert not doc.has_needed_dependencies(cs3)

        doc.receive_changeset(cs2)
        assert doc.has_needed_dependencies(cs3)

        cs4 = Changeset(doc.get_id(), 'user', [cs3, "555"])
        assert not doc.has_needed_dependencies(cs4)

        doc.receive_changeset(cs3)
        assert not doc.has_needed_dependencies(cs4)

        cs5 = Changeset(doc.get_id(), 'user', [cs1])
        cs5.set_id("555")
        doc.receive_changeset(cs5)
        cs4.relink_changesets(doc.all_known_changesets)
        assert cs5 in cs4.get_parents()
        assert cs4.has_full_dependency_info()
        assert doc.has_needed_dependencies(cs4)
