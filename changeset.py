import hashlib

class Changeset:
    self.id_ = None
    self.ops = []
    self.ops_transformed = []
    def __init__(self, doc_id, author, deps):
        self.doc_id = doc_id
        self.author = author
        self.deps = deps

    def add_op(self, op):
        if self.id_:
            return False
        self.ops.append(op)
        return True


    def to_json(self):
        op_list = []
        for op in self.ops:
            op_list.append(op.to_jsonable())
        j = [{'doc_id': self.doc_id}, {'author':self.author},\
             {'deps':self.deps}, {'ops': op_list}]
        return j

    def get_id(self):
        if self.id_ == None:
            h = hashlib.sha1()
            h.update(self.to_json())
            self.id_ = h.digest()
        return self.id_

        
                
