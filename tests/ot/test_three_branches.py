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


import pytest

from majormajor.document import Document
from majormajor.ops.op import Op
from majormajor.changeset import Changeset


def add_switches(params, n):
    switches = [(i, n) for i in xrange(pow(2,n))]
    bool_switches = [parse_switches(s) for s in switches]
    params = [p + s for p in params for s in bool_switches]
    return params



def parse_switches(switches):
    n, total = switches
    bn = str(bin(n))[2:]
    bn = ('0' * (total - len(bn))) + bn
    return [True if x == '0' else False for x in bn]

def build_changesets_from_tuples(css_data, doc):
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


insertion_results = [0, 1, 2, 3, 4, 5]
insertion_results += [None for x in range(14)]
insertion_results += [5, 6, 7, 8, 9, 10, 12]
results = [[i, o] for i, o in enumerate(insertion_results)]
results = add_switches(results, 2)


@pytest.mark.parametrize(('insert_index', 'resulting_index',
                          'insert_first', 'low_index_in_0_branch'),
                         results)
def test_insert_within_overlaping_deletes(insert_index, resulting_index,
                                          insert_first,
                                          low_index_in_0_branch):

    if low_index_in_0_branch:return # or not insert_first: return
    doc = Document(snapshot='abcdefghijklmnopqrstuvwxyz')
    doc.HAS_EVENT_LOOP = False

    first_delete_index = 10 if low_index_in_0_branch else 5
    zero_branch_index = 5 if low_index_in_0_branch else 10

    z_index = 16
    if insert_index > first_delete_index and \
       insert_index < first_delete_index + 10:
        z_index = 15
    if insert_index == 26:
        z_index = 15

    insert_id = 'A' if insert_first else 'B'
    delete_id = 'B' if insert_first else 'A'

    css_data = [
        ('si', insert_index, 'X', ['root'], insert_id),  # insert letter X
        ('sd', first_delete_index, 10, ['root'], delete_id),  # delete 'fghijklmno'
        ('si', z_index, 'Z', ['A', 'B'], 'C'),  # at a 'Z' right before the
                                                # existing 'z'

        ('sd', zero_branch_index, 10, ['root'], '0'),  # delete 'klmnopqrst'
    ]

    css = build_changesets_from_tuples(css_data, doc)

    for cs in css:
        doc.receive_changeset(cs)

    resulting_snapshot = 'abcdeuvwxyZz'
    if not resulting_index is None:
        rs = resulting_snapshot
        ri = resulting_index
        resulting_snapshot = rs[:ri] + 'X' + rs[ri:]
    assert doc.get_snapshot() == resulting_snapshot


params = [(i, True) for i in range(26)]
params += [(i, False) for i in range(26)]


@pytest.mark.parametrize(('delete_index', 'single_first'), params)
def Xtest_overlaping_deletes2(delete_index, single_first):
    original_snapshot = 'abcdefghijklmnopqrstuvwxyz'
    doc = Document(snapshot=original_snapshot)
    doc.HAS_EVENT_LOOP = False

    z_index = 14
    if delete_index >= 5 and delete_index < 15:
        z_index = 15
    if delete_index == 25:
        z_index = 15

    single_id = 'A' if single_first else 'B'
    range_id = 'B' if single_first else 'A'

    css_data = [
        ('sd', delete_index, 1, ['root'], single_id),
        ('sd', 5, 10, ['root'], range_id),  # delete 'fghijklmno'
        ('si', z_index, 'Z', ['A', 'B'], 'C'),

        ('sd', 10, 10, ['root'], '0'),  # delete 'klmnopqrst'
    ]

    css = build_changesets_from_tuples(css_data, doc)

    for cs in css:
        doc.receive_changeset(cs)

    resulting_snapshot = 'abcdeuvwxyZz'
    l = original_snapshot[delete_index]
    resulting_snapshot = resulting_snapshot.replace(l, '')

    assert doc.get_snapshot() == resulting_snapshot
