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
from majormajor.changeset import Changeset
from majormajor.ops.op import Op
import random

import pytest


class TestRandomStringsWithTwoUsers:
    MAX_CHARS = 10000

    def get_printable_ascii(self):
        import string
        #return string.letters + string.digits
        y = [unichr(i) for i in xrange(33, self.MAX_CHARS + 33)]
        return u''.join(y)

    def build_random_initial_document(self):
        snapshot = ''.join(random.sample(self.remaining_chars, 100))
        doc = _Document(snapshot=snapshot)
        doc.get_ordered_changesets()[0].ops[0].cheat = ""
        for i, char in enumerate(snapshot):
            before = list(snapshot[:i])
            after = list(snapshot[i + 1:])
            self.results[char]['before'] = before
            self.results[char]['after'] = after
            self.remaining_chars = self.remaining_chars.replace(char, '')
        doc.HAS_EVENT_LOOP = False
        self.doc = doc
        return doc

    def build_results_dict(self):
        self.remaining_chars = self.get_printable_ascii()
        d = {}
        for char in self.remaining_chars:
            d[char] = {'before': [],
                       'after': [],
                       'deleted': False}
        self.results = d
        return d

    def build_branch(self):
        doc = self.doc
        parent = doc.get_root_changeset()
        letters_to_insert = len(self.remaining_chars)
        first_branch = False
        if len(doc.get_ordered_changesets()) == 1:
            letters_to_insert = int(random.triangular(0, self.MAX_CHARS))
            first_branch = True
        else:
            doc.rebuild_historical_document([parent])
        while letters_to_insert > 0:
            cs = Changeset(doc.get_id(), str(self.user_vector), [parent])
            op = self.build_random_insert_or_delete()
            cs.add_op(op)
            doc.receive_changeset(cs, pull=False)
            if op.is_string_insert():
                letters_to_insert -= len(op.get_val())
            parent = cs
            if len(self.remaining_chars) == 0:
                break
        # Pull back in all changesets
        if not first_branch:
            doc.pull_from_pending_list()

    def build_random_insert_or_delete(self):
        insert = random.random() > 0.2
        if not self.remaining_chars:
            insert = False
        if insert:
            return self.build_random_string_insert()
        return self.build_random_string_delete()

    def build_random_string_insert(self):
        doc = self.doc
        snapshot = doc.get_snapshot()

        val = ''
        if len(self.remaining_chars) < 4:
            val = self.remaining_chars
        else:
            # pick random sample size
            k = random.choice(xrange(2, 5))
            # pick random letters
            val = ''.join(random.sample(self.remaining_chars, k))
        # pick random insertion point
        offset = random.choice(xrange(len(snapshot) + 1))

        # The inserted characters should appear after any existing character
        # before the offset
        previous_chars = snapshot[:offset]
        for char in previous_chars:
            self.results[char]['after'].extend(list(val))
        # The inserted characters should appear before any existing character
        # after the insertion
        subsequent_chars = snapshot[offset:]
        for char in subsequent_chars:
            self.results[char]['before'].extend(list(val))

        for i, char in enumerate(val):
            r = self.results[char]
            r['before'] = list(snapshot[:offset])
            r['before'].extend(list(val[:i]))
            r['after'] = list(snapshot[offset:])
            r['after'].extend(list(val[i + 1:]))
            self.remaining_chars = self.remaining_chars.replace(char, '')

        op = Op('si', [], offset=offset, val=val)
        op.cheat = previous_chars + " " + val + " " + subsequent_chars
        return op

    def build_random_string_delete(self):
        doc = self.doc
        snapshot = doc.get_snapshot()

        # pick random offset
        offset = 0
        if len(snapshot) > 1:
            offset = random.choice(xrange(len(snapshot)))

        # get random size for delete range
        characters_past_offset = len(snapshot[offset:])
        max_val = min(5, characters_past_offset)
        val = 0
        # as long as there is something in the snapshot, pick a delete size
        # larger than zero
        if characters_past_offset != 0:
            val = random.choice(xrange(max_val)) + 1

        deleted_chars = snapshot[offset:offset + val]
        for char in deleted_chars:
            self.results[char]['deleted'] = True
        op = Op('sd', [], offset=offset, val=val)
        op.cheat = "delete " + deleted_chars
        return op

    @pytest.mark.parametrize(('i'), [(i) for i in xrange(1)])
    def Xtest_full_runs(self, i):
        self.user_vector = 0  # ocasionally running into hash
                              # collisions. Change the username to avoid this.
        self.full_run()
        self.dump_doc()

    def full_run(self):
        self.build_results_dict()
        self.build_random_initial_document()
        while self.remaining_chars:
            self.build_branch()
        self.verify_results()

    def verify_results(self):
        # need to chekc a lot of indexes, so cache them in a dict
        snap_dict = {}
        for i, c in enumerate(self.doc.get_snapshot()):
            snap_dict[c] = i
        for k, v in self.results.items():
            if v['deleted']:
                if k in snap_dict: self.dump_doc()
                assert not k in snap_dict
                continue
            if not k in snap_dict:
                continue
            for c in v['before']:
                if c in snap_dict:
                    if snap_dict[c] > snap_dict[k]: self.dump_doc()
                    assert snap_dict[c] < snap_dict[k]
            for c in v['after']:
                if c in snap_dict:
                    if snap_dict[c] < snap_dict[k]: self.dump_doc()
                    assert snap_dict[c] > snap_dict[k]

    def dump_doc(self):
        with open('file.dot', 'w') as f:
            f.write(self.doc.get_tree_dotfile(show_ops=False))
        return
        with open('cs_data.txt', 'w') as f:
            for cs in self.doc.get_ordered_changesets():
                op = cs.get_ops()[0]
                t = (op.action, op.offset, op.val,
                     [c.get_short_id() for c in cs.get_parents()],
                     cs.get_short_id())
                f.write(str(t))
                f.write(',  # ')
                f.write(op.cheat)
                f.write('\n')
            f.write('\n\n')
            f.write(str(self.results))
            f.write('\n\n')
            for cs in self.doc.get_ordered_changesets():
                f.write(cs.get_short_id())
                f.write('\n')
                f.write(str([c.get_short_id() for c in cs.get_children()]))
                f.write('\n')
