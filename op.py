class Op:
    """
    When a key is not specified, then the root object is a simple
    value (string, boolean, number) and the opperation is being appled
    at the root level.

    offset is only used for string manipulation
    
    """
    def __init__(self, action, path, val=None, offset=None):
        self.action = action
        self.path = path
        self.val = val
        self.offset = offset


    def to_jsonable(self):
        s = [{'action': self.action}, {'path': self.path}]
        if self.val!=None:
            s.append({'val': self.val})
        if self.offset!=None:
            s.append({'offset': self.offset})
        return s

    def to_dict(self):
        s = {'action': self.action, 'path': self.path}
        if self.val!=None:
            s['val'] = self.val
        if self.offset!=None:
            s['offset'] = self.offset
        return s
