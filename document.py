import json
import random
import string
import uuid
from changeset import Changeset
from op import Op

class Document:
    snapshot = {}
    changesets = [] # all changesets from all users. sorted
    pending_changesets = []
    open_changeset = None
    changeset_stamp = 0

    # Each document needs an ID so that changesets can be associated
    # with it. If one is not supplied, make a random 5 character ID at
    # start
    def __init__(self, id_ = None, user=None):
        if id_ == None:
            id_ = ''.join(random.choice(string.ascii_letters + string.digits)
                          for x in range(5))
        self.id_ = id_
        if user == None:
            user = str(uuid.uuid4())
        self.user = user
        

    def get_id(self):
        return self.id_

    def get_user(self):
        return self.user

    def get_last_changeset(self):
        return self.changesets[-1] if self.changesets else None

    def get_changeset_by_id(self, cs_id):
        deps = None
        for cs in self.changesets:
            if cs.get_id() == cs_id:
                return cs
        return None

    def get_snapshot(self):
        return self.snapshot

    def set_snapshot(self, snapshot, deps=None):
        self.snapshot = snapshot
        
    def add_op(self, op):
        """
        For when this user (not remote collaborators) add an
        opperation. If there is no open changeset, one will be opened
        with correct dependencies and the given op. If a changeset is
        already started, the given op is just added on. The given op
        is then immediatly applied to this Document.
        """
        if self.open_changeset == None:
            self.open_changeset = Changeset(self.id_, self.user, self.changesets)
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

        # insert sort this changeset back into place
        i = len(self.changesets)
        while i > 0:
            if len(cs.deps) > len(self.changesets[i-1].deps):
                break
            if len(cs.deps) == len(self.changesets[i-1].deps):
                if cs.get_id() > self.changesets[i-1].get_id():
                    break
            i -= 1

        self.changesets.insert(i, cs)
        self.ot(i)
        self.rebuild_snapshot()
        return True


    def ot(self, start=0):
        """
        Perform opperational transformation on all changesets from
        start onwards.
        """
        prev = self.changesets[:start]
        to_transfrom = self.changesets[start:]
        for cs in to_transfrom:
            cs.transform_from_preceding_changesets(prev)
            prev.append(cs)
        
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

