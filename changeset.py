import hashlib
import json

class Changeset:
    id_ = None
    ops = []
    preceding_changesets = []
    def __init__(self, doc_id, author, deps):
        self.doc_id = doc_id
        self.author = author
        self.deps = deps[:]
        self.ops = []

    def add_op(self, op):
        if self.id_:
            return False
        self.ops.append(op)
        return True

    def add_preceding_changesets(self, pcs):
        self.preceding_changesets = []

        # figure out all the actions which have come before and are
        # not a dependency of this changeset.
        for pc in pcs:
            found = False
            for dep in self.deps:
                if pc.get_id() == dep.get_id():
                    found = True
            if not found:
                self.preceding_changesets.append(pc)

        # those 'preceding_changesets' need to be used to transform
        # this changeset's operations.
        for pc in self.preceding_changesets:
            for op in self.ops:
                op.ot(pc)


    def to_json(self):
        op_list = []
        for op in self.ops:
            op_list.append(op.to_jsonable())
        dep = None
        if len(self.deps) > 0:
            dep = self.deps[0].get_id()
        j = [{'doc_id': self.doc_id}, {'author':self.author},\
             {'dep':dep}, {'ops': op_list}]
        return json.dumps(j)

    def get_id(self):
        if self.id_ == None:
            h = hashlib.sha1()
            h.update(self.to_json().encode('utf-8'))
            self.id_ = h.hexdigest()
        return self.id_
