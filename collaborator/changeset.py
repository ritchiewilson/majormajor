import hashlib
import json

class Changeset:
    def __init__(self, doc_id, user, dependencies):
        self.doc_id = doc_id
        self.user = user
        self.id_ = None
        self.ops = []
        self.preceding_changesets = []
        self.dependencies = dependencies
        self.dependency_chain = None

    def is_empty(self):
        return len(self.ops) == 0

    def has_full_dependency_info(self):
        """
        Determine if each dependency has all it's info, or if any of the
        dependencies are just an ID.
        """
        for dep in self.dependencies:
            if not isinstance(dep, Changeset):
                return False
        return True

    def get_dependency_ids(self):
        dep_ids = []
        for dep in self.dependencies:
            if isinstance(dep, Changeset):
                dep_ids.append(dep.get_id())
            else:
                dep_ids.append(dep)
        return dep_ids

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

    def get_dependencies(self):
        """
        Return the Changeset object which is this changeset's most
        recent dependency.
        """
        return self.dependencies

    def get_dependency_chain(self):
        """
        Makes no garuntees for order.
        """
        if self.dependency_chain != None:
            return self.dependency_chain
        dep_chain = self.get_dependencies()
        i=0
        while i < len(dep_chain):
            for dep in dep_chain[i].get_dependencies():
                if not dep in dep_chain:
                    dep_chain.append(dep)
            i += 1
        self.dependency_chain = list(set(dep_chain))
        return self.dependency_chain
            
    def get_unaccounted_changesets(self):
        """
        List of all the changes that happened before this changeset
        but were not known or accounted for. Kept in ascending order.
        """
        return self.preceding_changesets
    
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

    def relink_changeset(self, dep):
        i = 0
        while i < len(self.dependencies):
            if self.dependencies[i] == dep.get_id():
                self.dependencies[i] = dep
                break
            i += 1

    def transform_from_preceding_changesets(self, prev_css):
        """
        pcs is a list of all known changesets that come before this
        one. Figure out which ones in that list are not a dependency
        of this one. If it is not a dependency of this one, the
        operations in this changeset need to go through opperational
        transformation for it.
        """
        self.preceding_changesets = []
        print "GETTING CHAIN"
        chain = self.get_dependency_chain()
        self.preceding_changesets = []
        print "Setting previous changesets"
        for prev_cs in prev_css:
            if not prev_cs in chain:
                self.preceding_changesets.append(prev_cs)
        print "OPPERATIONAL TRANSFORMATION"
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
        j = [{'doc_id': self.doc_id}, {'user':self.user},\
             {'dep':self.get_dependency_ids()}, {'ops': op_list}]
        return j

   
    def to_dict(self):
        """
        Build less verbose dict for just sending data. Not used for
        building id.
        """
        d = {'doc_id': self.doc_id,
             'user': self.user,
             'dep_ids': self.get_dependency_ids(),
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
