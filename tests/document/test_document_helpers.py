
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
from majormajor.op import Op


class TestDocumentHelpers:

    def setup_method(self, method):
        self.doc0 = Document(snapshot={})

        s1 = {'first': 'some string',
              'second': {'third':'more string',
                         'fourth':{'numb':55}},
              'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}
        self.doc1 = Document(snapshot=s1)

        s2 = [{'name':'value'},
              [1,2,3,4],
              'normal, ol string',
              [['multi'],['dimen'],['array']],
              True,
              None,
              42]
        self.doc2 = Document(snapshot=s2)
        self.doc3 = Document(snapshot = "ABCDEFG")
        
    def test_get_id(self):
        doc = Document('abc456')
        assert doc.get_id() == 'abc456'

    def test_get_last_changeset(self):
        assert self.doc0.get_last_changeset() == self.doc0.get_root_changeset()

        # add a changeset and make sure it ends up last
        self.doc0.add_local_op(Op('set',[],val='abc'))
        open_changeset = self.doc0.get_open_changeset()
        self.doc0.close_changeset()
        assert open_changeset == self.doc0.get_last_changeset()

        # do it again
        self.doc0.add_local_op(Op('set',[],val='abc'))
        assert open_changeset == self.doc0.get_last_changeset()
        new_open_changeset = self.doc0.get_open_changeset()
        self.doc0.close_changeset()
        assert new_open_changeset == self.doc0.get_last_changeset()
        
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
        assert doc1.get_node(path1) == doc1.snapshot
        assert doc2.get_node(path1) == doc2.snapshot
        
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

