
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

from document import Document
from op import Op
import unittest


class TestSimpleNodeOperations(unittest.TestCase):

    def setUp(self):
        self.doc0 = Document()
        self.doc1 = Document()
        self.doc1.snapshot = {'first': 'some string',
                            'second': {'third':'more string',
                                       'fourth':{'numb':55}},
                            'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}
        self.doc2 = Document()
        self.doc2.snapshot = [{'name':'value'},
                              [1,2,3,4],
                              'normal, ol string',
                              [['multi'],['dimen'],['array']],
                              True,
                              None,
                              42]
        self.doc3 = Document()
        self.doc3.snapshot = 'ABCDEFG'
        
    # Testing that Document can tell if a path is valid in its
    # snapshot without throwing any exceptions
    def test_contains_path(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2
        doc3 = self.doc3

        # all documents have a root (empty path)
        path1 = []
        self.assertTrue(doc0.contains_path(path1))
        self.assertTrue(doc1.contains_path(path1))
        self.assertTrue(doc2.contains_path(path1))

        path2 = ['first']
        self.assertEqual(doc0.contains_path(path2), False)
        self.assertTrue(doc1.contains_path(path2))

        path3 = ['second','fourth','numb']
        self.assertTrue(doc1.contains_path(path3))
        
        path4 = ['fifth',2,'sixth']
        self.assertTrue(doc1.contains_path(path4))

        # final key is not valid
        path5 = ['fifth',2,'deep string']
        self.assertEqual(doc1.contains_path(path5), False)

        # middle key is not valid
        path6 = ['second','first','numb']
        self.assertEqual(doc1.contains_path(path6), False)

        # 4 is one out of path
        path7 = ['second','fifth',4]
        self.assertEqual(doc1.contains_path(path7), False)
        
        # path can only be number when looking at list
        path8 = [0]
        self.assertEqual(doc0.contains_path(path8), False)
        self.assertEqual(doc1.contains_path(path8), False)
        self.assertEqual(doc2.contains_path(path8), True)

        path9 = [3,2]
        self.assertTrue(doc2.contains_path(path9))

        # This snapshot is just a string. Should have no path but
        # root.
        path10 = [3]
        self.assertEqual(doc3.contains_path(path10), False)

    # Testing the a document can get the value at the given
    # path. First some tests on deep nesting, then testing weirder
    # values like True or None (null in json)
    def test_get_value(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2

        path1 = []
        self.assertEqual(doc0.get_node(path1), {})
        self.assertEqual(doc1.get_node(path1), doc1.snapshot)
        self.assertEqual(doc2.get_node(path1), doc2.snapshot)
        
        path2 = ['first']
        self.assertEqual(doc1.get_value(path2),'some string')

        path3 = ['second']
        self.assertEqual(doc1.get_value(path3),
                         {'third':'more string',
                          'fourth':{'numb':55}})

        path4 = ['second','fourth','numb']
        self.assertEqual(doc1.get_value(path4), 55)

        path5 = ['fifth',2,'sixth']
        self.assertEqual(doc1.get_value(path5), 'deep string')

        path6 = [0, 'name']
        self.assertEqual(doc2.get_value(path6), 'value')

        path7 = [3,1,0]
        self.assertEqual(doc2.get_value(path7), 'dimen')

        path8 = [1,3]
        self.assertEqual(doc2.get_value(path8), 4)

        path9 = [4]
        self.assertEqual(doc2.get_value(path9), True)

        path10 = [5]
        self.assertEqual(doc2.get_value(path10), None)

    def test_set_value(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2

        # change value type of whole document
        doc0.apply_op(Op('set', [], val='ABCDEFG'))
        self.assertEqual(doc0.snapshot, 'ABCDEFG')
        doc0.apply_op(Op('set', [], val=None))
        self.assertEqual(doc0.snapshot, None)        
        doc0.apply_op(Op('set', [], val=False))
        self.assertEqual(doc0.snapshot, False)

        # simple, first level dict key/val change
        op1 = Op('set', ['first'], val='newval')
        doc1.apply_op(op1)
        self.assertEqual(doc1.get_value(['first']), 'newval')

        # nested dicts
        op2 = Op('set', ['second','third'], val=99)
        doc1.apply_op(op2)
        self.assertEqual(doc1.get_value(['second','third']), 99)
        # nested dicts with list index as key
        op3 = Op('set', ['fifth', 1], val=42)
        doc1.apply_op(op3)
        self.assertEqual(doc1.get_value(['fifth',1]), 42)

        #nested dict with list index in path
        op4 = Op('set', ['fifth',2,'sixth'], val={'a':1})
        doc1.apply_op(op4)
        self.assertEqual(doc1.get_value(['fifth',2,'sixth']), {'a':1})

        # traversing lists
        op5 = Op('set', [3,2,0], val=5)
        doc2.apply_op(op5)
        self.assertEqual(doc2.get_value([3,2,0]), 5)

    def test_boolean_negation(self):
        doc0 =  Document()
        doc0.snapshot = False
        doc1 = self.doc1
        doc2 = self.doc2

        # whole document is a boolean. Just change that
        op1 = Op('bn', [])
        doc0.apply_op(op1)
        self.assertEqual(doc0.snapshot, True)
        doc0.apply_op(op1)
        self.assertEqual(doc0.snapshot, False)

        # boolean at some key/index
        op2 = Op('bn', [4])
        doc2.apply_op(op2)
        self.assertEqual(doc2.get_value([4]), False)
        doc2.apply_op(op2)
        self.assertEqual(doc2.get_value([4]), True)

        # boolean along some path
        path3 = ['fifth',2,'sixth']
        doc1.apply_op(Op('set', path3, val=True))
        op3 = Op('bn', path3)
        doc1.apply_op(op3)
        self.assertEqual(doc1.get_value(path3), False)
        doc1.apply_op(op3)
        self.assertEqual(doc1.get_value(path3), True)

    def test_number_add(self):
        doc0 =  Document()
        doc0.snapshot = 0
        doc1 = self.doc1
        doc2 = self.doc2

        # whole document is just a number. Alter it.
        op1 = Op('na', [], val=5)
        doc0.apply_op(op1)
        self.assertEqual(doc0.snapshot, 5)

        # number deeper in doc
        op2 = Op('na', ['fifth',1], val=-100)
        doc1.apply_op(op2)
        self.assertEqual(doc1.get_value(['fifth',1]), -34)

        # funkier numbers accepted by JSON
        # int frac
        op3 = Op('na', ['fifth',1], val=34.5)
        doc1.apply_op(op3)
        self.assertEqual(doc1.get_value(['fifth',1]), 0.5)

    def test_string_insert(self):
        doc1 = self.doc1
        doc2 = self.doc2
        doc3 = self.doc3
        
        # whole object is just a string. alter it
        # add string to end
        op1 = Op('si', [], val='end', offset=7)
        doc3.apply_op(op1)
        self.assertEqual(doc3.snapshot, 'ABCDEFGend')
        # insert in middle
        op2 = Op('si', [], val=' word ', offset=3)
        doc3.apply_op(op2)
        self.assertEqual(doc3.snapshot, 'ABC word DEFGend')
        # insert at start
        op3 = Op('si', [], val='start', offset=0)
        doc3.apply_op(op3)
        self.assertEqual(doc3.snapshot, 'startABC word DEFGend')

        # something in nested dict
        op4 = Op('si', [3,1,0], offset=5, val='sional')
        doc2.apply_op(op4)
        self.assertEqual(doc2.get_value([3,1,0]), 'dimensional')

    def test_string_delete(self):
        doc1 = self.doc1
        doc2 = self.doc2
        doc3 = self.doc3

        # whole doc is just a string. alter it
        # delete last character
        op1 = Op('sd', [], val=1, offset=6)
        doc3.apply_op(op1)
        self.assertEqual(doc3.snapshot, 'ABCDEF')
        # delete in middle
        op2 = Op('sd', [], val=2, offset=3)
        doc3.apply_op(op2)
        self.assertEqual(doc3.snapshot, 'ABCF')
        # delete first two letters
        op3 = Op('sd', [], val=2, offset=0)
        doc3.apply_op(op3)
        self.assertEqual(doc3.snapshot, 'CF')

        # something deep in doc
        op4 = Op('sd', [3,1,0], val=2, offset=3)
        doc2.apply_op(op4)
        self.assertEqual(doc2.get_value([3,1,0]), 'dim')

    def test_array_insert(self):
        doc0 =  Document()
        doc0.snapshot = []
        doc1 = self.doc1
        doc2 = self.doc2

        # whole doc is just an empty array. alter it
        op1 = Op('ai', [], val='c', offset=0)
        doc0.apply_op(op1)
        self.assertEqual(doc0.snapshot, ['c'])
        # insert at start
        op2 = Op('ai', [], val='a', offset=0)
        doc0.apply_op(op2)
        self.assertEqual(doc0.snapshot, ['a', 'c'])
        # insert at end
        op3 = Op('ai', [], val='d', offset=2)
        doc0.apply_op(op3)
        self.assertEqual(doc0.snapshot, ['a','c','d'])
        # insert in middle
        op4 = Op('ai', [], val='b', offset=1)
        doc0.apply_op(op4)
        self.assertEqual(doc0.snapshot, ['a','b','c','d'])

        # insert into some array deep in doc
        op5 = Op('ai', [3,1], val='a', offset=1)
        doc2.apply_op(op5)
        self.assertEqual(doc2.get_value([3,1]), ['dimen', 'a'])

        # again
        op6 = Op('ai', ['fifth'], val='a', offset=1)
        doc1.apply_op(op6)
        result6 = [55,'a',66,{'sixth': 'deep string'}, 'rw']
        self.assertEqual(doc1.get_value(['fifth']), result6)

    def test_array_delete(self):
        doc0 =  Document()
        doc0.snapshot = []
        doc1 = self.doc1
        doc2 = self.doc2

        # can technically delete nothing from empty list. why not
        op1 = Op('ad', [], offset=0, val=0)
        doc0.apply_op(op1)
        self.assertEqual(doc0.snapshot, [])

        # remove one from list
        op2 = Op('ad', [], offset=1, val=1)
        doc2.apply_op(op2)
        self.assertEqual(doc2.get_value([1]), 'normal, ol string')

        # from nested lists
        op3 = Op('ad', [2], offset=1, val=1)
        doc2.apply_op(op3)
        self.assertEqual(doc2.get_value([2]), [['multi'],['array']])

        # delete multiple elements
        op4 = Op('ad', [], offset=0, val=4)
        doc2.apply_op(op4)
        self.assertEqual(doc2.snapshot, [None, 42])

        # delete last in list:
        op5 = Op('ad', [], offset=1, val=1)
        doc2.apply_op(op5)
        self.assertEqual(doc2.snapshot, [None])

        # in dicts
        op6 = Op('ad', ['fifth'], offset=2, val=2)
        doc1.apply_op(op6)
        self.assertEqual(doc1.get_value(['fifth']), [55,66])

    def test_array_move(self):
        doc1 = self.doc1
        doc2 = self.doc2

        # simple move at root list
        op1 = Op('am', [], offset=2, val=1)
        doc2.apply_op(op1)
        result1 = [{'name':'value'},'normal, ol string', [1,2,3,4],
                   [['multi'],['dimen'],['array']], True, None,42]
        self.assertEqual(doc2.snapshot, result1)

        # Move to end of list
        op2 = Op('am', ['fifth'], offset=0, val=3)
        doc1.apply_op(op2)
        result2 = [66,{'sixth': 'deep string'}, 'rw', 55]
        self.assertEqual(doc1.get_value(['fifth']), result2)

    def test_object_insert(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2

        # whole doc is a dict. insert a key val pair
        kv1 = {'key':'a', 'val':1}
        op1 = Op('oi', [], val=kv1)
        doc0.apply_op(op1)
        self.assertEqual(doc0.snapshot, {'a':1})
        kv2 = {'key':'b', 'val':2}
        op2 = Op('oi', [], val=kv2)
        doc0.apply_op(op2)
        self.assertEqual(doc0.snapshot, {'a':1, 'b':2})

        # nested dicts
        op3 = Op('oi', ['fifth',2], val=kv1)
        doc1.apply_op(op3)
        result3 = {'sixth': 'deep string', 'a': 1}
        self.assertEqual(doc1.get_value(['fifth',2]), result3)

    def test_object_delete(self):
        doc1 = self.doc1
        doc2 = self.doc2

        #simple delete
        op1 = Op('od', [], offset='second')
        doc1.apply_op(op1)
        result1 = {'first': 'some string',
                   'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}
        self.assertEqual(doc1.snapshot, result1)

        # nested
        op2 = Op('od', ['fifth',2], offset='sixth')
        doc1.apply_op(op2)
        result2 = {'first': 'some string',
                   'fifth': [55,66,{}, 'rw']}
        self.assertEqual(doc1.snapshot, result2)
        

if __name__ == '__main__':
    unittest.main()
