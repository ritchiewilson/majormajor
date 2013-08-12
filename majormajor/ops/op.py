
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
        self.noop = False
        
    def ot(self, pc):
        """
        pc: Changeset - previous changeset which has been applied but
        was not a dependency of this operation. This operation needs
        to be transformed to accomidate pc.
        """
        for op in pc.get_ops():
            func_name = self.json_opperations[op.action]
            transform_function = getattr(self, func_name)
            hazard = transform_function(op)
            if hazard:
                op.add_new_hazard(hazard)

    def add_new_hazard(self, hazard):
        self.hazards.append(hazard)

    def get_properties_shifted_by_hazards(self):
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

    def is_string_delete(self):
        return False

    def is_string_insert(self):
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

    

class SetOp(Op):
    pass
    
from string_insert_op import StringInsertOp
from string_delete_op import StringDeleteOp
