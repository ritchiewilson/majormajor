import json
import random
import string
from changeset import Changeset
from op import Op

class Document:
    snapshot = {}
    deps = []
    dep_hashes = []
    open_changeset = None
    author = 'Ritchie'

    # Each document needs an ID so that changesets can be associated
    # with it. If one is not supplied, make a random 5 character ID at
    # start
    def __init__(self, id_ = None):
        if id_ == None:
            id_ = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(5))
        self.id_ = id_
        

    def add_op(self, op):
        """
        For when this user (not remote collaborators) add an
        opperation. If there is no open changeset, one will be opened
        with correct dependencies and the given op. If a changeset is
        already started, the given op is just added on. The given op
        is then immediatly applied to this Document.
        """
        if self.open_changeset == None:
            dep_list = []
            for dep in self.deps:
                dep_list.append(dep['id'])
            self.open_changeset = Changeset(self.id_, self.author, dep_list)
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
        self.deps.append({'id':self.open_changeset.get_id(),\
                          'changeset': self.open_changeset.to_dict()})
        self.dep_hashes.append({'id':self.open_changeset.get_id(), \
                                'deps': self.open_changeset.deps})
        self.open_changeset = None

    # When a user is sent a new changeset from another editor, put it
    # into place and rebuild state with that addition. Because the
    # list of dependencies should already be sorted, this is a simple
    # insertion sort applied only to the new item.
    def recieve_changeset(self, cs):
        # TODO first check that this doc has all needed dependencies

        # insert sort this changeset back into place
        i = len(self.deps)
        while i > 0:
            if len(cs.deps) > len(self.deps[i-1]['changeset']['deps']):
                break
            if len(cs.deps) == len(self.deps[i-1]['changeset']['deps']):
                if cs.get_id() > self.deps[i-1]['id']:
                    break
            i -= 1
                
        self.deps.insert(i, {'id': cs.get_id(), 'changeset':cs.to_dict()})
        self.dep_hashes.insert(i, {'id': cs.get_id(), 'deps':cs.deps})
        self.rebuild_snapshot()

    # Start from an empty {} document and rebuild it from op in each changeset
    def rebuild_snapshot(self):
        self.snapshot = {}
        for dep in self.deps:
            for op in dep['changeset']['ops']:
                tmpOp = Op(op['action'], op['path'], val=op['val'])
                self.apply_op(tmpOp)

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
        cur = self.get_value(op.path)
        return  cur[:op.offset] + op.val + cur[op.offset:]

    # JSON Opperation - Delete given number of characters from a
    # string at the given path, and at the given offset within that
    # string.
    def string_delete(self, op):
        cur = self.get_value(op.path)
        return cur[:op.offset] + cur[op.offset + op.val:]
        
    
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

d = Document()
d.add_op(Op('oi', [], val={'key':'a','val':1}))
d.close_changeset()
d.add_op(Op('set', ['a'], val={'c':3}))
d.close_changeset()
d.add_op(Op('oi', [], val={'key':'b','val':2}))
d.close_changeset()


init_hash = d.dep_hashes[0]['id']
second_hash = d.dep_hashes[1]['id']
d_id = d.id_
cs1 = Changeset(d_id, 'NOT RITCHIE', [init_hash, second_hash])
cs1.add_op(Op('oi', ['a'], val={'key':'d','val':4}))
d.recieve_changeset(cs1)

for dep in d.deps:
    print(dep)
print(d.snapshot)
for dep in d.dep_hashes:
    print(dep)
print (d.snapshot)
