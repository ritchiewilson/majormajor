
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
        
    def ot(self, pc):
        """
        pc: Changeset - previous changeset which has been applied but
        was not a dependency of this operation. This operation needs
        to be transformed to accomidate pc.
        """
        for op in pc.ops:
            func_name = self.json_opperations[op.action]
            func = getattr(self, func_name)
            func(op)

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
    def string_insert_transform(self, op):
        if self.t_path != op.t_path:
            return

        if self.t_action == 'si':
            if self.t_offset >= op.t_offset:
                self.t_offset += len(op.t_val)

    def string_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return

        if self.t_offset >= op.t_offset + op.t_val:
            self.t_offset -= op.t_val
        elif self.t_offset > op.t_offset:
            self.t_offset = op.t_offset
            self.t_val = ''
 
        
class StringDeleteOp(Op):
    
    def string_insert_transform(self, op):
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

    def string_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.
        """
        if self.t_path != op.t_path:
            return
            
        # there are six ways two delete ranges can overlap and
        # each one is a different case.
        if self.t_action == 'sd':
            srs = self.t_offset # self range start
            sre = self.t_offset + self.t_val # self range end
            oprs = op.t_offset # prev op range start
            opre = op.t_offset + op.t_val # prev op range end
            if sre < oprs:
                #only case for which nothing changes
                pass
            elif srs >= opre:
                self.t_offset -= op.t_val
            elif srs >= oprs and sre >= opre:
                self.t_val += (self.t_offset - (op.t_offset + op.t_val))
                self.t_val = max(0, self.t_val)
                self.t_offset = op.t_offset
            elif sre >= opre:
                self.t_val -= op.t_val
            else:
                self.t_val = op.t_offset - self.t_offset

class SetOp(Op):
    pass
    
