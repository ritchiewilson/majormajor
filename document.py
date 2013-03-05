import json
import random
import string


class Document:
    snapshot = {}
    deps = []
    open_changeset = None

    def __init__(self, id_ = None):
        if id_ == None:
            id_ = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(5))
        self.id_ = id_
        

    
    def contains_path(self, path):
        """ Checks if the given path is valid in this document's snapshot """
        node = self.snapshot
        for i in path:
            if isinstance(i, str):
               if not isinstance(node, dict):
                  return False
               if not i in node:
                   return False
            elif isinstance(i, int):
                if not isinstance(node, list):
                    return False
                if i >= len(node):
                    return False
            node = node[i]
        return True
    
    def get_node(self, path):
        node = self.snapshot
        for i in path:
            node = node[i]
        return node

    def get_value(self, path, key=None):
        if key==None:
            return self.snapshot
        return self.get_node(path)[key]

    def apply_op(self, op):
        if not self.contains_path(op.path):
            return "ERROR!"
        
        func_name = self.json_opperations[op.action]
        func = getattr(self, func_name)
        if op.key == None:
            self.snapshot = func(op)
        else:
            node = self.get_node(op.path)
            node[op.key] = func(op)
            
    def set_value(self, op):
        return op.val

    def boolean_negation(self, op):
        cur = self.get_value(op.path, op.key)
        return False if cur else True

    def number_add(self, op):
        return self.get_value(op.path, op.key) + op.val

    def string_insert(self, op):
        cur = self.get_value(op.path, op.key)
        return  cur[:op.offset] + op.val + cur[op.offset:]

    def string_delete(self, op):
        cur = self.get_value(op.path, op.key)
        return cur[:op.offset] + cur[op.offset + op.val:]
        
    
    def array_insert(self, op):
        cur = self.get_value(op.path, op.key)
        r = cur[:op.offset]
        r.append(op.val)
        r.extend(cur[op.offset:])
        return r

    def array_delete(self, op):
        cur = self.get_value(op.path, op.key)
        r = cur[:op.offset]
        r.extend(cur[op.offset + op.val:])
        return r

    def array_move(self, op):
        cur = self.get_value(op.path, op.key)
        item = cur.pop(op.offset)
        r = cur[:op.val]
        r.append(item)
        r.extend(cur[op.val:])
        return r

    def object_insert(self, op):
        cur = self.get_value(op.path, op.key)
        cur[op.val['key']]  = op.val['val']
        return cur

    def object_delete(self, op):
        cur = self.get_value(op.path, op.key)
        cur.pop(op.offset)
        return cur

        
    json_opperations = {
        'set': 'set_value',
        'bn' : 'boolean_negation',
        'na' : 'number_add',
        'si' : 'string_insert',
        'sd' : 'string_delete',
        'ai' : 'array_insert',
        'ad' : 'array_delete',
        'am' : 'array_move',
        'oi' : 'object_insert',
        'od' : 'object_delete'
    }
