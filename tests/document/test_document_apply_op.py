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

from majormajor.document import _Document
from majormajor.ops.op import Op


class TestDocumentApplyOp:
    def setup_method(self, method):
        self.doc0 = _Document()
        self.doc1 = _Document()
        doc1_snap = {'first': 'some string',
                     'second': {'third': 'more string',
                                'fourth': {'numb': 55}},
                     'fifth': [55, 66, {'sixth': 'deep string'}, 'rw']}
        self.doc1.snapshot.set_snapshot(doc1_snap)
        
        self.doc2 = _Document()
        doc2_snap = [{'name': 'value'},
                     [1, 2, 3, 4],
                     'normal, ol string',
                     [['multi'], ['dimen'], ['array']],
                     True,
                     None,
                     42]
        self.doc2.snapshot.set_snapshot(doc2_snap)

        self.doc3 = _Document()
        self.doc3.snapshot.set_snapshot('ABCDEFG')

    def test_set_value(self):
        doc0 = self.doc0
        doc1 = self.doc1
        doc2 = self.doc2

        # change value type of whole document
        doc0.apply_op(Op('set', [], val='ABCDEFG'))
        assert doc0.get_snapshot() == 'ABCDEFG'
        doc0.apply_op(Op('set', [], val=None))
        assert doc0.get_snapshot() is None
        doc0.apply_op(Op('set', [], val=False))
        assert doc0.get_snapshot() is False

        # simple, first level dict key/val change
        op1 = Op('set', ['first'], val='newval')
        doc1.apply_op(op1)
        assert doc1.get_value(['first']) == 'newval'

        # nested dicts
        op2 = Op('set', ['second','third'], val=99)
        doc1.apply_op(op2)
        assert doc1.get_value(['second','third']) == 99
        # nested dicts with list index as key
        op3 = Op('set', ['fifth', 1], val=42)
        doc1.apply_op(op3)
        assert doc1.get_value(['fifth',1]) == 42

        #nested dict with list index in path
        op4 = Op('set', ['fifth',2,'sixth'], val={'a':1})
        doc1.apply_op(op4)
        assert doc1.get_value(['fifth',2,'sixth']) == {'a':1}

        # traversing lists
        op5 = Op('set', [3,2,0], val=5)
        doc2.apply_op(op5)
        assert doc2.get_value([3,2,0]) == 5

    def test_boolean_negation(self):
        doc0 = _Document()
        doc0.snapshot.set_snapshot(False)
        doc1 = self.doc1
        doc2 = self.doc2

        # whole document is a boolean. Just change that
        op1 = Op('bn', [])
        doc0.apply_op(op1)
        assert doc0.get_snapshot() is True
        doc0.apply_op(op1)
        assert doc0.get_snapshot() is False

        # boolean at some key/index
        op2 = Op('bn', [4])
        doc2.apply_op(op2)
        assert doc2.get_value([4]) == False
        doc2.apply_op(op2)
        assert doc2.get_value([4]) == True

        # boolean along some path
        path3 = ['fifth',2,'sixth']
        doc1.apply_op(Op('set', path3, val=True))
        op3 = Op('bn', path3)
        doc1.apply_op(op3)
        assert doc1.get_value(path3) == False
        doc1.apply_op(op3)
        assert doc1.get_value(path3) == True

    def test_number_add(self):
        doc0 =  _Document()
        doc0.snapshot.set_snapshot(0)
        doc1 = self.doc1
        doc2 = self.doc2

        # whole document is just a number. Alter it.
        op1 = Op('na', [], val=5)
        doc0.apply_op(op1)
        assert doc0.get_snapshot() == 5

        # number deeper in doc
        op2 = Op('na', ['fifth',1], val=-100)
        doc1.apply_op(op2)
        assert doc1.get_value(['fifth',1]) == -34

        # funkier numbers accepted by JSON
        # int frac
        op3 = Op('na', ['fifth',1], val=34.5)
        doc1.apply_op(op3)
        assert doc1.get_value(['fifth',1]) == 0.5

    def test_string_insert(self):
        doc1 = self.doc1
        doc2 = self.doc2
        doc3 = self.doc3
        
        # whole object is just a string. alter it
        # add string to end
        op1 = Op('si', [], val='end', offset=7)
        doc3.apply_op(op1)
        assert doc3.get_snapshot() == 'ABCDEFGend'
        # insert in middle
        op2 = Op('si', [], val=' word ', offset=3)
        doc3.apply_op(op2)
        assert doc3.get_snapshot() == 'ABC word DEFGend'
        # insert at start
        op3 = Op('si', [], val='start', offset=0)
        doc3.apply_op(op3)
        assert doc3.get_snapshot() == 'startABC word DEFGend'

        # something in nested dict
        op4 = Op('si', [3,1,0], offset=5, val='sional')
        doc2.apply_op(op4)
        assert doc2.get_value([3,1,0]) == 'dimensional'

    def test_string_delete(self):
        doc1 = self.doc1
        doc2 = self.doc2
        doc3 = self.doc3

        # whole doc is just a string. alter it
        # delete last character
        op1 = Op('sd', [], val=1, offset=6)
        doc3.apply_op(op1)
        assert doc3.get_snapshot() == 'ABCDEF'
        # delete in middle
        op2 = Op('sd', [], val=2, offset=3)
        doc3.apply_op(op2)
        assert doc3.get_snapshot() == 'ABCF'
        # delete first two letters
        op3 = Op('sd', [], val=2, offset=0)
        doc3.apply_op(op3)
        assert doc3.get_snapshot() == 'CF'

        # something deep in doc
        op4 = Op('sd', [3,1,0], val=2, offset=3)
        doc2.apply_op(op4)
        assert doc2.get_value([3,1,0]) == 'dim'

    def test_array_insert(self):
        doc0 = _Document()
        doc0.snapshot.set_snapshot([])
        doc1 = self.doc1
        doc2 = self.doc2

        # whole doc is just an empty array. alter it
        op1 = Op('ai', [], val=['c'], offset=0)
        doc0.apply_op(op1)
        assert doc0.get_snapshot() == ['c']
        # insert at start
        op2 = Op('ai', [], val=['a'], offset=0)
        doc0.apply_op(op2)
        assert doc0.get_snapshot() == ['a', 'c']
        # insert at end
        op3 = Op('ai', [], val=['d'], offset=2)
        doc0.apply_op(op3)
        assert doc0.get_snapshot() == ['a', 'c', 'd']
        # insert several in the middle
        op4 = Op('ai', [], val=['b0', 'b1', 'b2'], offset=1)
        doc0.apply_op(op4)
        assert doc0.get_snapshot() == ['a', 'b0', 'b1', 'b2', 'c', 'd']

        # insert into some array deep in doc
        op5 = Op('ai', [3, 1], val=['a'], offset=1)
        doc2.apply_op(op5)
        assert doc2.get_value([3, 1]) == ['dimen', 'a']

        # again
        op6 = Op('ai', ['fifth'], val=['a'], offset=1)
        doc1.apply_op(op6)
        result6 = [55, 'a', 66, {'sixth': 'deep string'}, 'rw']
        assert doc1.get_value(['fifth']) == result6

    def test_array_delete(self):
        doc0 =  _Document()
        doc0.snapshot.set_snapshot([])
        doc1 = self.doc1
        doc2 = self.doc2

        # can technically delete nothing from empty list. why not
        op1 = Op('ad', [], offset=0, val=0)
        doc0.apply_op(op1)
        assert doc0.get_snapshot() == []

        # remove one from list
        op2 = Op('ad', [], offset=1, val=1)
        doc2.apply_op(op2)
        assert doc2.get_value([1]) == 'normal, ol string'

        # from nested lists
        op3 = Op('ad', [2], offset=1, val=1)
        doc2.apply_op(op3)
        assert doc2.get_value([2]) == [['multi'],['array']]

        # delete multiple elements
        op4 = Op('ad', [], offset=0, val=4)
        doc2.apply_op(op4)
        assert doc2.get_snapshot() == [None, 42]

        # delete last in list:
        op5 = Op('ad', [], offset=1, val=1)
        doc2.apply_op(op5)
        assert doc2.get_snapshot() == [None]

        # in dicts
        op6 = Op('ad', ['fifth'], offset=2, val=2)
        doc1.apply_op(op6)
        assert doc1.get_value(['fifth']) == [55,66]

    def test_array_move(self):
        doc1 = self.doc1
        doc2 = self.doc2

        # simple move at root list
        op1 = Op('am', [], offset=2, val=1)
        doc2.apply_op(op1)
        result1 = [{'name':'value'},'normal, ol string', [1,2,3,4],
                   [['multi'],['dimen'],['array']], True, None,42]
        assert doc2.get_snapshot() == result1

        # Move to end of list
        op2 = Op('am', ['fifth'], offset=0, val=3)
        doc1.apply_op(op2)
        result2 = [66,{'sixth': 'deep string'}, 'rw', 55]
        assert doc1.get_value(['fifth']) == result2

    def test_object_insert(self):
        doc0 = self.doc0
        doc1 = self.doc1

        # whole doc is a dict. insert a key val pair
        op1 = Op('oi', [], offset='a', val=1)
        doc0.apply_op(op1)
        assert doc0.get_snapshot() == {'a': 1}
        op2 = Op('oi', [], offset='b', val=2)
        doc0.apply_op(op2)
        assert doc0.get_snapshot() == {'a': 1, 'b': 2}

        # nested dicts
        op3 = Op('oi', ['fifth', 2], offset='a', val=1)
        doc1.apply_op(op3)
        result3 = {'sixth': 'deep string', 'a': 1}
        assert doc1.get_value(['fifth', 2]) == result3

        # complex vals
        v = {'X': 'Y', 'Z': [1, 2, 3]}
        op4 = Op('oi', [], offset='c', val=v)
        doc0.apply_op(op4)
        assert doc0.get_snapshot() == {'a': 1,
                                       'b': 2,
                                       'c': {'X': 'Y', 'Z': [1, 2, 3]}}

    def test_object_delete(self):
        doc1 = self.doc1
        doc2 = self.doc2

        #simple delete
        op1 = Op('od', [], offset='second')
        doc1.apply_op(op1)
        result1 = {'first': 'some string',
                   'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}
        assert doc1.get_snapshot() == result1

        # nested
        op2 = Op('od', ['fifth',2], offset='sixth')
        doc1.apply_op(op2)
        result2 = {'first': 'some string',
                   'fifth': [55,66,{}, 'rw']}
        assert doc1.get_snapshot() == result2

