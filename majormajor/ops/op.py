
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

from ..hazards.hazard import Hazard


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

    def get_relevant_hazards(self, cs=None):
        """
        Hazards stored in the op are only relevant when the conflic_cs is an
        acestor the changeset being transformed. For running tests, it is
        possible that the op has no cs, in which case ignore any hazards.

        TODO: THIS IS WHERE SHIT GETS UNUSABLY SLOW
        """
        if cs is None:
            return []

        return [h for h in self.hazards
                if cs is h.conflict_cs or
                cs.has_ancestor(h.conflict_cs)]

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
        self.t_action = self.action
        self.t_path = self.path
        self.t_val = self.val
        self.t_offset = self.offset
        self.t_dest_path = self.dest_path
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
            hazard = transform_function(op)
            if hazard:
                op.add_new_hazard(hazard)

    def add_new_hazard(self, hazard):
        self.hazards.append(hazard)

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
        past_t_path, past_t_offset, past_t_val \
            = op.get_properties_shifted_by_hazards(self.get_changeset())

        if len(self.t_path) <= len(past_t_path):
            return

        path_index = len(past_t_path)  # the only path peice that might move
        if past_t_path == self.t_path[:path_index]:
            if past_t_offset <= self.t_path[path_index]:
                self.t_path[path_index] += len(past_t_val)
        return

    def array_delete_transform(self, op):
        """
        Previous op was an array delete. If this changeset went into the delete
        range, this becomes a noop. If the ops share a path, and the delete
        range comes before the index for this op, shift the path.
        """
        past_t_path, past_t_offset, past_t_val \
            = op.get_properties_shifted_by_hazards(self.get_changeset())

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
            op.get_properties_shifted_by_hazards(self.get_changeset())
        r = self.object_transformation(past_t_path, past_t_offset, past_t_val)
        return r

    def object_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation did an
        object deletion. Either this is fine or a noop.
        """
        past_t_path, past_t_offset, past_t_val = \
            op.get_properties_shifted_by_hazards(self.get_changeset())

        r = self.object_transformation(past_t_path, past_t_offset, past_t_val)
        return r

    def shift_from_overlaping_delete_ranges(self, op,
                                            past_t_offset, past_t_val):
        """
        The transformations are the same for when combining two array_deletes
        with the same path or two string deletes in the same string. Depending
        on if and how the delete ranges overlap, this will shift the offset and
        val, plus create the apropriate hazards.
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

    def shift_from_consecutive_inserts(self, op, past_t_offset, past_t_val):
        """
        With string inserts working on the same string or array inserts working
        on the same array, the OT and resulting hazards are the same. This is
        called in those cases to handle the ot and return the needed Hazard.
        """
        hazard = False
        if self.t_offset >= past_t_offset:
            self.t_offset += len(past_t_val)
        else:
            hazard = Hazard(op, self, offset_shift=len(self.t_val))
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
