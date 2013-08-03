
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
        self._has_full_dependency_info = False
        self.set_as_snapshot_cache()
        self._is_ancestor_cache = False
        self.set_as_ancestor_cache()

    def is_empty(self):
        return len(self.ops) == 0
    
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

    def set_as_snapshot_cache(self, boolean=None):
        # if not specified, this changeset should be randomly assigned
        # to be a snapshot cache.
        if boolean == None:
            boolean = random.random() < 0.01
        self._is_snapshot_cache = boolean
        if boolean:
            self.snapshot_cache_is_valid = False

    def set_as_ancestor_cache(self, boolean=None):
        # if not specified, this changeset should be randomly assigned
        # to be a cache. If it has multiple parents it should be far
        # more likely to be a cache, in order to best reduce
        # complexity. If it has one parent, low chance of being a
        # cache
        if boolean == None:
            x = random.random()
            boolean = True if len(self.get_parents()) > 1 else x < 0.1
        self._is_ancestor_cache = boolean
        if boolean:
            self._has_valid_ancestor_cache = False
            self.ancestor_cache = None
        
    def set_snapshot_cache(self, snapshot):
        self.snapshot_cache = snapshot

    def get_snapshot_cache(self):
        return self.snapshot_cache

    def set_snapshot_cache_is_valid(self, boolean=True):
        self.snapshot_cache_is_valid = boolean

    def has_valid_snapshot_cache(self):
        return self._is_snapshot_cache and self.snapshot_cache_is_valid

    def get_ancestors(self):
        """
        Recursively go through all parents to the document root to return
        a set of all ancestors. If this changeset is an ancestor cache,
        the set is saved.
        """
        if not self.has_full_dependency_info():
            raise Exception("Cannot get ancestor list without full dependency info.")

        # just return the cache if able
        if self._is_ancestor_cache and self._has_valid_ancestor_cache:
            return self.ancestor_cache

        # otherwise, recursively find all ancestors
        ancestors = set(self.parents)
        for parent in self.parents:
            ancestors.update(parent.get_ancestors())

        # make sure this list is full and accurate before cacheing it
        if self._is_ancestor_cache:
            self._has_valid_ancestor_cache = True
            self.ancestor_cache = ancestors
        return ancestors
        
    def has_ancestor(self, ancestor):
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
        if self._has_full_dependency_info:
            return True
        for dep in self.parents:
            if not isinstance(dep, Changeset):
                return False
        self._has_full_dependency_info = True
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
        op.set_changeset(self)
        self.ops.append(op)
        return True

    def relink_changesets(self, all_known_changesets):
        """
        From the dictionary of all_known_changesets, relink this
        changesets parents where able, and make this a child of it's
        parents.

        The given all_known_changesets is a dict, where keys are cs id
        strings, and values are {'obj':<cs object>, 'active':boolean}
        """
        for parent in iter(self.parents):
            if not isinstance(parent, Changeset):
                if parent in all_known_changesets:
                    self.parents.remove(parent)
                    self.parents.append(all_known_changesets[parent]['obj'])
            else:
                parent = parent.get_id()
            if parent in all_known_changesets:
                all_known_changesets[parent]['obj'].add_child(self)

                
    def relink_parent(self, cs):
        """
        Remove apropraite id string from parents list and replace it
        with parent object.
        """
        for parent in iter(self.parents):
            if cs.get_id() == parent:
                self.parents.append(cs)
                self.parents.remove(parent)
                break

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

    def add_to_unaccounted_changesets(self, cs, index, ordered_changesets):
        """
        This changeset keeps a list of changesets which come before it in
        order, but it did not know about. The given cs is the
        changeset which was just inserted into the documents
        ordered_changesets, and for cnvenience, index is where it was
        inserted. ordered_changeset is the doc's ordered_changest.

        Determine where the given cs should go in this Changeset's
        ordered list of unaccounted changesets.
        """
        # When this changeset has one parent, and the parent has only
        # one child (this), they have the same preceding
        # changesets. Common, and much faster.
        if len(self.get_parents()) == 1:
            parent = self.get_parents()[0]
            if len(parent.get_children()) == 1:
                self.preceding_changesets = parent.get_unaccounted_changesets()
                return

        # when the preceding changesets have not been calculated yet,
        # or is empty, just insert the changeset and return.
        if self.preceding_changesets in [None, []]:
            self.preceding_changesets = [cs]
            return
        i = index
        preceding_css = set(self.preceding_changesets)
        while i < len(ordered_changesets):
            if ordered_changesets[i] == self:
                self.preceding_changesets.append(cs)
                break
            if ordered_changesets[i] in preceding_css:
                insertion_point = self.preceding_changesets.index(ordered_changesets[i])
                self.preceding_changesets.insert(insertion_point, cs)
                break
            i += 1
        
    def ot(self, hazards=[]):
        """
        All the unaccounted changesets should have already been
        determined. Loop through those, using them to transform this
        changeset.
        """
        for op in self.ops:
            op.reset_transformations()
        hazards_this_changeset_causes = []
        # those 'preceding_changesets' need to be used to transform
        # this changeset's operations.
        for pc in self.preceding_changesets:
            for op in self.ops:
                new_hazards = op.ot(pc, hazards)
                hazards.extend(new_hazards)
                hazards_this_changeset_causes.extend(new_hazards)
        return hazards_this_changeset_causes

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
