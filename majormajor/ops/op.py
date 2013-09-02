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
        
        new_instance = object.__new__(subclass, *args, **kwargs)
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

        self.changeset = None
        
        self.hazards = []

    def set_changeset(self, cs):
        self.changeset = cs

    def get_changeset(self):
        return self.changeset

    def get_path(self):
        return self.path[:]

    def get_transformed_path(self):
        return self.t_path[:]

    def is_noop(self):
        return self.noop

    def remove_old_hazards(self, css):
        self.hazards = [h for h in self.hazards if not h.conflict_cs in css]

    def get_relevant_hazards(self, op):
        """
        Filter all of the stored Hazards in this op to just the ones needed for
        ot with the given Op.

        :param op: The future :class:`Op` which is being transformed by this op
        :rtype: list of :class:`Ops<Op>`
        """
        return [h for h in self.hazards
                if self.hazard_is_relevant_for_ot(h, op)]

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
        return True

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
        self.t_action = deepcopy(self.action)
        self.t_path = deepcopy(self.path)
        self.t_val = deepcopy(self.val)
        self.t_offset = self.offset
        self.t_dest_path = deepcopy(self.dest_path)
        self.t_dest_offset = self.dest_offset
        self.noop = False

    def ot(self, pc):
        """
        pc: Changeset - previous changeset which has been applied but
        was not a dependency of this operation. This operation needs
        to be transformed to accomidate pc.
        """
        for op in pc.get_ops():
            if op.is_noop():
                continue
            func_name = self.json_opperations[op.action]
            transform_function = getattr(self, func_name)
            op.process_for_future_ot(self)
            hazard = transform_function(op)
            if hazard:
                op.add_new_hazard(hazard)

    def add_new_hazard(self, hazard):
        self.hazards.append(hazard)

    def process_for_future_ot(self, op):
        """
        Prepare this Op for transforming a future Op by applying all
        :class:`Hazards<Hazard>` and storing the resulting values.
        """
        past_t_path, past_t_offset, past_t_val = \
            self.get_properties_shifted_by_hazards(op)
        self.past_t_path = past_t_path
        self.past_t_offset = past_t_offset
        self.past_t_val = past_t_val

    def get_properties_shifted_by_hazards(self, cs):
        """
        Calculate how this op should be handled by a future op, accounting
        for any hazards that need to be applied. This is overriden by
        each op. By default, there are no hazards, so just return these
        transformed properties.
        """
        return self.t_path, self.t_offset, self.t_val

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
        past_t_path, past_t_offset, past_t_val \
            = op.get_properties_shifted_by_hazards(self)

        if len(self.t_path) <= len(past_t_path):
            return

        path_index = len(past_t_path)  # the only path peice that might move
        if past_t_path == self.t_path[:path_index]:
            delete_range = xrange(past_t_offset, past_t_offset + past_t_val)
            if self.t_path[path_index] in delete_range:
                self.noop = True
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
            op.get_properties_shifted_by_hazards(self)
        r = self.object_transformation(past_t_path, past_t_offset, past_t_val)
        return r

    def object_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation did an
        object deletion. Either this is fine or a noop.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self)

        r = self.object_transformation(past_t_path, past_t_offset, past_t_val)
        return r

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
            self.t_offset = past_t_offset
        # case 4
        #   |--- prev op ---|
        #     |-- self --|
        elif srs >= oprs and sre <= opre:
            overlap = srs - sre
            hazard = Hazard(op, self, val_shift=overlap)
            self.t_offset = past_t_offset
            self.t_val = 0
            self.noop = True
        # case 5
        #     |-- prev op --|
        #   |----- self ------|
        elif sre >= opre:
            overlap = past_t_val * -1
            hazard = Hazard(op, self, val_shift=overlap)
            self.t_val -= past_t_val
        # case 6
        #      |-- prev op --|
        #   |-- self --|
        else:
            overlap = oprs - sre
            offset_shift = srs - oprs
            hazard = Hazard(op, self, offset_shift=offset_shift,
                            val_shift=overlap)
            self.t_val = past_t_offset - self.t_offset

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

        if self.t_offset >= past_t_offset + past_t_val:
            self.t_offset -= past_t_val
        elif self.t_offset > past_t_offset:
            self.t_offset = past_t_offset
            vs = len(self.t_val)
            # If string insert, blank val is '', for array it is []
            self.t_val = '' if self.is_string_insert() else []
            self.noop = True
            hazard = Hazard(op, self, val_shift=vs)
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

        # if insertion was in this deletion range, expand the range to delete
        # that text as well.
        if self.t_offset + self.t_val > past_t_offset \
                and self.t_offset < past_t_offset:
            self.t_val += len(past_t_val)
        # if the insertion comes before deletion range, shift deletion range
        # forward
        elif self.t_offset >= past_t_offset:
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
    
from .string_insert_op import StringInsertOp
from .string_delete_op import StringDeleteOp
from .string_move_op import StringMoveOp
from .array_insert_op import ArrayInsertOp
from .array_delete_op import ArrayDeleteOp
from .object_insert_op import ObjectInsertOp
from .object_delete_op import ObjectDeleteOp
