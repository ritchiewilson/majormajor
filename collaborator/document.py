import json
import random
import string
import uuid
from changeset import Changeset
from op import Op

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
        self.changesets = []
        self.pending_changesets = []
        self.open_changeset = None
        self.snapshot = {}
        # set initial snapshot if called upon
        if not snapshot == None:
            self.set_initial_snapshot(snapshot)
        

    def get_id(self):
        return self.id_

    def get_user(self):
        return self.user

    def get_last_changeset(self):
        return self.changesets[-1] if self.changesets else None

    def get_dependencies(self):
        """
        Returns a list of the dependencies that make up the the current
        document. Usually this is a list of with just the most recent
        changeset. There can be multiple changesets if they each
        depend on the same changeset but do not know about each other.
        """
        dep_heads = []
        i = 0
        while i < len(self.changesets):
            j = i+1
            found = False
            while j < len(self.changesets):
                if self.changesets[i] in self.changesets[j].get_dependencies():
                    found = True
                    break
                j += 1
            if not found:
                dep_heads.append(self.changesets[i])
            i += 1
        return dep_heads

    def get_changeset_by_id(self, cs_id):
        for cs in self.changesets:
            if cs.get_id() == cs_id:
                return cs
        for cs in self.pending_changesets:
            if cs.get_id() == cs_id:
                return cs
        return None

    def get_open_changeset(self):
        return self.open_changeset

    def get_changesets_in_ranges(self, start_ids, end_ids):
        cs_in_range = []            
        start_reached = False if start_ids else True
        for cs in self.changesets:
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

    def set_initial_snapshot(self, s):
        """
        Can stick in boilerplate snapshot for doc. turns snapshot into an
        opperation.
        TODO - throw exception if doc is not new
        """
        op = Op('set', [], val=s)
        self.add_local_op(op)
        self.close_changeset()
        

    def set_snapshot(self, snapshot, deps=None):
        """
        Reset the snapshot of this documnet. Also needs to take the
        dependency that defines this snapshot. Since the local user
        will be working on from this point, this dependency takes over
        and all previously known changesets are put in the pending
        list until they can be sorted back in.
        """
        self.pending_changesets += self.changesets
        self.snapshot = snapshot
        self.changesets = deps

    def relink_changesets(self, css):
        """
        UGLY. From a list of changesets, css, go through each one and
        link up thier dependencies to changeset objects if need be.
        """
        for cs in css:
            if not cs.has_full_dependency_info():
                for dep in cs.get_dependencies():
                    if not isinstance(dep, Changeset):
                        dep = self.get_changeset_by_id(dep)
                        if dep: cs.relink_changeset(dep)
        
    def knows_changeset(self, cd_id):
        for cs in self.changesets:
            if cd_id == cs.get_id(): return True
        return False

    def insert_historical_changeset(self, cs):
        for dep in cs.get_dependencies():
            if not dep in self.changesets:
                self.pending_changesets.append(cs)
                return -1
            
        i =self.insert_changeset_into_changsets(cs)
        return i # return index of where it was stuck

        
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

        self.changesets.append(self.open_changeset)
        self.open_changeset = None
        self.changesets[-1].get_id()
        return self.changesets[-1]


    def recieve_changeset(self, cs):
        """
        When a user is sent a new changeset from another editor, put
        it into place and rebuild state with that addition. Because
        the list of dependencies should already be sorted, this is a
        simple insertion sort applied only to the new item.
        """
        if not self.has_needed_deps(cs):
            print("ERROR")
            self.pending_changesets.append(cs)
            return False

        i = self.insert_changeset_into_changsets(cs)
        self.ot(i)
        self.rebuild_snapshot()
        return True

    def insert_changeset_into_changsets(self, cs):
        """
        Also Return the index for where the changeset was put
        """
        # insert sort this changeset back into place
        dep_ids = cs.get_dependency_ids()
        i = len(self.changesets)
        # move backwards through list until it finds it's dependency
        while i > 0:
            if self.changesets[i-1].get_id() in dep_ids:
                break
            i -= 1

        # Move forward through list if multiple changesets have the
        # same dependency
        while i < len(self.changesets) and \
              dep_ids == self.changesets[i].get_dependency_ids() and \
              cs.get_id() > self.changesets[i].get_id():
            i += 1
        
        self.changesets.insert(i, cs)
        return i

    def ot(self, start):
        """
        Perform opperational transformation on all changesets from
        start onwards.
        """
        prev = self.changesets[:start]
        new_cs = self.changesets[start]
        new_cs.transform_from_preceding_changesets(prev)

        prev.append(new_cs)
        to_transfrom = self.changesets[start+1:]
        for cs in to_transfrom:
            cs.transform_from_preceding_changesets(prev)

        
    def has_needed_deps(self, cs):
        """
        A peer has sent the changeset cs, so this determines if this
        client has all the need dependencies before it can be applied.
        """
        return True
            

    def rebuild_snapshot(self):
        """
        Start from an empty {} document and rebuild it from each op in
        each changeset.
        """
        self.snapshot = {}
        for cs in self.changesets:
            cs.get_user()
            for op in cs.ops:
                self.apply_op(op)

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

