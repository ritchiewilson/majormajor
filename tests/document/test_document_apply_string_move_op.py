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


class TestDocumentApplyStringMoveOp:
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

    def test_move_in_root(self):
        doc = _Document()
        doc.snapshot.set_snapshot('ABCDEFGHIJKLMNOPQRS')

        # move from higher index to lower
        op1 = Op('sm', [], offset=10, val=4, dest_path=[], dest_offset=2)
        doc.apply_op(op1)
        assert doc.get_snapshot() == 'ABKLMNCDEFGHIJOPQRS'

        # move from lower index to higher
        op2 = Op('sm', [], offset=2, val=4, dest_path=[], dest_offset=10)
        doc.apply_op(op2)
        assert doc.get_snapshot() == 'ABCDEFGHIJKLMNOPQRS'  # original value

        # move by one index
        op3 = Op('sm', [], offset=0, val=6, dest_path=[], dest_offset=1)
        doc.apply_op(op3)
        assert doc.get_snapshot() == 'GABCDEFHIJKLMNOPQRS'

        op4 = Op('sm', [], offset=10, val=9, dest_path=[], dest_offset=0)
        doc.apply_op(op4)
        assert doc.get_snapshot() == 'KLMNOPQRSGABCDEFHIJ'

    def test_move_in_same_path(self):
        doc1 = self.doc1

        path1 = ['fifth', 2, 'sixth']
        op1 = Op('sm', path1, offset=4, val=1, dest_path=path1, dest_offset=0)
        doc1.apply_op(op1)
        assert doc1.get_value(path1) == ' deepstring'
        op2 = Op('sm', path1, offset=5, val=6, dest_path=path1, dest_offset=0)
        doc1.apply_op(op2)
        assert doc1.get_value(path1) == 'string deep'

        doc2 = self.doc2

        path2 = [3, 2, 0]
        op3 = Op('sm', path2, offset=0, val=2, dest_path=path2, dest_offset=2)
        doc2.apply_op(op3)
        assert doc2.get_value(path2) == 'raary'

    def test_move_to_different_paths(self):
        doc1 = self.doc1

        path1 = ['first']
        path2 = ['fifth', 2, 'sixth']
        path3 = ['second', 'third']
        op1 = Op('sm', path1, offset=2, val=3,
                 dest_path=path2, dest_offset=4)
        doc1.apply_op(op1)
        result1 = {'first': 'sostring',
                   'second': {'third': 'more string',
                              'fourth': {'numb': 55}},
                   'fifth': [55, 66, {'sixth': 'deepme  string'}, 'rw']}
        assert doc1.get_snapshot() == result1

        op2 = Op('sm', path2, offset=1, val=10,
                 dest_path=path3, dest_offset=7)
        doc1.apply_op(op2)
        result2 = {'first': 'sostring',
                   'second': {'third': 'more steepme  strring',
                              'fourth': {'numb': 55}},
                   'fifth': [55, 66, {'sixth': 'ding'}, 'rw']}
        assert doc1.get_snapshot() == result2
