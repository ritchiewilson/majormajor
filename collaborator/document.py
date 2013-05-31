import json
import random
import string
import uuid
import copy
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
        # some initial values
        #self.changesets = []
        self.ordered_changesets = []
        self.all_known_changesets = {}
        self.missing_changesets = []
        self.send_queue = []
        self.pending_new_changesets = []
        self.pending_historical_changesets = []
        self.open_changeset = None
        self.snapshot = {}
        self.root_changeset = None
        self.dependencies = []
        # set initial snapshot if called upon
        if not snapshot == None:
            self.set_initial_snapshot(snapshot)
        self.dependencies = [self.root_changeset]
        

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
        
    def get_missing_dependency_ids(self, new_cs):
        missing_dep_ids = []
        for dep in new_cs.get_dependencies():
            if not isinstance(dep, Changeset):
                missing_dep_ids.append(dep)
        return missing_dep_ids
                
    def get_changeset_by_id(self, cs_id):
        if cs_id in self.all_known_changesets:
            return self.all_known_changesets[cs_id]
        return None

    def get_open_changeset(self):
        return self.open_changeset

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

    def add_to_pending_new_changesets(self, cs):
        self.pending_new_changesets.append(cs)

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

        if self.open_changeset == None or self.open_changeset.is_empty():
            return

        cs = self.open_changeset
        self.add_to_known_changesets(cs)
        self.ordered_changesets.append(cs)
        self.open_changeset = None
        cs.set_unaccounted_changesets([])
        # clean out old dependencies, since this should be the only
        # one now
        self.dependencies = [cs]
        # randomly select if if this changeset should be a cache
        if random.random() < 0.1:
            cs.set_as_snapshot_cache(True)
            cs.set_snapshot_cache(copy.deepcopy(self.snapshot))
            cs.set_snapshot_cache_is_valid(True)
        return cs


    def receive_changeset(self, cs):
        """
        When a user is sent a new changeset from another editor, put
        it into place and rebuild state with that addition.
        """
        if not isinstance(cs, Changeset):
            cs = build_changeset_from_dict(cs['payload'], self)
        if not self.has_needed_dependencies(cs):
            self.pending_new_changesets.append(cs)
            dep_ids = self.get_missing_dependency_ids(cs)
            self.missing_changesets += dep_ids
            return False
        # close the currently open changeset and get it ready for sending
        current_cs = self.close_changeset()
        if current_cs:
            # randomly select if if this changeset should be a cache
            if random.random() < 0.1:
                cs.set_as_snapshot_cache(True)
                cs.set_snapshot_cache_is_valid(False)
                cs.set_as_ancestor_cache(True)
            self.send_queue.append(current_cs)
            
        self.add_to_known_changesets(cs)
        from datetime import datetime
        d = datetime.now()

        self.insert_changeset_into_ordered_list(cs)
        diff = datetime.now() - d
        #print diff.microseconds
        #print "Number of changesets: ", len(self.ordered_changesets)
        #print "number of all known: ", len(self.all_known_changesets.keys())

        for parent in cs.get_parents():
            if parent in self.dependencies:
                self.dependencies.remove(parent)
        self.dependencies.append(cs)
        
        #self.ot()
        self.rebuild_snapshot()
        
        # randomly select if if this changeset should be a cache
        if random.random() < 0.1:
            cs.set_as_snapshot_cache(True)
            cs.set_snapshot_cache_is_valid(False)
            cs.set_as_ancestor_cache(True)
        
        return True

    def receive_snapshot(self, m):
        """
        m is the dict coming straight from another user over
        the tubes.
        """
        deps = m['deps']
        new_css = []
        for dep in deps:
            new_css.append(build_changeset_from_dict(dep, self))
        self.set_snapshot(m['snapshot'], new_css)


    def receive_history(self, m):
        for cs in m['history']:
            # build historical changeset
            hcs = build_changeset_from_dict(cs,self)
            if hcs.get_dependencies() == []:
                self.root_changeset = hcs
            self.add_to_known_changesets(hcs)
        self.relink_changesets()
        self.ordered_changesets = self.tree_to_list()
        for cs in self.ordered_changesets:
            print cs.get_id()
            print cs.get_parents()
        prev = []
        for cs in self.ordered_changesets:
            cs.find_unaccounted_changesets(prev)
            prev.append(cs)
            
    def relink_changesets(self):
        for cs in self.all_known_changesets.values():
            cs.relink_changesets(self.all_known_changesets)
            
    def add_to_known_changesets(self, cs):
        self.all_known_changesets[cs.get_id()] = cs
        for p in cs.get_parents():
            if not isinstance(p, Changeset):
                p_obj = self.get_changeset_by_id(p)
                if p_obj:
                    p = p_obj
                    cs.relink_parent(p)
            if isinstance(p, Changeset):
                p.add_child(cs)
        

    def ot(self, start):
        """
        Perform opperational transformation on all changesets from
        start onwards.
        """
        prev = self.ordered_changesets[:start]
        new_cs = self.ordered_changesets[start]
        new_cs.find_unaccounted_changesets(prev)
        new_cs.transform_from_preceding_changesets(prev)

        prev.append(new_cs)
        to_transfrom = self.ordered_changesets[start+1:]
        for cs in to_transfrom:
            cs.find_unaccounted_changesets(prev)
            cs.transform_from_preceding_changesets(prev)
            prev.append(cs)

        
    def has_needed_dependencies(self, cs):
        """
        A peer has sent the changeset cs, so this determines if this
        client has all the need dependencies before it can be applied.
        """
        deps = cs.get_parents()
        for dep in deps:
            if not dep.get_id() in self.all_known_changesets:
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

    def insert_changeset_into_ordered_list(self, cs):
        # if this changests dependencies are the docuemtns
        # dependencies, jsut stick it on the end
        if set(cs.get_parents()) == set(self.dependencies):
            self.ordered_changesets.append(cs)
            return

        # if parent and child only point to each other, there's no
        # reason to split them up, so just stick it in.
        parents = cs.get_parents()
        if len(parents) == 1 and parents[0].get_children() == [cs]:
            insertion_point = self.ordered_changesets.index(parents[0]) + 1
            self.ordered_changesets.insert(insertion_point, cs)
            return

        i = self.get_insertion_point_into_ordered_changesets(cs)
        self.ordered_changesets.insert(i, cs)

    def get_insertion_point_into_ordered_changesets(self, cs, ordered_list=None):
        if ordered_list == None:
            ordered_list = self.ordered_changesets
        
        # first get the most recent dependency
        deps = cs.get_parents()
        i = len(ordered_list) - 1
        while not ordered_list[i] in deps:
            i -= 1

        # if this is the end of the list, just append
        if i == len(ordered_list) - 1:
            return i + 1

        last_dep = ordered_list[i]

        i += 1
        if not last_dep in ordered_list[i].get_parents():
            return i
        
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

