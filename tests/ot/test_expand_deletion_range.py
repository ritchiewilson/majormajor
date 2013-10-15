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
Some expanded deletion ranges overlapping other deletion ranges
"""

from majormajor.document import Document

from tests.test_utils import build_changesets_from_tuples


class TestExpandDeletionRange:

    def test_expand_deletion_range(self):
        doc = Document(snapshot='HjpRFtZXW5')
        doc.HAS_EVENT_LOOP = False

        css_data = [
            ('si', 7, 'OeI', ['root'], 'c3c'),  # HjpRFtZ OeI XW5
            ('sd', 2, 5, ['c3c'], '950'),  # delete pRFtZ
            ('si', 2, 'Qx', ['950'], 'bf0'),  # Hj Qx OeIXW5
            ('sd', 2, 4, ['bf0'], '4c5'),  # delete QxOe
            ('si', 6, 'U6', ['4c5'], '61a'),  # HjIXW5 U6
            ('si', 3, 'AG', ['61a'], '1f0'),  # HjI AG XW5U6

            ('si', 3, 'qwEg', ['1f0'], '393'),  # HjI qwEg AGXW5U6
            ('si', 9, 'vsY', ['393'], '18d'),  # HjIqwEgAG vsY XW5U6
            ('si', 0, 'MiNV', ['18d'], '688'),  # MiNV HjIqwEgAGvsYXW5U6
            ('si', 20, 'L4n', ['688'], '796'),  # MiNVHjIqwEgAGvsYXW5U L4n 6
            ('si', 5, '9l', ['796'], 'b29'),  # MiNVH 9l jIqwEgAGvsYXW5UL4n6
            ('si', 1, 'k0Jf', ['b29'], 'e1a'),
            # M k0Jf iNVH9ljIqwEgAGvsYXW5UL4n6

            ('si', 8, 'd', ['e1a'], 'a23'),
            # Mk0JfiNV d H9ljIqwEgAGvsYXW5UL4n6

            ('sd', 3, 1, ['1f0'], '47a'),  # delete A
            ('sd', 0, 3, ['47a'], 'cc0'),  # delete HjI
            ('si', 4, 'K1DT', ['cc0'], 'd32'),  # GXW5 K1DT U6
            ('si', 5, 'b3oS', ['d32'], '175'),  # GXW5K b3oS 1DTU6
            ('si', 3, 'hm8z', ['175'], 'd28'),  # GXW hm8z 5Kb3oS1DTU6

            ('sd', 0, 5, ['1f0'], '997'),  # delete HjIAG
            ('si', 0, 'rBya', ['997'], '17a'),  # rBya XW5U6
            ('sd', 7, 1, ['17a'], '592'),  # delete U
            ('si', 8, 'cPu', ['592'], '893'),  # rByaXW56 cPu
            ('si', 1, 'C72', ['d28', '893'], 'b20'),
            # r C72 ByaXWhm8z5Kb3oS1DT6cPu

            ('sd', 37, 3, ['a23', 'b20'], '9e0'),  # delete 6cP
        ]

        self.css = build_changesets_from_tuples(css_data, doc)
        get_cs = self.get_cs

        for i in self.css[:13]:
            doc.receive_changeset(i)
        assert doc.get_snapshot() == 'Mk0JfiNVdH9ljIqwEgAGvsYXW5UL4n6'

        for i in self.css[13:18]:
            doc.receive_changeset(i)
        assert doc.get_snapshot() == 'Mk0JfiNVdqwEgGvsYXWhm8z5Kb3oS1DTUL4n6'

        cs = get_cs('997')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'Mk0JfiNVdvsYXWhm8z5Kb3oS1DTUL4n6'

        cs = get_cs('17a')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'Mk0JfiNVdvsYrByaXWhm8z5Kb3oS1DTUL4n6'

        cs = get_cs('592')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'Mk0JfiNVdvsYrByaXWhm8z5Kb3oS1DTL4n6'

        cs = get_cs('893')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'Mk0JfiNVdvsYrByaXWhm8z5Kb3oS1DTL4n6cPu'

        cs = get_cs('b20')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'Mk0JfiNVdvsYrC72ByaXWhm8z5Kb3oS1DTL4n6cPu'

        cs = get_cs('9e0')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'Mk0JfiNVdvsYrC72ByaXWhm8z5Kb3oS1DTL4nu'

    def get_cs(self, _id):
        for cs in self.css:
            if cs.get_short_id() == _id:
                return cs
        raise Exception("wrong id, jerk", _id)
