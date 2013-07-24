
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

import json, difflib
import random
import string
import uuid
import copy
from datetime import datetime
from changeset import Changeset
from op import Op
from utils import build_changeset_from_dict

class Document:

    # Each document needs an ID so that changesets can be associated
    # with it. If one is not supplied, make a random 5 character ID at
    # start
    def __init__(self, id_ = None, user=None, snapshot=None):
        if id_ == None:
            id_ = ''.join(random.choice(string.ascii_letters + string.digits)
                          for x in range(5))
        self.id_ = id_
        if user == None:
            user = str(uuid.uuid4())
        self.user = user
        self.ordered_changesets = []
        self.ordered_changesets_set_cache = set([])
        self.all_known_changesets = {}
        self.missing_changesets = set([])
        self.send_queue = []
        self.pending_new_changesets = []
        self.open_changeset = None
        self.snapshot = {}
        self.root_changeset = None
        self.dependencies = []
        self.hazards = []
        # set initial snapshot if called upon
        if not snapshot == None:
            self.set_initial_snapshot(snapshot)
        self.dependencies = [self.root_changeset]
        #  With an event loop, many actions happen on a timer. For
        #  testing, there is no event loop, so actions happen
        #  immediately.
        self.HAS_EVENT_LOOP = True
        self.time_of_last_received_cs = datetime.now()

    def get_id(self):
        return self.id_

    def get_user(self):
        return self.user

    def get_last_changeset(self):
        return self.ordered_changesets[-1] if self.ordered_changesets else None

    def get_root_changeset(self):
        return self.root_changeset

    def get_ordered_changesets(self):
        return self.ordered_changesets[:]

    def get_dependencies(self):
        """
        Returns a list of the dependencies that make up the the current
        document. Usually this is a list of with just the most recent
        changeset. There can be multiple changesets if they each
        depend on the same changeset but do not know about each other.
        """
        return self.dependencies[:]

    def get_missing_changeset_ids(self):
        return self.missing_changesets.copy()

    def get_send_queue(self):
        return self.send_queue[:]
    
    def clear_send_queue(self):
        self.send_queue = []
        
    def get_missing_dependency_ids(self, new_cs):
        missing_dep_ids = []
        for dep in new_cs.get_parents():
            if not isinstance(dep, Changeset):
                missing_dep_ids.append(dep)
        return missing_dep_ids
                
    def get_changeset_by_id(self, cs_id):
        if cs_id in self.all_known_changesets:
            return self.all_known_changesets[cs_id]['obj']
        return None

    def get_open_changeset(self):
        return self.open_changeset

    def get_time_of_last_received_cs(self):
        return self.time_of_last_received_cs

    def get_changesets_in_ranges(self, start_ids, end_ids):
        cs_in_range = []            
        start_reached = False if start_ids else True
        for cs in self.ordered_changesets:
            if len(end_ids) == 0:
                break
            if cs.get_id() in end_ids:
                end_ids.pop(end_ids.index(cs.get_id()))
            elif start_reached:
                cs_in_range.append(cs)
            if cs.get_id() in start_ids:
                start_reached = True
        return cs_in_range # TODO needed?

    def get_snapshot(self):
        return self.snapshot

    def get_changesets(self):
        return self.changesets

    def get_sync_status(self, remote_deps):
        request_css = [dep for dep in remote_deps if not self.knows_changeset(dep)]
        send_css = [cs for cs in self.dependencies if not cs.get_id() in remote_deps]
        return request_css, send_css

    def set_initial_snapshot(self, s):
        """
        Can stick in boilerplate snapshot for doc. turns snapshot into an
        opperation.
        TODO - throw exception if doc is not new
        """
        op = Op('set', [], val=s)
        self.add_local_op(op)
        cs = self.close_changeset()
        self.root_changeset = cs
        self.ordered_changesets = [cs]
        self.ordered_changesets_set_cache = set([cs])
        

    def set_snapshot(self, snapshot, deps):
        """
        Reset the snapshot of this documnet. Also needs to take the
        dependency that defines this snapshot. Since the local user
        will be working on from this point, this dependency takes over
        and all previously known changesets are put in the pending
        list until they can be sorted back in.
        """
        self.snapshot = snapshot
        for dep in deps:
            self.add_to_known_changesets(dep)
        self.dependencies = deps



    def knows_changeset(self, cs_id):
        if cs_id in self.all_known_changesets:
            return True
        return False

    def insert_historical_changeset(self, cs):
        """
        Inserts a changeset into the changeset list without performing
        OT. This is done when some future snapshot is known, but its
        history is being put together.
        """
        self.add_to_known_changesets(cs)
        #i = self.insert_changeset_into_changsets(cs)
        #cs.find_unaccounted_changesets(self.changesets[:i])
        return 0 # return index of where it was stuck

        
    def add_local_op(self, op):
        """
        For when this user (not remote collaborators) add an
        opperation. If there is no open changeset, one will be opened
        with correct dependencies and the given op. If a changeset is
        already started, the given op is just added on. The given op
        is then immediatly applied to this Document.
        """
        if self.open_changeset == None:
            self.open_changeset = Changeset(self.id_, self.user,
                                            self.get_dependencies())
        self.open_changeset.add_op(op)
        self.apply_op(op)

    def close_changeset(self):
        """
        Close a changeset so it can be hashed and sent to
        collaborators. Once a changeset is closed it must stay
        unaltered so that sha1 hash is always calculable and
        consistant.

        Adds the changeset to this documents list of dependencies.
        """

        if self.open_changeset and self.open_changeset.is_empty():
            self.open_changeset == None
            
        if self.open_changeset == None:
            return False

        cs = self.open_changeset
        self.add_to_known_changesets(cs)
        self.ordered_changesets.append(cs)
        self.ordered_changesets_set_cache.update([cs])
        self.open_changeset = None
        cs.set_unaccounted_changesets([])
        # clean out old dependencies, since this should be the only
        # one now
        self.dependencies = [cs]
        self.send_queue.append(cs)
        # randomly select if if this changeset should be a cache
        if random.random() < 0.1:
            cs.set_as_snapshot_cache(True)
            cs.set_snapshot_cache(copy.deepcopy(self.snapshot))
            cs.set_snapshot_cache_is_valid(True)
        return cs

    def receive_changesets(self, css):
        for cs in css:
            self.receive_changeset(cs)
        return True
        

    def receive_changeset(self, cs):
        """
        When a user is sent a new changeset from another editor, put
        it into place and rebuild state with that addition.
        """
        if not isinstance(cs, Changeset):
            cs = build_changeset_from_dict(cs, self)

        if self.knows_changeset(cs.get_id()):
            return False

        self.add_to_known_changesets(cs)

        if cs.get_id() in self.missing_changesets:
            self.missing_changesets.remove(cs.get_id())

        self.pending_new_changesets.append(cs)
        dep_ids = self.get_missing_dependency_ids(cs)
        self.missing_changesets.update(dep_ids)

        if self.HAS_EVENT_LOOP:
            return True

        was_inserted = self.pull_from_pending_list()
        return was_inserted


    def activate_changeset_in_document(self, cs):
        """
        Handles actually inserting the cs into the ordered changesets,
        resetting changesets which must do OT, performing OT, and
        reseting this document's dependency info.
        
        The given cs must a be one which 1) is not already in the ordered
        changesets, 2) has all needed info to be inserted into ordered
        changesets.
        """

        # this is the first time a changeset's ancestors can be
        # accuratly determined, so cache it if need be.
        if cs._is_ancestor_cache:
            cs.get_ancestors()
        
        index = self.insert_changeset_into_ordered_list(cs)
        self.update_unaccounted_changesets(cs, index=index)
        
        # remove document dependencies covered by this new changeset
        for parent in cs.get_parents():
            if parent in self.dependencies:
                self.dependencies.remove(parent)
        self.dependencies.append(cs)
        return index

        
    def pull_from_pending_list(self):
        """
        Go through the list of pending changesets and try again to
        incorporatet them into this document. As long as the list of
        pending changests shrinks, it loops through again.
        """
        self.close_changeset()
        # keep track of lowest index for start point for ot
        index = len(self.ordered_changesets)
        one_inserted = False
        l = -1 # flag for when looping is done
        while not l == len(self.pending_new_changesets):
            l = len(self.pending_new_changesets)
            for cs in iter(self.pending_new_changesets):
                if self.has_needed_dependencies(cs):
                    i = self.activate_changeset_in_document(cs)
                    index = min(i, index)
                    self.pending_new_changesets.remove(cs)
                    one_inserted = True
        if not one_inserted:
            return False

        self.ot(index-1)
        self.rebuild_snapshot()
        return True

        
    def receive_snapshot(self, m):
        """
        m is the dict coming straight from another user over
        the tubes.
        """
        self.root_changeset = build_changeset_from_dict(m['root'], self)
        deps = m['deps']
        new_css = []
        for dep in deps:
            new_cs = build_changeset_from_dict(dep, self)
            if new_cs.get_id() == self.root_changeset.get_id():
                new_cs = self.root_changeset
            new_css.append(new_cs)
            
        self.set_snapshot(m['snapshot'], new_css)
        if [self.root_changeset] == self.dependencies:
            self.ordered_changesets = [self.root_changeset]
            self.ordered_changesets_set_cache = set([self.root_changeset])


    def receive_history(self, m):
        for cs in m['history']:
            # build historical changeset
            hcs = build_changeset_from_dict(cs,self)
            if hcs.get_parents() == []:
                self.root_changeset = hcs
            self.add_to_known_changesets(hcs)
        self.relink_changesets()
        self.ordered_changesets = self.tree_to_list()
        self.ordered_changesets_set_cache = set(self.ordered_changesets)
        for i, cs in enumerate(self.ordered_changesets):
            self.update_unaccounted_changesets(cs, i)
            
    def relink_changesets(self):
        for cs in self.all_known_changesets.values():
            cs['obj'].relink_changesets(self.all_known_changesets)
            
    def add_to_known_changesets(self, cs):
        """
        Add a changeset to the dict of all known changesets, then link it
        up to its parents and children.
        """
        if self.knows_changeset(cs.get_id()):
            return
        self.all_known_changesets[cs.get_id()] = {'obj': cs, 'active':False }
        for p in cs.get_parents():
            if not isinstance(p, Changeset):
                p_obj = self.get_changeset_by_id(p)
                if p_obj:
                    p = p_obj
                    cs.relink_parent(p)
            if isinstance(p, Changeset):
                p.add_child(cs)
        

    def ot(self, start=0):
        """
        Perform opperational transformation on all changesets from
        start onwards.
        """
        i = max(start, 1)
        # any hazards past start point are not invalid.
        self.remove_old_hazards(i)

        # when a cs has one child, the child has one parent, and no
        # new hazards were produced, the child will have the same list
        # of hazards. Don't recalc.
        recalculate_hazards_for_cs = True
        hazards = []
        while i < len(self.ordered_changesets):
            cs = self.ordered_changesets[i]
            if recalculate_hazards_for_cs:
                hazards = self.get_hazards_for_cs(cs, i)
            new_hazards = cs.ot(hazards)
            if new_hazards:
                self.add_new_hazards(new_hazards)
                recalculate_hazards_for_cs = True
            elif len(cs.get_children()) == 1 and \
                 len(cs.get_children()[0].get_parents()) == 1:
                recalculate_hazards_for_cs = False
            else:
                recalculate_hazards_for_cs = True
            i += 1

    def add_new_hazards(self, new_hazards):
        ocs = {cs: i for i, cs in enumerate(self.ordered_changesets)}
        self.hazards.extend(new_hazards)
        self.hazards.sort(key=lambda h: h.get_conflict_op_index())
        self.hazards.sort(key=lambda h: ocs[h.conflict_cs])
        self.hazards.sort(key=lambda h: h.get_base_op_index())
        self.hazards.sort(key=lambda h: ocs[h.base_cs])

    def remove_old_hazards(self, index=0):
        css = set(self.ordered_changesets[index:])
        self.hazards = [h for h in self.hazards if not h.conflict_cs in css]

    def get_hazards_for_cs(self, cs, index=None):
        index = index if index else self.ordered_changesets.index(cs)
        css = set(self.ordered_changesets[index:])
        hazards = [h for h in self.hazards \
                   if not h.conflict_cs in css and not cs.has_ancestor(h.base_cs)]
        return hazards

    def has_needed_dependencies(self, cs):
        """
        A peer has sent the changeset cs, so this determines if this
        client has all the need dependencies before it can be applied.
        """
        cs.relink_changesets(self.all_known_changesets)
        if not cs.has_full_dependency_info():
            return False
        deps = cs.get_parents()
        for dep in deps:
            if not dep in self.ordered_changesets_set_cache:
                return False
        return True

    def rebuild_snapshot(self, index=0):
        """
        Start from an empty {} document and rebuild it from each op in
        each changeset.
        """
        while index > 0 and not self.ordered_changesets[index].has_valid_snapshot_cache():
            index -= 1
        if index == 0:
            self.snapshot ={}
        else:
            self.snapshot = self.ordered_changesets[index].get_snapshot_cache()
            index +=1
        while index < len(self.ordered_changesets):
            for op in self.ordered_changesets[index].get_ops():
                self.apply_op(op)
            if self.ordered_changesets[index].is_snapshot_cache():
                self.ordered_changesets[index].set_snapshot_cache(copy.deepcopy(self.snapshot))
                self.ordered_changesets[index].set_snapshot_cache_is_valid(True)
            index += 1

    def update_unaccounted_changesets(self, cs, index=None):
        """
        cs has just been inserted into the list. First find all
        unaccounted changesets which come before it. Then add this
        changeset to each subsequent changeset which needs it. (all?)
        """
        unaccounted_css = []
        deps = cs.get_parents()
        pos_of_cs = self.ordered_changesets.index(cs) if index == None else index
        i = pos_of_cs - 1
        while deps and i > 0:
            old_cs = self.ordered_changesets[i]
            if old_cs in deps:
                if len(deps) == 1:
                    # if this is the last dep, then cs (generally)
                    # shares it's unknown dependencies
                    rev_ucss = reversed(old_cs.get_unaccounted_changesets())
                    ucss = [ucs for ucs in rev_ucss if not cs.has_ancestor(ucs)]
                    unaccounted_css.extend(ucss)
                    break
                deps.remove(old_cs)
            elif not cs.has_ancestor(old_cs) and not old_cs in unaccounted_css:
                unaccounted_css.append(old_cs)
            i -= 1
        unaccounted_css.reverse()
        cs.set_unaccounted_changesets(unaccounted_css)

        # now add the given cs to all subsequent changesets which need it
        i = pos_of_cs + 1
        while i < len(self.ordered_changesets):
            future_cs = self.ordered_changesets[i]
            future_cs.add_to_unaccounted_changesets(cs,pos_of_cs, self.ordered_changesets)
            i += 1
        
    def insert_changeset_into_ordered_list(self, cs):
        """
        When there is just one new changeset to add, there is no need to
        build the whole tree. Just insert this one into place in the ordered
        list.
        """

        i = self.get_insertion_point_into_ordered_changesets(cs)
        self.ordered_changesets.insert(i, cs)
        self.ordered_changesets_set_cache.update([cs])
        return i

    def get_insertion_point_into_ordered_changesets(self, cs, ordered_list=None):
        if ordered_list == None:
            ordered_list = self.ordered_changesets
        
        # first get the most recent dependency
        deps = cs.get_parents()
        i = len(ordered_list) - 1
        while not ordered_list[i] in deps:
            i -= 1

        last_dep = ordered_list[i]

        i += 1        
        while i < len(ordered_list):
            if ordered_list[i].has_ancestor(cs):
                break
            if last_dep in ordered_list[i].get_parents():
                if cs.get_id() < ordered_list[i].get_id():
                    break
            elif not ordered_list[i].has_ancestor(last_dep):
                break
            i += 1
            
        return i

        

    def tree_to_list(self):
        """
        The CS objects point to parents and children in order to build the
        whole dependency tree. Take that tree and turn it into the
        correct ordered list.
        """
        cs = self.root_changeset
        tree_list = []
        tree_set_cache = set([])
        children = cs.get_children()
        divergence_queue = []
        insertion_point = 0
        loop_completed = False

        while True:
            tree_list.insert(insertion_point, cs)
            tree_set_cache.update([cs])
            insertion_point += 1
            children = cs.get_children()
            cs = children[0] if children else None
            if children:
                divergence_queue += children[1:]

            just_increment = True
            while self._cs_cannot_be_inserted(cs, tree_set_cache):
                just_increment = False
                if not divergence_queue:
                    loop_completed = True
                    break
                cs = divergence_queue.pop()

            if loop_completed:
                break
                
            if not just_increment or len(cs.get_parents()) > 1:
                insertion_point = self.get_insertion_point_into_ordered_changesets(cs, tree_list)
                children = cs.get_children()
                if children:
                    divergence_queue += children[1:]

        return tree_list

    def _cs_cannot_be_inserted(self, cs, tree_set_cache):
        return (cs == None or 
                set(cs.get_parents()) - tree_set_cache != set([]) or
                cs in tree_set_cache)

    def get_diff_opcode(self, old_state):
        """
        Accept an old snapshot and get the opcodes which turn it into the
        current snapshot.
        TODO: this is only set up for strings right now. 
        """
        new_state = self.get_snapshot()
        diff = difflib.SequenceMatcher(None, old_state, new_state)
        path = [] # just working with strings. path is always root
        opcodes = []
        for tag, i1, i2, j1, j2 in diff.get_opcodes():
            if tag == 'insert':
                txt = self.get_snapshot()[j1:j2]
                opcodes.append((tag, path, i1, txt))
            elif tag == 'delete':
                opcodes.append((tag, path, i1, (i2 - i1)))
            elif tag == 'replace':
                txt = self.get_snapshot()[j1:j2]
                opcodes.append(('replace', path, i1, (i2 - i1), txt))

        return opcodes
        

        
    # To determine if the path is valid in this document
    def contains_path(self, path):
        """ Checks if the given path is valid in this document's snapshot """
        node = self.snapshot
        for i in path:
            if isinstance(i, str):
               if not isinstance(node, dict):
                  return False
               if not i in node:
                   return False
            elif isinstance(i, int):
                if not isinstance(node, list):
                    return False
                if i >= len(node):
                    return False
            node = node[i]
        return True

    def get_node(self, path):
        node = self.snapshot
        if len(path) != 0:
            for i in path[:-1]:
                node = node[i]
        return node

    def get_value(self, path):
        if len(path) ==0:
            return self.snapshot
        return self.get_node(path)[path[-1]]

    def apply_op(self, op):
        if not self.contains_path(op.path):
            return "ERROR!"
        
        func_name = self.json_opperations[op.action]
        func = getattr(self, func_name)
        if len(op.path) == 0:
            self.snapshot = func(op)
        else:
            node = self.get_node(op.path)
            node[op.path[-1]] = func(op)

    # JSON Opperation - wholesale replacing value at a given path        
    def set_value(self, op):
        return op.val

    # JSON Opperation - Flip the value of the boolean at the given path
    def boolean_negation(self, op):
        cur = self.get_value(op.path)
        return False if cur else True

    # JSON Opperation - Add some constant value to the number at the given path
    def number_add(self, op):
        return self.get_value(op.path) + op.val

    # JSON Opperation - Insert characters into a string at the given
    # path, and at the given offset within that string.
    def string_insert(self, op):
        cur = self.get_value(op.t_path)
        return  cur[:op.t_offset] + op.t_val + cur[op.t_offset:]

    # JSON Opperation - Delete given number of characters from a
    # string at the given path, and at the given offset within that
    # string.
    def string_delete(self, op):
        cur = self.get_value(op.t_path)
        return cur[:op.t_offset] + cur[op.t_offset + op.t_val:]
        
    
    def array_insert(self, op):
        cur = self.get_value(op.path)
        r = cur[:op.offset]
        r.append(op.val)
        r.extend(cur[op.offset:])
        return r

    def array_delete(self, op):
        cur = self.get_value(op.path)
        r = cur[:op.offset]
        r.extend(cur[op.offset + op.val:])
        return r

    def array_move(self, op):
        cur = self.get_value(op.path)
        item = cur.pop(op.offset)
        r = cur[:op.val]
        r.append(item)
        r.extend(cur[op.val:])
        return r

    def object_insert(self, op):
        cur = self.get_value(op.path)
        cur[op.val['key']]  = op.val['val']
        return cur

    def object_delete(self, op):
        cur = self.get_value(op.path)
        cur.pop(op.offset)
        return cur

        
    json_opperations = {
        'set': 'set_value',
        'bn' : 'boolean_negation',
        'na' : 'number_add',
        'si' : 'string_insert',
        'sd' : 'string_delete',
        'ai' : 'array_insert',
        'ad' : 'array_delete',
        'am' : 'array_move',
        'oi' : 'object_insert',
        'od' : 'object_delete'
    }

