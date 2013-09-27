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

"""
An String Insert (A) may collect a hazard relating to a future insert
(B). But that future insert B is later deleted by C which does not have A in
its history. An interbranch Hazard needs to be sent to that past op A. Later,
if A is being applied to something that knows about B but not C, it will only
use the original Hazard. If it is being applied to something which has both B
and C in its history, then the interbranch Hazard is also applied.


TODO: This data was pulled from a failing random test. It is long, and hard to
read.
"""

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


class HazardForPastInsertWhenFutureInsertIsDeleted:

    def build_changesets_from_tuples(self, css_data, doc):
        css = []
        for cs_data in css_data:
            action, offset, val, deps, _id = cs_data
            deps = [doc.get_root_changeset() if dep == 'root' else dep
                    for dep in deps]
            cs = Changeset(doc.get_id(), 'u1', deps)
            cs.add_op(Op(action, [], offset=offset, val=val))
            cs.set_id(_id)
            css.append(cs)
        return css

    def test_insert_gets_deleted_document(self):
        doc = Document(snapshot='05IiYTALOC')
        doc.HAS_EVENT_LOOP = False

        css_data = [
            ('si', 8, '3Z', ['root'], 'ba4'),  # 05IiYTAL 3Z OC

            ('si', 2, 'XkGu', ['ba4'], '179'),  # 05 XkGu IiYTAL3ZOC
            ('si', 9, 'Mpb', ['179'], '9b5'),  # 05XkGuIiY Mpb TAL3ZOC
            ('si', 18, '6wc2', ['9b5'], '133'),  # 05XkGuIiYMpbTAL3ZO 6wc2 C
            ('si', 4, 'xUg', ['133'], '36f'),  # 05Xk xUg GuIiYMpbTAL3ZO6wc2C
            ('si', 4, 'NdKa', ['36f'], '6ad'),
            # 05Xk NdKa xUgGuIiYMpbTAL3ZO6wc2C
            ('si', 15, 'hE', ['6ad'], 'ebe'),
            # 05XkNdKaxUgGuIi hE YMpbTAL3ZO6wc2C
            ('si', 23, 'H7', ['ebe'], '2b6'),
            # 05XkNdKaxUgGuIihEYMpbTA H7 L3ZO6wc2C
            ('si', 34, 'yD', ['2b6'], 'c0c'),
            # 05XkNdKaxUgGuIihEYMpbTAH7L3ZO6wc2C yD

            ('sd', 5, 5, ['ba4'], 'b31'),  # delete TAL3Z
            ('si', 4, '9R', ['b31'], '96a'),  # 05Ii 9R YOC
            ('sd', 2, 4, ['96a'], '74e'),  # delete Ii9R

            ('si', 1, '41', ['74e'], '2f0'),  # 0 41 5YOC
            ('si', 0, 'oQmB', ['2f0'], 'ffc'),  # oQmB 0415YOC
            ('sd', 2, 4, ['ffc'], 'da8'),  # delete mB04
            ('si', 3, 'rn', ['da8'], '36d'),  # oQ1 rn 5YOC

            ('si', 0, 'qtWS', ['74e'], 'd96'),  # qtWS 05YOC'
            ('si', 2, 'Psj', ['d96'], '319'),  # qt Psj WS05YOC
            ('si', 6, 'FV', ['319'], '20e'),  # qtPsjW FV S05YOC
            ('si', 9, 'lJve', ['20e'], '5ef'),  # qtPsjWFVS lJve 05YOC

            ('si', 8, 'zf8', ['5ef', '36d'], 'c73'),  # oQ1rn5YO zf8 C
            ('sd', 29, 3, ['c0c', 'c73'], '5f3'),

        ]

        self.css = self.build_changesets_from_tuples(css_data, doc)
        get_cs = self.get_cs

        doc.receive_changeset(self.css[0])
        assert doc.get_snapshot() == '05IiYTAL3ZOC'

        if True:
            cs = get_cs('179')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkGuIiYTAL3ZOC'

            cs = get_cs('9b5')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkGuIiYMpbTAL3ZOC'

            cs = get_cs('133')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkGuIiYMpbTAL3ZO6wc2C'

            cs = get_cs('36f')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkxUgGuIiYMpbTAL3ZO6wc2C'

            cs = get_cs('6ad')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkNdKaxUgGuIiYMpbTAL3ZO6wc2C'

            cs = get_cs('ebe')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkNdKaxUgGuIihEYMpbTAL3ZO6wc2C'

            cs = get_cs('2b6')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkNdKaxUgGuIihEYMpbTAH7L3ZO6wc2C'

            cs = get_cs('c0c')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '05XkNdKaxUgGuIihEYMpbTAH7L3ZO6wc2CyD'

        cs = get_cs('b31')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == '05XkNdKaxUgGuIihEYMpbO6wc2CyD'

        cs = get_cs('96a')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == '05XkNdKaxUgGuIihE9RYMpbO6wc2CyD'

        cs = get_cs('74e')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == '05XkNdKaxUgGuYMpbO6wc2CyD'

        if True:
            cs = get_cs('2f0')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == '0415XkNdKaxUgGuYMpbO6wc2CyD'

            cs = get_cs('ffc')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == 'oQmB0415XkNdKaxUgGuYMpbO6wc2CyD'

            cs = get_cs('da8')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == 'oQ15XkNdKaxUgGuYMpbO6wc2CyD'

            cs = get_cs('36d')
            doc.receive_changeset(cs)
            assert doc.get_snapshot() == 'oQ1rn5XkNdKaxUgGuYMpbO6wc2CyD'

        cs = get_cs('d96')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'oQ1rn5XkNdKaxUgGuYMpbO6wc2CyD'

        cs = get_cs('319')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'oQ1rn5XkNdKaxUgGuYMpbO6wc2CyD'

        cs = get_cs('20e')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'oQ1rn5XkNdKaxUgGuYMpbO6wc2CyD'

        cs = get_cs('5ef')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'oQ1rn5XkNdKaxUgGuYMpbO6wc2CyD'

        cs = get_cs('c73')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'oQ1rn5XkNdKaxUgGuYMpbO6wc2zf8CyD'

    def get_cs(self, _id):
        for cs in self.css:
            if cs.get_short_id() == _id:
                return cs
        raise Exception("wrong id, jerk", _id)
