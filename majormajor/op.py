
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

from hazard import Hazard

class Op(object):
    """
    offset is only used for string manipulation
    
    """
    def __new__(cls, *args, **kwargs):
        subclass = {'si': StringInsertOp,
                    'sd': StringDeleteOp,
                    'set': SetOp }.get(args[0], cls)
        
        new_instance = object.__new__(subclass, *args, **kwargs)
        return new_instance
        
        
    def __init__(self, action, path, val=None, offset=None):
        # These are the canonical original intentions. They are what's
        # actually stored in databases and sent to peers. Once set,
        # these values should not change.
        self.action = action
        self.path = path
        self.val = val
        self.offset = offset

        # These are copies, which are allowed to change based on
        # opperational transformations.
        self.t_action = action
        self.t_path = path
        self.t_val = val
        self.t_offset = offset
        self.noop = False

        self.changeset = None

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

    def to_jsonable(self):
        s = [{'action': self.action}, {'path': self.path}]
        if self.val!=None:
            s.append({'val': self.val})
        if self.offset!=None:
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
        self.noop = False
        
    def ot(self, pc, hazards=[]):
        """
        pc: Changeset - previous changeset which has been applied but
        was not a dependency of this operation. This operation needs
        to be transformed to accomidate pc.
        """
        new_hazards = []
        for i, op in enumerate(pc.ops):
            hazards_after_conflict_point = [h for h in hazards \
                                            if not h.base_cs == pc or \
                                            h.get_base_op_index() <= i]
            # then run OT, checking for new hazards
            func_name = self.json_opperations[op.action]
            transform_function = getattr(self, func_name)
            hazard = transform_function(op, hazards_after_conflict_point)
            if hazard:
                new_hazards.append(hazard)
        return new_hazards

        
    def set_transform(self, op, hazards):
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

    def string_insert_transform(self, op, hazards):
        """
        Transform this opperation when a previously unknown opperation
        did a string insert.

        In the default case, pass
        """
        pass
        
    def string_delete_transform(self, op, hazards):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.

        In all default cases, do nothing
        """
        pass
                
    def is_string_transform(self):
        return False

    def is_string_delete(self):
        return False

    json_opperations = {
        'set': 'set_transform',
        'bn' : 'boolean_negation',
        'na' : 'number_add',
        'si' : 'string_insert_transform',
        'sd' : 'string_delete_transform',
        'ai' : 'array_insert',
        'ad' : 'array_delete',
        'am' : 'array_move',
        'oi' : 'object_insert',
        'od' : 'object_delete'
    }

class StringInsertOp(Op):
    def is_string_transform(self):
        return True
        
    def string_insert_transform(self, op, hazards):
        if self.t_path != op.t_path:
            return
        past_t_offset = op.t_offset
        for hazard in hazards:
            past_t_offset -= hazard.get_string_insert_offset_shift()
        
        if self.t_offset >= past_t_offset:
            self.t_offset += len(op.t_val)

    def string_delete_transform(self, op, hazards):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return

        past_t_val = op.t_val
        past_t_offset = op.t_offset
        for hazard in hazards:
            if hazard.conflict_op_t_offset < hazard.base_op_t_offset:
                past_t_offset += hazard.get_delete_overlap_range_size()
            past_t_val -= hazard.get_delete_overlap_range_size()

        if self.t_offset >= past_t_offset + past_t_val:
            self.t_offset -= past_t_val
        elif self.t_offset > past_t_offset:
            self.t_offset = past_t_offset
            self.t_val = ''
 
        
class StringDeleteOp(Op):
    def is_string_transform(self):
        return True

    def is_string_delete(self):
        return True
    
    def string_insert_transform(self, op, hazards):
        if self.t_path != op.t_path:
            return

        # if text was inserted into the deletion range, expand the
        # range to delete that text as well.
        if self.t_offset + self.t_val > op.t_offset and self.t_offset < op.t_offset:
            self.t_val += len(op.t_val)
        # if the insertion comes before deletion range, shift
        # deletion range forward
        elif self.t_offset >= op.t_offset:
            self.t_offset += len(op.t_val)

    def string_delete_transform(self, op, hazards):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return

        hazard = False
            
        srs = self.t_offset # self range start
        sre = self.t_offset + self.t_val # self range end
        oprs = op.t_offset # prev op range start
        opre = op.t_offset + op.t_val # prev op range end
        # there are six ways two delete ranges can overlap and
        # each one is a different case.

        # case 1
        #                |-- prev op --|
        # |-- self --|
        if sre <= oprs:
            pass
        # case 2
        #   |-- prev op --|
        #                   |-- self --|
        elif srs >= opre:
            self.t_offset -= op.t_val
        # case 3
        #   |-- prev op --|
        #           |-- self --|
        elif srs >= oprs and sre > opre:
            hazard = Hazard(op, self)
            self.t_val += (self.t_offset - (op.t_offset + op.t_val))
            self.t_val = max(0, self.t_val)
            self.t_offset = op.t_offset
        # case 4
        #   |--- prev op ---|
        #     |-- self --|
        elif srs >= oprs and sre <= opre:
            hazard = Hazard(op, self)
            self.t_offset = op.t_offset
            self.t_val = 0
        # case 5
        #     |-- prev op --|
        #   |----- self ------|
        elif sre >= opre:
            hazard = Hazard(op, self)
            self.t_val -= op.t_val
        # case 6
        #      |-- prev op --|
        #   |-- self --|
        else:
            hazard = Hazard(op, self)
            self.t_val = op.t_offset - self.t_offset

        return hazard

class SetOp(Op):
    pass
    
