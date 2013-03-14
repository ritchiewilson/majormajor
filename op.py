class Op:
    """
    offset is only used for string manipulation
    
    """
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


    def to_jsonable(self):
        s = [{'action': self.action}, {'path': self.path}]
        if self.val!=None:
            s.append({'val': self.val})
        if self.offset!=None:
            s.append({'offset': self.offset})
        return s

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

    def string_insert_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string insert.

        A past string insert only changes this opperation if 1) this
        is a string insert or string delete and 2) the two opperations
        have identical paths.

        If so, shift offset and possibly val
        """
        if self.t_action != 'si' and self.t_action != 'sd':
            return

        if self.t_path != op.t_path:
            return

        if self.t_action == 'si':
            if self.t_offset >= op.t_offset:
                self.t_offset += len(op.t_val)

        elif self.t_action == 'sd':
            # if text was inserted into the deletion range, expand the
            # range to delete that text as well.
            if self.t_offset + self.t_val > op.t_offset and self.t_offset < op.t_offset:
                self.t_val += len(op.t_val)
            # if the insertion comes before deletion range, shift
            # deletion range forward
            if self.t_offset >= op.t_offset:
                self.t_offset += len(op.t_val)                

    def string_delete_transform(self, op):
        """
        Transform this opperation when a previously unknown opperation
        did a string deletion.

        A past string insert only changes this opperation if 1) this
        is a string insert or string delete and 2) the two opperations
        have identical paths.
        
        If so, shift offset and possibly val
        """
        if self.t_action != 'si' and self.t_action != 'sd':
            return
        
        if self.t_path != op.t_path:
            return

        if self.t_action == 'si':
            if self.t_offset >= op.t_offset + op.t_val:
                self.t_offset -= op.t_val
            elif self.t_offset > op.t_offset:
                self.t_offset = op.t_offset
                self.t_val = ''


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
                
                

    json_opperations = {
        'set': 'set_value',
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

