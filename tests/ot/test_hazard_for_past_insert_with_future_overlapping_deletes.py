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
The first branch has a string insert op then deletes the letter 'j' among
others. In the second branch, the letter 'j' is also deleted in changeset
dd8. In the third branch, 'j' is also deleted in branch 64d. The tripple
overlapping delete was working fine, but the overlapping delete in branches two
and three needed to be accounted for in the ops before branch A deletes.
"""

from majormajor.document import Document

from tests.test_utils import build_changesets_from_tuples


class HazardForPastInsertWithFutureOverlappingDeletes:

    def test_hazard_for_insert_with_future_overlapping_deletes(self):
        doc = Document(snapshot='WfjxUPBNyE')
        doc.HAS_EVENT_LOOP = False

        # Both dd8 and 64d delete the string '7j'. That overlap must be relayed
        # back to cs 98c.

        css_data = [
            ('si', 3, 'iu0I', ['root'], 'b3a'),  # Wfj iu0I xUPBNyE

            ('si', 12, 'p5Z', ['b3a'], '98c'),  # Wfjiu0IxUPBN p5Z yE
            ('sd', 1, 3, ['98c'], 'c3e'),  # delete fji
            ('si', 11, 'DRv', ['c3e'], '3c6'),  # Wu0IxUPBNp5 DRv ZyE
            ('si', 0, 'Tt9G', ['3c6'], 'bdd'),  # Tt9G Wu0IxUPBNp5DRvZyE
            ('si', 0, 'gkrY', ['bdd'], '44e'),  # gkrY Tt9GWu0IxUPBNp5DRvZyE
            ('si', 0, 'M', ['44e'], '79b'),  # M gkrYTt9GWu0IxUPBNp5DRvZyE

            ('si', 0, '7O', ['b3a'], 'fb7'),  # 7O Wfjiu0IxUPBNyE
            ('si', 14, 'ad', ['fb7'], '26f'),  # 7OWfjiu0IxUPBN ad yE
            ('si', 11, 'w8cK', ['26f'], '7c3'),  # 7OWfjiu0IxU w8cK PBNadyE
            ('si', 20, 'mb', ['7c3'], '810'),  # 7OWfjiu0IxUw8cKPBNad mb yE
            ('sd', 1, 3, ['810'], '254'),  # delete OWf

            ('si', 7, 'J1', ['254'], '39c'),  # 7jiu0Ix J1 Uw8cKPBNadmbyE
            ('sd', 19, 1, ['39c'], '4c6'),  # delete m
            ('si', 12, 'e4', ['4c6'], '44f'),  # 7jiu0IxJ1Uw8 e4 cKPBNadbyE
            ('si', 19, 'LV', ['44f'], 'b25'),  # 7jiu0IxJ1Uw8e4cKPBN LV adbyE
            ('sd', 0, 3, ['b25'], 'dd8'),  # delete 7ji
            ('si', 14, 'hH2s', ['dd8'], 'bac'),
            # u0IxJ1Uw8e4cKP hH2s BNLVadbyE

            ('sd', 0, 2, ['254'], '64d'),  # delete 7j

            ('si', 2, '6nA', ['bac', '64d'], '25f'),
            # u0 6nA IxJ1Uw8e4cKPhH2sBNLVadbyE
            ('sd', 7, 4, ['25f'], '35a'),
            # delete J1Uw
            ('si', 9, '3lSz', ['35a'], 'b0c'),
            # u06nAIx8e 3lSz 4cKPhH2sBNLVadbyE
            ('si', 21, 'CXqQ', ['b0c'], '017'),
            # u06nAIx8e3lSz4cKPhH2s CXqQ BNLVadbyE
            ('si', 26, 'Fo', ['017'], '68e'),
            # u06nAIx8e3lSz4cKPhH2sCXqQB Fo NLVadbyE

            ('sd', 23, 5, ['79b', '68e'], '895'),  # delete cKPhH
        ]

        self.css = build_changesets_from_tuples(css_data, doc)
        get_cs = self.get_cs

        for i in self.css[:7]:
            doc.receive_changeset(i)
        assert doc.get_snapshot() == 'MgkrYTt9GWu0IxUPBNp5DRvZyE'

        cs = get_cs('fb7')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7OWu0IxUPBNp5DRvZyE'

        cs = get_cs('26f')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7OWu0IxUPBNp5DRvZadyE'

        cs = get_cs('7c3')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7OWu0IxUw8cKPBNp5DRvZadyE'

        cs = get_cs('810')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7OWu0IxUw8cKPBNp5DRvZadmbyE'

        cs = get_cs('254')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7u0IxUw8cKPBNp5DRvZadmbyE'

        cs = get_cs('39c')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7u0IxJ1Uw8cKPBNp5DRvZadmbyE'

        cs = get_cs('4c6')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7u0IxJ1Uw8cKPBNp5DRvZadbyE'

        cs = get_cs('44f')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7u0IxJ1Uw8e4cKPBNp5DRvZadbyE'

        cs = get_cs('b25')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9G7u0IxJ1Uw8e4cKPBNp5DRvZLVadbyE'

        cs = get_cs('dd8')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == 'MgkrYTt9Gu0IxJ1Uw8e4cKPBNp5DRvZLVadbyE'

        cs = get_cs('bac')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu0IxJ1Uw8e4cKPhH2sBNp5DRvZLVadbyE'

        cs = get_cs('64d')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu0IxJ1Uw8e4cKPhH2sBNp5DRvZLVadbyE'

        cs = get_cs('25f')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu06nAIxJ1Uw8e4cKPhH2sBNp5DRvZLVadbyE'

        cs = get_cs('35a')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu06nAIx8e4cKPhH2sBNp5DRvZLVadbyE'

        cs = get_cs('b0c')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu06nAIx8e3lSz4cKPhH2sBNp5DRvZLVadbyE'

        cs = get_cs('017')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu06nAIx8e3lSz4cKPhH2sCXqQBNp5DRvZLVadbyE'

        cs = get_cs('68e')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu06nAIx8e3lSz4cKPhH2sCXqQBFoNp5DRvZLVadbyE'

        cs = get_cs('895')
        doc.receive_changeset(cs)
        assert doc.get_snapshot() == \
            'MgkrYTt9Gu06nAIx8e3lSz42sCXqQBFoNp5DRvZLVadbyE'

    def get_cs(self, _id):
        for cs in self.css:
            if cs.get_short_id() == _id:
                return cs
        raise Exception("wrong id, jerk", _id)
