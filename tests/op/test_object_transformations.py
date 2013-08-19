
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

"""
Testing simple operational transformation (ignoring hazards) for Object
transformations, Object Insert and Object Delete
"""

from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class TestObjectTransformations:
    def test_oi_oi(self):
        """
        A past opperation is an Object insert which gets applied to this object
        insert. The only opportunity for conflict is if the later insert
        happens along a path that is no longer valid.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('oi', array_path, offset='X', val=['Y', 'Z'])
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('oi', ['a', 'b', 3, 5], offset='c', val=["XYZ"])
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        op1.hazards = []

        # op3 happens along path, so it will just overwrite past data
        op3 = Op('oi', ['a'], offset='b', val="XYZ")
        op3.ot(cs1)
        assert op3.t_path == ['a']
        assert op3.t_offset == 'b'
        assert op3.t_val == 'XYZ'
        op1.hazards = []

        # op4 is at same path, different offset, so no conflict
        op4 = Op('oi', array_path, offset='W', val="WWW")
        op4.ot(cs1)
        assert op4.t_path == array_path
        assert op4.t_offset == 'W'
        assert op4.t_val == 'WWW'
        assert not op4.is_noop()
        op1.hazards = []

        # op5 is at same path and offset, so previous op takes precedence
        op5 = Op('oi', array_path, offset='X', val=["XXX"])
        op5.ot(cs1)
        assert op5.t_path == array_path
        assert op5.t_offset == 'X'
        assert op5.t_val == ['XXX']
        assert op5.is_noop()
        op1.hazards = []

        # op6 path is deep within a previous object insert
        op6_path = array_path + ['X', 9, 'c']
        op6 = Op('oi', op6_path, offset=8, val=["XYZ"])
        op6.ot(cs1)
        assert op6.is_noop()
        op1.hazards = []

    def test_od_oi(self):
        """
        A past opperations is an object delete which gets applied to this
        object insert.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('od', array_path, offset='X')
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('oi', ['a', 'b', 3, 5], offset='Y', val=['XYZ'])
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        assert op2.t_offset == 'Y'
        assert op2.t_val == ['XYZ']
        assert not op2.is_noop()
        op1.hazards = []

        # op3 happens at path, but differant offset, no change
        op3 = Op('oi', array_path, offset='W', val=['XYZ'])
        op3.ot(cs1)
        assert op3.t_path == array_path
        assert op3.t_offset == 'W'
        assert not op3.is_noop()
        op1.hazards = []

        # op4 happens within deletion
        op4_path = array_path + ['X']
        op4 = Op('oi', op4_path, offset='R', val=['XYZ'])
        op4.ot(cs1)
        assert op4.is_noop()
        op1.hazards = []

        # op5 inserts right where there was a deletion. Some previous conflict,
        # so noop
        op5 = Op('oi', array_path, offset='X', val='XYZ')
        op5.ot(cs1)
        assert op5.t_path == array_path
        assert op5.t_offset == 'X'
        assert op5.t_val == 'XYZ'
        assert op5.is_noop()
        op1.hazards = []

        # op6 is at a partial path along deletion, no change
        op6_path = ['a']
        op6 = Op('oi', op6_path, offset='c', val=['XYZ'])
        op6.ot(cs1)
        assert op6.t_path == ['a']
        assert op6.t_offset == 'c'
        assert op6.t_val == ['XYZ']
        assert not op6.is_noop()
        op1.hazards = []

    def test_oi_od(self):
        """
        A past opperation is an object insert which gets applied to these
        object deletes.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('oi', array_path, offset='X', val=['X', 'Y'])
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('od', ['a', 'b', 3, 5], offset='R')
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        assert op2.t_offset == 'R'
        assert not op2.is_noop()
        op1.hazards = []

        # op3 deletes a key were unknown op had inserted one. Could not have
        # intended to delete what it did not know, so noop
        op3 = Op('od', array_path, offset='X')
        op3.ot(cs1)
        assert op3.t_path == array_path
        assert op3.t_offset == 'X'
        assert op3.is_noop()
        op1.hazards = []

        # same as above, but well within the inserted value
        op4_path = array_path + ['X']
        op4 = Op('od', op4_path, offset='Y')
        op4.ot(cs1)
        assert op4.t_path == array_path + ['X']
        assert op4.t_offset == 'Y'
        assert op4.is_noop()
        op1.hazards = []

        # op5 is at same path, differant offset. No change
        op5 = Op('od', array_path, offset='R')
        op5.ot(cs1)
        assert op5.t_path == array_path
        assert op5.t_offset == 'R'
        assert not op5.is_noop()
        op1.hazards = []

        # op6 is at shorter path. No change
        op6 = Op('od', ['a'], offset='c')
        op6.ot(cs1)
        assert op6.t_path == ['a']
        assert op6.t_offset == 'c'
        assert not op6.is_noop()
        op1.hazards = []

        # op7 deletes whatever was previously changed
        op7 = Op('od', ['a'], offset='b')
        op7.ot(cs1)
        assert op7.t_path == ['a']
        assert op7.t_offset == 'b'
        assert not op7.is_noop()
        op1.hazards = []

    def test_od_od(self):
        """
        A past opperation is an object delete which gets applied to these
        object deletes.
        """
        array_path = ['a', 'b', 3, 4]
        op1 = Op('od', array_path, offset='X')
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a different path, so should not be affected
        op2 = Op('od', ['a', 'b', 3, 5], offset='Y')
        op2.ot(cs1)
        assert op2.t_path == ['a', 'b', 3, 5]
        assert op2.t_offset == 'Y'
        assert not op2.is_noop()
        op1.hazards = []

        # op3 happens at same path but different offset
        op3 = Op('od', array_path, offset='R')
        op3.ot(cs1)
        assert op3.t_path == array_path
        assert op3.t_offset == 'R'
        assert not op3.is_noop()
        op1.hazards = []

        # op4 tries to delete the same key as op1
        op4 = Op('od', array_path, offset='X')
        op4.ot(cs1)
        assert op4.is_noop()
        op1.hazards = []

        # op5 tries to delete something within what was already deleted
        op5_path = array_path + ['X']
        op5 = Op('od', op5_path, offset='R')
        op5.ot(cs1)
        assert op5.is_noop()
        op1.hazards = []

        # op6 is at a shorter, different path. No change
        op6_path = ['a']
        op6 = Op('od', op6_path, offset='c')
        op6.ot(cs1)
        assert op6.t_path == ['a']
        assert op6.t_offset == 'c'
        assert not op6.is_noop()
        op1.hazards = []

        # op9 is at shorter, same path. No change
        op9_path = ['a']
        op9 = Op('od', op9_path, offset='b')
        op9.ot(cs1)
        assert op9.t_path == op9_path
        assert op9.t_offset == 'b'
        assert not op9.is_noop()
        op1.hazards = []
