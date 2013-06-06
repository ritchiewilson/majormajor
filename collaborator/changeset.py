import hashlib
import json
import random

class Changeset:
    def __init__(self, doc_id, user, dependencies):
        self.doc_id = doc_id
        self.user = user
        self.id_ = None
        self.ops = []
        self.preceding_changesets = None
        self.dependencies = dependencies
        self.children = []
        self.parents = dependencies[:]
        self._is_snapshot_cache = False
        self.snapshot_cache = None
        self.set_dependencies(dependencies)
        self._is_ancestor_cache = False
        self.set_as_ancestor_cache()
        
    def is_empty(self):
        return len(self.ops) == 0
    
    def set_dependencies(self, deps):
        """
        Split dependencies into two lists. One which holds dependencies
        when the full cs object is known. The other is where we put
        dependencies for which only the id is known.
        """
        self.dependencies_with_full_info = []
        self.dependencies_with_id_only = []
        for dep in deps:
            if isinstance(dep, Changeset):
                self.dependencies_with_full_info.append(dep)
            else:
                self.dependencies_with_id_only.append(dep)

    def get_dependencies_with_id_only(self):
        return self.dependencies_with_id_only[:]

    def get_dependencies_with_full_info(self):
        return self.dependencies_with_full_info[:]

    def get_parents(self):
        return self.parents[:]

    def get_children(self):
        return self.children[:]

    def add_child(self, cs):
        if cs not in self.children:
            self.children.append(cs)
        id_list = [child.get_id() for child in self.children]
        id_list.sort()
        ret = []
        for _id in id_list:
            for child in self.children:
                if child.get_id() == _id:
                    ret.append(child)
                    break
        self.children = ret


    def has_children(self):
        return not self.children == []
    
    def is_snapshot_cache(self):
        return self._is_snapshot_cache

    def set_as_snapshot_cache(self, boolean):
        self._is_snapshot_cache = boolean

    def set_as_ancestor_cache(self, boolean=None):
        # if not specified, this changeset should be randomly assigned
        # to be a cache. If it has multiple parents it should be far
        # more likely to be a cache, in order to best reduce
        # complexity. If it has one parent, low chance of being a
        # cache
        if boolean == None:
            x = random.random()
            boolean = x < 0.6 if len(self.get_parents()) > 1 else x < 0.07
        self.ancestor_cache = None
        self._is_ancestor_cache = boolean
        if boolean:
            self.ancestor_cache = self.get_ancestors()
        
    def set_snapshot_cache(self, snapshot):
        self.snapshot_cache = snapshot

    def get_snapshot_cache(self):
        return self.snapshot_cache

    def set_snapshot_cache_is_valid(self, boolean):
        self.snapshot_cache_is_valid = boolean

    def has_valid_snapshot_cache(self):
        return self._is_snapshot_cache and self.snapshot_cache_is_valid

    def get_ancestors(self):
        if self.parents == []:
            return set([])
        if self._is_ancestor_cache and self.ancestor_cache != None:
            return self.ancestor_cache
        ancestors = set(self.parents)
        for parent in self.parents:
            ancestors.update(parent.get_ancestors())
        if self._is_ancestor_cache:
            self.ancestor_cache = ancestors
        return ancestors
        
    def has_ancestor(self, ancestor):
        if len(self.parents) == 0:
            return False
        if ancestor in self.parents:
            return True
        if self._is_ancestor_cache and self.ancestor_cache != None:
            return ancestor in self.get_ancestors()
        for parent in self.parents:
            if parent.has_ancestor(ancestor):
                return True
        return False

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
        for dep in self.parents:
            if isinstance(dep, Changeset):
                dep_ids.append(dep.get_id())
            else:
                dep_ids.append(dep)
        dep_ids.sort()
        return dep_ids

    def get_ops(self):
        return self.ops[:]

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
        return self.dependencies[:]
            
    def set_id(self, id_):
        """
        Set the id of this document. Called when building a remote
        changset and the id is already known.
        """
        self.id_ = id_
        return True
    
    def add_op(self, op):
        """
        Add an opperation to this changeset. Changesets should never
        change once they get an id, so if an opperation is added to
        closed changeset, throw an error.
        """
        if self.id_:
            raise Exception("Can't add op. Changeset is already closed.")
        if op in self.ops:
            raise Exception("Can't add same op object multiple times.")
        self.ops.append(op)
        return True

    def relink_changesets(self, all_known_changesets):
        """
        """
        i = 0
        while i < len(self.parents):
            parent = self.parents[i]
            if not isinstance(parent, Changeset):
                if parent in all_known_changesets:
                    self.parents.remove(parent)
                    self.parents.append(all_known_changesets[parent])
            else:
                parent = parent.get_id()
            all_known_changesets[parent].add_child(self)
            i += 1

    def get_dependency_chain(self):
        chain = set([])
        still_to_check_queue = self.get_dependencies_with_full_info()
        while len(still_to_check_queue) > 0:
            el = still_to_check_queue.pop(0)
            if el in chain:
                continue
            chain.update([el])
            still_to_check_queue += el.get_dependencies_with_full_info()
        return chain
        
    def set_unaccounted_changesets(self, css):
        """
        Sometimes the changesets could be calculated elsewhere. Just
        stick it in.
        """
        self.preceding_changesets = css
    
    def get_unaccounted_changesets(self):
        """
        List of all the changes that happened before this changeset
        but were not known or accounted for. Kept in ascending order.
        """
        if self.preceding_changesets == None:
            raise Exception("Preceding Changesets not yet known")
        return self.preceding_changesets[:]

    def find_unaccounted_changesets(self, prev_css):
        # when this has no dependencies, the unacounted changesets are
        # all the previous changesets with no dependenies.
        # Constant time
        if len(self.parents) == 0:
            self.preceding_changesets = prev_css[:]
            return self.preceding_changesets

        i = len(prev_css)-1 # index to prev_css to later look through
        # With one dependency, linear time at worst. Should be closer
        # to constant time
        if len(self.parents) == 1:
            dep = self.parents[0]
            self.preceding_changesets = dep.get_unaccounted_changesets()
            while not prev_css[i] == dep:
                i -= 1
        # with multiple dependencies, quadratic time? Still not good
        else:
            # get the unique list of all unacounted changsets from
            # dependencies
            p = set([])
            for dep in self.parents:
                #TODO HERE! WRONG! Can't just add up the unaccounted
                #changesets from deps because a cs unnaccounted in
                # one line could be accounted for in the another
                p.update(dep.get_unaccounted_changesets())
            chain = self.get_dependency_chain()
            p -= chain
            p = list(p)
            # sort those changesets into correct order
            self.preceding_changesets = []
            for prev_cs in prev_css:
                if len(p) == 1:
                    self.preceding_changesets.append(prev_cs)
                    while not prev_css[i] == prev_cs:
                        i -=1
                    break
                if prev_cs in p:
                    self.preceding_changesets.append(prev_cs)
                    p.remove(prev_cs)

        # Here all cached unknown changesets are in place in
        # self.preceding_changesets and i is set to the index in
        # prev_css of the most recent dependency to this changeset.
        self.preceding_changesets += prev_css[i+1:]
        return self.preceding_changesets
        
    def transform_from_preceding_changesets(self, prev_css):
        """
        pcs is a list of all known changesets that come before this
        one. Figure out which ones in that list are not a dependency
        of this one. If it is not a dependency of this one, the
        operations in this changeset need to go through opperational
        transformation for it.
        """
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
