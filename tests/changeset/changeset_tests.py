
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

from changeset import Changeset
from document import Document
import unittest


class TestChangeset(unittest.TestCase):

    def setUp(self):
        self.doc = Document()
        self.doc.content = {'first': 'some string',
                            'second': {'third':'more string',
                                       'fourth':{'numb':55}},
                            'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}

        self.c1 = Changeset('insert_pair', 1, 0, '', 'new_key')
        self.c2 = Changeset('insert_pair', 1, 0, [], 'new_key')
        self.c3 = Changeset('insert_pair', 1, 0, pos='new_key')
        self.c4 = Changeset('insert_pair', 1, 0, 'second,fourth', 'new_key')

        self.c5 = Changeset('remove_pair', 1, 0, '', 'first')
        self.c6 = Changeset('remove_pair', 1, 0, '', 'second')
        self.c7 = Changeset('remove_pair', 1, 0, 'second', 'fourth')
        self.c8 = Changeset('remove_pair', 1, 0, 'fifth,2', 'sixth')

        self.c9 = Changeset('insert_into_array', 1, 0, 'fifth', 1, value=77)
        self.c10 = Changeset('insert_into_array', 1, 0, 'fifth', 2, value=88)
        self.c11 = Changeset('insert_into_array', 1, 0, 'fifth', 3, value=99)
        self.c12 = Changeset('insert_pair', 1, 0, 'fifth,2', 'new_key', 55)

    def test_init(self):
        # these three objects should end up the same
        self.assertEqual(self.c1.op, self.c2.op)
        self.assertEqual(self.c1.pos, self.c2.pos)
        self.assertEqual(self.c1.path, self.c2.path)
        self.assertEqual(self.c3.path, self.c2.path)

    def test_parse_path(self):
        path1 = ''
        result1 = []

        path2 = 'first'
        result2 = ['first']

        path3 = 'second,third'
        result3 = ['second', 'third']

        path4 = 'fifth,1'
        result4 = ['fifth', 1]

        path5 = 'fifth,2,sixth'
        result5 = ['fifth', 2, 'sixth']

        path6 = '0,fifth,3'
        result6 = [0,'fifth',3]

        self.c1.path = ''
        self.assertEqual(self.c1.parse_path(path1), result1)
        self.assertEqual(self.c1.parse_path(path2), result2)
        self.assertEqual(self.c1.parse_path(path3), result3)
        self.assertEqual(self.c1.parse_path(path4), result4)
        self.assertEqual(self.c1.parse_path(path5), result5)
        self.assertEqual(self.c1.parse_path(path6), result6)
        self.assertEqual(self.c1.path, result6)


    def test_merge_insert_pair_and_insert_merge(self):
        # past revision merged is an insert_pair. Only revision number
        # changes
        self.c1.merge_in_insert_pair(self.c2)
        self.assertEqual(self.c1.rev_raw, 1)
        self.assertEqual(self.c1.rev, 2)
        self.assertEqual(self.c1.op, 'insert_pair')
        self.assertEqual(self.c1.pos, 'new_key')

    def test_merge_in_remove_pair(self):
        # Whenever an old revision is 'remove_pair', the logic should
        # be the same. If subsequent changes are not a part of the
        # removed node, they are unaffected. If they are a part of the
        # removed node, the new opperation is nullified.

        # c5 should not affect c1
        self.c1.merge_past_changeset(self.c5)
        self.assertEqual(self.c1.op, 'insert_pair')

        # c6 should affect c4 (simple path)
        self.c4.merge_past_changeset(self.c6)
        self.assertEqual(self.c4.op, None)

        self.setUp()
        # c7 should affect c4 (more complicated path)
        self.c4.merge_past_changeset(self.c7)
        self.assertEqual(self.c4.op, None)

    def test_merge_in_insert_into_array(self):
        # c11 should not affect c12
        self.c12.merge_past_changeset(self.c11)
        self.assertEqual(self.c12.path, ['fifth',2])

        # c10 should affect c12
        self.c12.merge_past_changeset(self.c10)
        self.assertEqual(self.c12.path, ['fifth',3])

        # c1 should not affect c12
        self.c12.merge_past_changeset(self.c1)
        self.assertEqual(self.c12.path, ['fifth',3])

        # c9 should not affect c12
        self.c12.merge_past_changeset(self.c9)
        self.assertEqual(self.c12.path, ['fifth',4])

        # When inserting into the same place, figure out which order
        # they should go
        c1 = Changeset('insert_into_array', 1, 0, 'fifth', 3, value=19)
        c2 = Changeset('insert_into_array', 1, 0, 'fifth', 3, value=99)
        c1.merge_past_changeset(c2)
        self.assertEqual(c1.pos, 3)

        c2.merge_past_changeset(c1)
        self.assertEqual(c2.pos, 4)

if __name__ == '__main__':
    unittest.main()
