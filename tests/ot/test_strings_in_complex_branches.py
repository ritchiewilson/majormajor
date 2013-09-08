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

from majormajor.document import Document
from majormajor.changeset import Changeset
from majormajor.ops.op import Op
import random
import string


class TestStringsInComplexBranches:
    def get_printable_ascii(self):
        return string.letters + string.digits

    def build_random_initial_document(self):
        snapshot = ''.join(random.sample(self.remaining_chars, 10))
        doc = Document(snapshot=snapshot)
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
        # pick a random changeset to start building off of
        parent = random.choice(doc.get_ordered_changesets())
        branch_length = random.choice(xrange(4, 10))
        for x in xrange(branch_length):
            # revert document to when it went as far as parent
            doc.rebuild_historical_document([parent])
            insert = random.random() > 0.3
            if not self.remaining_chars:
                insert = False
            if insert:
                parent = self.build_random_string_insert(parent)
            else:
                parent = self.build_random_string_delete(parent)
        # Pull back in all changesets
        doc.pull_from_pending_list()

        # create a new changeset which just ties that branch back to the other
        # dependencies
        deps = doc.get_dependencies()
        deps.remove(parent)
        # chose another dep, if able
        if len(deps) != 0:
            dep = random.choice(deps)
            deps = [parent, dep]
            cs = Changeset(doc.get_id(), 'u1', deps)
            doc.receive_changeset(cs)

    def build_random_string_insert(self, parent):
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

        cs = Changeset(doc.get_id(), 'u1', [parent])
        cs.add_op(Op('si', [], offset=offset, val=val))
        doc.receive_changeset(cs)
        return cs

    def build_random_string_delete(self, parent):
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
        cs = Changeset(doc.get_id(), 'u1', [parent])
        cs.add_op(Op('sd', [], offset=offset, val=val))
        doc.receive_changeset(cs)
        return cs

    def test_build_random_changesets(self):
        self.build_results_dict()
        self.build_random_initial_document()
        while self.remaining_chars:
            self.build_branch()
        self.verify_results()

    def verify_results(self):
        with open('file.dot', 'w') as f:
            f.write(self.doc.get_tree_dotfile())
        # need to chekc a lot of indexes, so cache them in a dict
        snap_dict = {}
        for i, c in enumerate(self.doc.get_snapshot()):
            snap_dict[c] = i
        for k, v in self.results.items():
            if v['deleted']:
                assert not k in snap_dict
                continue
            if not k in snap_dict:
                continue
            for c in v['before']:
                if c in snap_dict:
                    assert snap_dict[c] < snap_dict[k]
            for c in v['after']:
                if c in snap_dict:
                    assert snap_dict[c] > snap_dict[k]
