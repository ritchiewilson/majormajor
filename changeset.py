import hashlib
import json

class Changeset:
    id_ = None
    ops = []
    preceding_changesets = []
    def __init__(self, doc_id, user, deps):
        self.doc_id = doc_id
        self.user = user
        self.deps = deps[:]
        self.ops = []

    def get_doc_id(self):
        """
        Return the id of the document this applies to.
        """
        return self.doc_id

    def get_user(self):
        """
        Get the user who created this changeset.
        """
        return self.user

    def get_deps(self):
        """
        Return the full list of dependencies for this changeset.
        """
        return self.deps

    def set_id(self, id_):
        """
        Set the id of this document. Called when building a remote
        changset and the id is already known.
        """
        self.id_ = id_
    
    def add_op(self, op):
        """
        Add an opperation to this changeset. Changesets should never
        change once they get an id, so if an opperation is added to
        closed changeset, throw an error.
        """
        if self.id_:
            raise Exception("Can't add op. Changeset is already closed.")
            return False
        self.ops.append(op)
        return True

    def transform_from_preceding_changesets(self, pcs):
        """
        pcs is a list of all known changesets that come before this
        one. Figure out which ones in that list are not a dependency
        of this one. If it is not a dependency of this one, the
        operations in this changeset need to go through opperational
        transformation for it.
        """
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

    def to_jsonable(self):
        """
        Build this changeset into a jsonable form. Instead of normal
        dicts, they are lists of key/value pairs so that order is
        preserved. The resulting json is what's used to hash and id
        this changeset, so the order must be preserved.
        """
        op_list = []
        for op in self.ops:
            op_list.append(op.to_jsonable())
        dep = None
        if len(self.deps) > 0:
            dep = self.deps[-1].get_id()
        j = [{'doc_id': self.doc_id}, {'user':self.user},\
             {'dep':dep}, {'ops': op_list}]
        return j

   
    def to_dict(self):
        """
        Build less verbose dict for just sending data. Not used for
        building id.
        """
        d = {'doc_id': self.doc_id,
             'user': self.user,
             'dep': self.deps[-1].get_id() if len(self.deps) > 0 else None,
             'ops': [op.to_dict() for op in self.ops]}
        return d
        
    def get_id(self):
        """
        Creates an id by building a specific json representation of
        this changeset, then getting the sha1 hash. If this has
        already been done, the id_ is cached so just return it.
        """
        if self.id_ == None:
            h = hashlib.sha1()
            j = json.dumps(self.to_jsonable())
            h.update(j.encode('utf-8'))
            self.id_ = h.hexdigest()
        return self.id_

    def __str__(self):
        """
        Helpful for when building messages to send to collaborators.
        """
        return self.get_id()
