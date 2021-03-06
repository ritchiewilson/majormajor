# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ..hazards.hazard import Hazard
from copy import deepcopy

class Op(object):
    """
    offset is only used for string manipulation

    """
    def __new__(cls, *args, **kwargs):
        subclass = {'si': StringInsertOp,
                    'sd': StringDeleteOp,
                    'sm': StringMoveOp,
                    'ai': ArrayInsertOp,
                    'ad': ArrayDeleteOp,
                    'oi': ObjectInsertOp,
                    'od': ObjectDeleteOp,
                    'set': SetOp }.get(args[0], cls)

        new_instance = object.__new__(subclass)
        new_instance.__init__(*args, **kwargs)
        return new_instance

    def __init__(self, action, path, val=None, offset=None,
                 dest_path=None, dest_offset=None):
        # These are the canonical original intentions. They are what's
        # actually stored in databases and sent to peers. Once set,
        # these values should not change.
        self.action = action
        self.path = path
        self.val = val
        self.offset = offset
        self.dest_path = dest_path
        self.dest_offset = dest_offset

        # These are copies, which are allowed to change based on
        # opperational transformations.
        self.t_action = action
        self.t_path = path
        self.t_val = val
        self.t_offset = offset
        self.t_dest_path = dest_path
        self.t_dest_offset = dest_offset
        self.noop = False
        self.reset_transformations()
        self.reset_hazard_transformations()

        self.changeset = None

        self.hazards = []
        self.hazards_between_branches = []
        self.valid_hazard_shifted_cache = False

        self.extends_at_head = False
        self.extends_at_tail = False

        self.past_t_noop = False

        self.val_shifting_ops = []
        self.deletion_edges = []

    def set_changeset(self, cs):
        self.changeset = cs

    def get_changeset(self):
        return self.changeset

    def get_path(self):
        """
        Get a copy of the orignal, unaltered path which was assigned to this
        Op.
        """
        return self.path[:]

    def get_transformed_path(self):
        """
        Get this Op's path after it has gone through all opperational
        transformation. This is the path used when this Op is applied to the
        documnet.
        """
        return self.t_path[:]

    def _get_hazard_shifted_path(self):
        """
        Get this Op's path as it will be when used in opperational
        transformation with a future Op.

        This value is only used during OT.
        """
        return self.past_t_path[:]

    def get_offset(self):
        """
        Get the orignal, unaltered offset which was assigned to this Op.
        """
        return self.offset[:]

    def get_transformed_offset(self):
        """
        Get this Op's offset after it has gone through all opperational
        transformation. This is the offset used when this Op is applied to the
        documnet.
        """
        return self.t_offset[:]

    def _get_hazard_shifted_offset(self):
        """
        Get this Op's offset as it will be when used in opperational
        transformation with a future Op.

        This value is only used during OT.
        """
        return self.past_t_offset[:]

    def get_val(self):
        """
        Get a copy of the orignal, unaltered val which was assigned to this Op.
        """
        return deepcopy(self.val)

    def get_transformed_val(self):
        """
        Get this Op's val after it has gone through all opperational
        transformation. This is the val used when this Op is applied to the
        documnet.
        """
        return deepcopy(self.t_val)

    def _get_hazard_shifted_val(self):
        """
        Get this Op's val as it will be when used in opperational
        transformation with a future Op.

        This value is only used during OT.
        """
        return deepcopy(self.past_t_val)

    def is_noop(self):
        """
        Returns if this Op has become a 'noop' due to opperational
        transformation.

        An Op becomes a 'no opperation', or 'noop', when it has gone through
        OT, and previous opperations make this invalid or superfluous. For
        example, this Op could become invalid if it should have happened within
        a node which was deleted. It could become superfluous if, for example
        this Op does a string delete which is effectively already covered in
        previous string deletes.

        Ops which have become a 'noop' will be skipped when applied to the
        document.

        :returns: If this Op should be skipped when applied to a document
        :rtype: bool
        """
        return self.noop

    def remove_old_hazards(self, css=[], purge=False):
        if purge:
            self.hazards = []
        else:
            self.hazards = [h for h in self.hazards
                            if not h.conflict_cs in css]
        self.reset_hazard_transformations()

    def hazard_is_relevant_for_ot(self, hazard, op):
        """
        Hazards stored in the op are only relevant when the conflic_cs is an
        acestor the changeset being transformed. For running tests, it is
        possible that the op has no cs, in which case ignore any hazards.

        TODO: THIS IS WHERE SHIT GETS UNUSABLY SLOW
        """
        cs = op.get_changeset()
        if not cs:
            return False
        h = hazard
        if not (cs is h.conflict_cs or cs.has_ancestor(h.conflict_cs)):
            return False
        if h.is_interbranch_hazard():
            dd_cs = h.interbranch_op.get_changeset()
            if not (cs is dd_cs or cs.has_ancestor(dd_cs)):
                return False
        return True

    def add_val_shifting_op(self, op, offset_shift=0, val_shift=0):
        self.val_shifting_ops.append((op, offset_shift, val_shift))

    def add_deletion_edge(self, op, head=None, tail=None):
        s = "Must specify if insert is at head or tail of delete range."
        if head is tail:
            raise Exception(s)
        at_head = not tail if head is None else head
        if not (at_head is True or at_head is False):
            raise Exception(s)
        self.deletion_edges.append((op, at_head))

    def add_interbranch_hazard(self, hazard):
        conflict_ops = hazard.get_interbranch_conflict_ops()
        i = 0
        for i, h in enumerate(reversed(self.hazards)):
            if h.get_conflict_op() in conflict_ops:
                index = len(self.hazards) - i
                self.hazards.insert(index, hazard)
                break

    def get_val_shifting_ops(self):
        return self.val_shifting_ops[:]

    def must_check_full_delete_range(self, op):
        if not op.is_noop():
            return False
        killing_ops = op.get_val_shifting_ops()
        if not killing_ops:
            return False
        k_op = killing_ops[0][0]
        if k_op.is_string_insert() or k_op.is_string_delete():
            return self.is_string_insert() or self.is_string_delete()
        return self.is_array_insert() or self.is_array_delete()

    def get_extended_delete_range(self, cs, past_del=False):
        start = self.past_t_offset if past_del else self.t_offset
        val = self.past_t_val if past_del else self.t_val
        for shift_op, offset_shift, val_shift in self.val_shifting_ops:
            if not cs.has_ancestor(shift_op.get_changeset()):
                start += offset_shift
                val += val_shift
        stop = start + val
        return start, stop

    def is_in_interbranch_deletion_range(self, op):
        at_head_of_prev_op = self.deletion_edges[-1][1]
        interbranch_del = None
        op_vso = set([vso[0] for vso in op.get_val_shifting_ops()])
        for edge in self.deletion_edges:
            if edge[1] != at_head_of_prev_op:
                if edge[0] in op_vso:
                    return True
                interbranch_del = edge[0]
                #break
        return False
        if not interbranch_del:
            return False
        if interbranch_del.t_val == 0 or op.t_val == 0:
            return False
        if at_head_of_prev_op:
            return (interbranch_del.extends_at_tail or op.extends_at_head)
        return (interbranch_del.extends_at_head or op.extends_at_tail)

    def to_jsonable(self):
        s = [{'action': self.action}, {'path': self.path}]
        if not self.val is None:
            s.append({'val': self.val})
        if not self.offset is None:
            s.append({'offset': self.offset})
        return s

    def to_dict(self):
        s = {'action': self.action,
             'path': self.path,
             'val': self.val,
             'offset': self.offset}
        return s

    def reset_transformations(self):
        """
        Reset how this Op will be applied to the document by reseting its
        tranformed values to the original values. This is typically only done
        at the begining of this Op's opperational transformation.
        """
        self.t_action = deepcopy(self.action)
        self.t_path = deepcopy(self.path)
        self.t_val = deepcopy(self.val)
        self.t_offset = self.offset
        self.t_dest_path = deepcopy(self.dest_path)
        self.t_dest_offset = self.dest_offset
        self.noop = False
        self.val_shifting_ops = []
        self.deletion_edges = []
        self.extends_at_head = False
        self.extends_at_tail = False

    def reset_hazard_transformations(self):
        """
        Reset how this Op will be used in opperational transformation with a
        future Op.
        """
        self.past_t_action = deepcopy(self.t_action)
        self.past_t_path = deepcopy(self.t_path)
        self.past_t_val = deepcopy(self.t_val)
        self.past_t_offset = self.t_offset
        self.past_t_dest_path = deepcopy(self.t_dest_path)
        self.past_t_dest_offset = self.t_dest_offset
        self.past_t_noop = False
        self.valid_hazard_shifted_cache = False

    def ot(self, pc):
        """
        pc: Changeset - previous changeset which has been applied but
        was not a dependency of this operation. This operation needs
        to be transformed to accomidate pc.
        """
        for op in pc.get_ops():
            #if op.is_noop():
            #    continue
            func_name = self.json_opperations[op.action]
            transform_function = getattr(self, func_name)
            op.process_for_future_ot(self)
            if op.past_t_noop:
                continue
            hazard = transform_function(op)
            if hazard:
                op.add_new_hazard(hazard)

    def add_new_hazard(self, hazard):
        if hazard._is_between_branches:
            self.hazards_between_branches.append(hazard)
        else:
            self.hazards.append(hazard)
        self.apply_hazard(hazard)

    def apply_hazard(self, hazard):
        if hazard.is_noop_hazard():
            self.past_t_noop = True
        if hazard.is_path_hazard():
            self.past_t_path = hazard.get_path_shift()
        if hazard.is_offset_hazard():
            self.past_t_offset += hazard.get_offset_shift()
        if hazard.is_val_hazard():
            self.past_t_val += hazard.get_val_shift()

    def process_for_future_ot(self, op):
        """
        Prepare this Op for transforming a future Op by applying all
        :class:`Hazards<Hazard>` and storing the resulting values.
        """
        cs = op.get_changeset()
        if cs and not cs.is_singly_linked_with_parent():
            self.valid_hazard_shifted_cache = False
        #if self.valid_hazard_shifted_cache:
        #    return
        self.reset_hazard_transformations()
        for hazard in self.hazards:
            if self.hazard_is_relevant_for_ot(hazard, op):
                self.apply_hazard(hazard)
            if self.past_t_noop:
                break
        self.valid_hazard_shifted_cache = True

    def set_transform(self, op):
        """
        Transfrom this opperation for a when a previously unknown
        opperation was a "set" opperation.
        """
        if self.is_noop() or op.is_noop():
            return

        # If the set opperation was in the path of this op, this
        # becomes a noop. Otherwise fine
        op_path = op.get_transformed_path()
        if op_path == self.t_path[:len(op_path)]:
            self.noop = True

    def string_insert_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string insert.

        In the default case, pass
        """
        pass

    def string_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.

        In all default cases, do nothing
        """
        pass

    def array_insert_transform(self, op):
        """
        Previous op was an array insert. Shift this ops path if necessary.
        """
        hazard = False

        past_t_path, past_t_offset, past_t_val \
            = op.past_t_path, op.past_t_offset, op.past_t_val

        if len(self.t_path) <= len(past_t_path):
            return
        path_index = len(past_t_path)  # the only path peice that might move
        if past_t_path == self.t_path[:path_index]:
            if past_t_offset <= self.t_path[path_index]:
                self.t_path[path_index] += len(past_t_val)
        return hazard

    def array_delete_transform(self, op):
        """
        Previous op was an array delete. If this changeset went into the delete
        range, this becomes a noop. If the ops share a path, and the delete
        range comes before the index for this op, shift the path.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.past_t_path, op.past_t_offset, op.past_t_val

        if len(self.t_path) <= len(past_t_path):
            return

        path_index = len(past_t_path)  # the only path peice that might move
        if past_t_path == self.t_path[:path_index]:
            delete_range = xrange(past_t_offset, past_t_offset + past_t_val)
            if self.t_path[path_index] in delete_range:
                self.noop = True
                self.set_value_to_nil()
                return
            if not self.t_path[path_index] < past_t_offset:
                self.t_path[path_index] -= past_t_val
        return False

    def object_insert_transform(self, op):
        """
        This op is being transformed by a previously unknown object insert. The
        result is either no change, or switch to noop
        """
        past_t_path, past_t_offset, past_t_val = \
            op.past_t_path, op.past_t_offset, op.past_t_val

        r = self.object_transformation(past_t_path, past_t_offset, past_t_val)
        return r

    def object_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation did an
        object deletion. Either this is fine or a noop.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.past_t_path, op.past_t_offset, op.past_t_val

        r = self.object_transformation(past_t_path, past_t_offset, past_t_val)
        return r

    def get_size_of_original_delete_overlap(self, op):
        """
        Figure out the original overlap size of the delete ranges of self and
        op. This essentially means how much they would have overlapped if self
        and op were the only final dependencies of the doc, and have not been
        transformed by any branch unknown to either.This is needed to determine
        if a hazard must be added previous unaccounted ops common to both.
        """
        # first get the two deletes intended ranges, and find their overlap
        cs = self.get_changeset()
        if not cs:
            return 0
        past_start, past_stop = op.get_extended_delete_range(cs, past_del=True)
        self_start, self_stop = \
            self.get_extended_delete_range(op.get_changeset(), past_del=False)
        overlap = 0
        if past_start <= self_start and self_start < past_stop:
            if self_stop < past_stop:
                overlap = self_stop - self_start
            else:
                overlap = past_stop - self_start
        elif self_start <= past_start and self_stop > past_start:
            if self_stop < past_stop:
                overlap = self_stop - past_start
            else:
                overlap = past_stop - past_start
        return overlap

    def add_double_delete_hazard_to_common_prev_ops(self, op, overlap):
        """
        When self and op should have been overlapping deletes, add a hazard to
        all their common previous unaccounted ops.
        """
        # Find any previous ops which partially deleted (val shifted) both of
        # these ops. if any of the same ops deleted them both, then there is
        # some interbranch overlap which requires a hazard
        needed_val_shifts = set([])
        ops_that_val_shifted_self = set([vso[0] for vso in
                                        self.val_shifting_ops])
        for shift_op, offset_shift, val_shift in op.get_val_shifting_ops():
            if not shift_op in ops_that_val_shifted_self:
                continue

            self_val_shift = 0
            for vso in self.val_shifting_ops:
                if vso[0] == shift_op:
                    self_val_shift = vso[2]
                    break
            # the size of the three layered overlap is the min of any two of
            # their overlaps.
            size = min(overlap, self_val_shift, val_shift)
            ddh = Hazard(shift_op, op, self, val_shift=size)
            shift_op.add_interbranch_hazard(ddh)
            needed_val_shifts.update([shift_op])

        # now that all those triple overlapping deletes are accounted for, add
        # hazards to every other past operation not known to these two ops.
        cs = self.changeset
        self_ucs = set(cs.get_unaccounted_changesets())
        op_ucs = set(op.get_changeset().get_unaccounted_changesets())
        common_css = self_ucs.intersection(op_ucs)
        for prev_cs in common_css:
            for prev_op in prev_cs.get_ops():
                if prev_op in needed_val_shifts:
                    continue
                h = Hazard(prev_op, op, self, offset_shift=overlap)
                prev_op.add_interbranch_hazard(h)

    def transform_delete_by_previous_delete(self, op,
                                            past_t_offset, past_t_val):
        """
        Transform a string_delete by a string_delete when they apply to the
        same string, or transform an array_delete by an array_delete when they
        apply to the same array.

        Depending on if and how the delete ranges overlap, this will shift the
        offset and val, then create and return any apropriate hazard.

        :param op: Previous Op this is being transformed by
        :param past_t_offset: The offset of op with all hazards applied
        :type past_t_offset: int
        :param past_t_val: The val of op with all hazards applied
        :type past_t_val: int
        :returns: Hazard caused by this OT or False if not needed
        :rtype: Hazard or False
        """
        # first check if these deletes would have overlapped if not shortend
        original_overlap  = self.get_size_of_original_delete_overlap(op)
        if original_overlap != 0:
            self.add_double_delete_hazard_to_common_prev_ops(op,
                                                             original_overlap)

        hazard = False

        srs = self.t_offset  # self range start
        sre = self.t_offset + self.t_val  # self range end
        oprs = past_t_offset  # prev op range start
        opre = past_t_offset + past_t_val  # prev op range end
        # there are six ways two delete ranges can overlap and
        # each one is a different case.

        # case 1
        #                |-- prev op --|
        # |-- self --|
        if sre <= oprs:
            shift = self.t_val * -1
            hazard = Hazard(op, self, offset_shift=shift)
        # case 2
        #   |-- prev op --|
        #                   |-- self --|
        elif srs >= opre:
            self.t_offset -= past_t_val
        # case 3
        #   |-- prev op --|
        #           |-- self --|
        elif srs >= oprs and sre > opre:
            overlap = srs - opre
            hazard = Hazard(op, self, val_shift=overlap)
            self.t_val += (self.t_offset - (past_t_offset + past_t_val))
            offset_shift = self.t_offset - past_t_offset
            self.t_offset = past_t_offset
            self.add_val_shifting_op(op, offset_shift, overlap * -1)
            self.extends_at_head = True
        # case 4
        #   |--- prev op ---|
        #     |-- self --|
        elif srs >= oprs and sre <= opre:
            overlap = srs - sre
            hazard = Hazard(op, self, val_shift=overlap)
            offset_shift = self.t_offset - past_t_offset
            self.t_offset = past_t_offset
            self.t_val = 0
            self.noop = True
            self.add_val_shifting_op(op, offset_shift, overlap * -1)
            #self.extends_at_head = False
            #self.extends_at_tail = False
        # case 5
        #     |-- prev op --|
        #   |----- self ------|
        elif sre >= opre:
            overlap = past_t_val * -1
            hazard = Hazard(op, self, noop_shift=True)
            self.t_val -= past_t_val
            self.add_val_shifting_op(op, val_shift=past_t_val)
        # case 6
        #      |-- prev op --|
        #   |-- self --|
        else:
            overlap = oprs - sre
            offset_shift = srs - oprs
            hazard = Hazard(op, self, offset_shift=offset_shift,
                            val_shift=overlap)
            self.t_val = past_t_offset - self.t_offset
            val_shift = overlap * -1
            self.add_val_shifting_op(op, val_shift=val_shift)
            self.extends_at_tail = True

        return hazard

    def transform_insert_by_previous_insert(self, op, past_t_offset,
                                            past_t_val):
        """
        Transform a string_insert by a string_insert when they apply to the
        same string, or transform an array_insert by an array_insert when they
        apply to the same array.

        When the previous op's offset is at a lower index, this op needs to be
        shifted forward in the string or array. Otherwise it does not need to
        change, but needs to return a hazard instead.

        :param op: Previous Op this is being transformed by
        :param past_t_offset: The offset of op with all hazards applied
        :type past_t_offset: int
        :param past_t_val: The val of op with all hazards applied
        :type past_t_val: str or list
        :returns: Hazard caused by this OT or False if not needed
        :rtype: Hazard or False
        """
        hazard = False
        if self.t_offset >= past_t_offset:
            self.t_offset += len(past_t_val)
        else:
            hazard = Hazard(op, self, offset_shift=len(self.t_val))
        return hazard

    def transform_insert_by_previous_delete(self, op, past_t_offset,
                                            past_t_val):
        """
        Transform a string_insert by a string_delete when they apply to the
        same string, or transform an array_insert by an array_delete when they
        apply to the same array.

        When this insertion happens at an index above the previous op's
        deletion range, this op's offset needs to shift back by that amount. If
        it is in the deletion range, this becomes a noop, and the value is
        reduced to nothing ('' for strings, [] for arrays). This will also
        return a Hazards. Finally, if this insertion's happens at an index
        below the deletion range, this Op does not need to change, but it will
        return a Hazard.

        The boundaries of the deletion range are excluded from the deletion
        range. This allows inserts at the edge cases to be preserved, and data
        is not unnecessarily deleted.

        :param op: Previous Op this is being transformed by
        :param past_t_offset: The offset of op with all hazards applied
        :type past_t_offset: int
        :param past_t_val: The val of op with all hazards applied
        :type past_t_val: int
        :returns: Hazard caused by this OT or False if not needed
        :rtype: Hazard or False
        """
        hazard = False

        if op.must_check_full_delete_range(self):
            cs = self.get_changeset()
            start, stop = op.get_extended_delete_range(cs, past_del=True)
            insert_offset = self.t_offset
            insert_offset += self.val_shifting_ops[0][1]
            if start < insert_offset and stop > insert_offset:
                # I got deleted twice
                overlapping_op = self.val_shifting_ops[0][0]
                s = len(self.val) * -1
                ddh = Hazard(overlapping_op, op, self, val_shift=s)
                overlapping_op.add_interbranch_hazard(ddh)

        def delete_self(s):
            offset = s.t_offset - past_t_offset
            s.t_offset = past_t_offset
            vs = len(s.t_val)
            s.set_value_to_nil()
            s.noop = True
            s.add_val_shifting_op(op, offset)
            h = Hazard(op, s, val_shift=vs)
            if self.changeset:
                self.changeset.alert_preceding_changesets_of_deletion(op,
                                                                      self, vs)
            return h

        # If this insertion is exactly at the edge of the past delete, see if
        # it falls into an interbranch delete range. If it does, make this a
        # noop, otherwise, shift as normal.
        if self.t_offset == past_t_offset + past_t_val:
            self.add_deletion_edge(op, tail=True)
            if self.is_in_interbranch_deletion_range(op):
                hazard = delete_self(self)
            else:
                self.t_offset -= past_t_val
        # This insert happens beyond the delete range, so it needs to be
        # shifted back into place.
        elif self.t_offset > past_t_offset + past_t_val:
            self.t_offset -= past_t_val
        # This insert is within a past delete range
        elif self.t_offset > past_t_offset:
            hazard = delete_self(self)
        # If this insertion is exactly at the edge of the past delete, see if
        # it falls into an interbranch delete range. If it does, make this a
        # noop, otherwise, shift as normal.
        elif self.t_offset == past_t_offset:
            self.add_deletion_edge(op, head=True)
            if self.is_in_interbranch_deletion_range(op):
                hazard = delete_self(self)
            else:
                hazard = Hazard(op, self, offset_shift=len(self.t_val))
        # Otherwise this insert is at a lower index than the delete range, so
        # just create a hazard.
        else:
            hazard = Hazard(op, self, offset_shift=len(self.t_val))

        return hazard

    def transform_delete_by_previous_insert(self, op, past_t_offset,
                                            past_t_val):
        """Transform a string_delete by a string_insert when they apply to the
        same string, or transform an array_delete by an array_insert when they
        apply to the same array.

        When this deletion happens at an index above the previous op's offset,
        this op's offset needs to shift forward by the size of the insert.. If
        the past insertion is in this deletion range, this expands to encompass
        the inserted text as well. Finally, if this deletion range is lower
        than the index of the past insertion, this Op does not need to change,
        but it will return a Hazard.

        The boundaries of the deletion range are excluded from the deletion
        range. This allows inserts at the edge cases to be preserved, and data
        is not unnecessarily deleted.

        :param op: Previous Op this is being transformed by
        :param past_t_offset: The offset of op with all hazards applied
        :type past_t_offset: int
        :param past_t_val: The val of op with all hazards applied
        :type past_t_val: str or list
        :returns: Hazard caused by this OT or False if not needed
        :rtype: Hazard or False
        """
        hazard = False

        in_deletion_range = self.t_offset + self.t_val > past_t_offset and \
                                     self.t_offset < past_t_offset

        # first determine if this and some other past delete have overlapping
        # ranges, which both delete the insert.
        if self.must_check_full_delete_range(op):
            cs = op.get_changeset()
            start, stop = self.get_extended_delete_range(cs)
            insert_offset = op.t_offset
            insert_offset += op.val_shifting_ops[0][1]
            if start < insert_offset and stop > insert_offset:
                overlapping_op = op.get_val_shifting_ops()[0][0]
                s = len(op.get_val()) * -1
                ddh = Hazard(overlapping_op, self, op, val_shift=s)
                overlapping_op.add_interbranch_hazard(ddh)

        def expand_deletion_range(s):
            """Local helper called in several conds. Returns needed hazard"""
            s.t_val += len(past_t_val)
            s.add_val_shifting_op(op, 0, -1 * len(past_t_val))
            return Hazard(op, s, noop_shift=True)

        # if insertion was in this deletion range, expand the range to delete
        # that text as well.
        if in_deletion_range:
            hazard = expand_deletion_range(self)
        # if insertion is exactly at start of deletion range, check if this is
        # part of an interbranch delete range. If so, delete. Otherwise shift
        # like normal.
        elif self.t_offset == past_t_offset:
            op.add_deletion_edge(self, head=True)
            if op.is_in_interbranch_deletion_range(self):
                hazard = expand_deletion_range(self)
            else:
                self.t_offset += len(past_t_val)
        elif self.t_offset + self.t_val == past_t_offset:
            op.add_deletion_edge(self, tail=True)
            if op.is_in_interbranch_deletion_range(self):
                hazard = expand_deletion_range(self)
            else:
                shift = self.t_val * -1
                hazard = Hazard(op, self, offset_shift=shift)
        # if the insertion comes before deletion range, shift deletion range
        # forward
        elif self.t_offset > past_t_offset:
            self.t_offset += len(past_t_val)
        # Otherwise the past insertion has a higher index, so should be shifted
        # to come in line with current document.
        else:
            shift = self.t_val * -1
            hazard = Hazard(op, self, offset_shift=shift)

        return hazard

    def object_transformation(self, past_t_path, past_t_offset, past_t_val):
        """
        For any object transformations, the results are the same. Either 1)
        there is no conflict and the previous op does nothing or 2) there is a
        conflict and the prev op forces this to be a noop.
        """
        # when this path is shorter than the old one, nothing needs to be done.
        if len(self.t_path) < len(past_t_path):
            pass

        # when the paths are exactly equal, this offset may need to shift up
        elif past_t_path == self.t_path:
            if past_t_offset == self.t_offset:
                self.noop = True
        # otherwise the path may need to shift
        elif past_t_path == self.t_path[:len(past_t_path)]:
            if past_t_offset == self.t_path[len(past_t_path)]:
                self.noop = True
        return False

    def is_string_delete(self):
        return False

    def is_string_insert(self):
        return False

    def is_string_move(self):
        return False

    def is_array_insert(self):
        return False

    def is_array_delete(self):
        return False

    json_opperations = {
        'set': 'set_transform',
        'bn': 'boolean_negation_transform',
        'na': 'number_add_transform',
        'si': 'string_insert_transform',
        'sd': 'string_delete_transform',
        'ai': 'array_insert_transform',
        'ad': 'array_delete_transform',
        'am': 'array_move_transform',
        'oi': 'object_insert_transform',
        'od': 'object_delete_transform'
    }



class SetOp(Op):
    pass
    # def __init__(self, *args, **kwargs):
    #     super().__init__(args, kwargs)

from .string_insert_op import StringInsertOp
from .string_delete_op import StringDeleteOp
from .string_move_op import StringMoveOp
from .array_insert_op import ArrayInsertOp
from .array_delete_op import ArrayDeleteOp
from .object_insert_op import ObjectInsertOp
from .object_delete_op import ObjectDeleteOp
