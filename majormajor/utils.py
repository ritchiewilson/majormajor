from op import Op
from changeset import Changeset

def build_changeset_from_dict(m, doc=None):
    """
    From a dict, build a changeset object with all its ops.
    If a doc is provided, this changeset will link up all
    availible dependencies.
    """
    p = m # used to send whole message. fix this later TODO
    dependencies = []
    for dep in m['dep_ids']:
        d = doc.get_changeset_by_id(dep) if doc else None
        dependencies.append(d if not d == None else dep)
    cs = Changeset(p['doc_id'], p['user'], dependencies)
    for j in p['ops']:
        op = Op(j['action'],j['path'],j['val'],j['offset'])
        cs.add_op(op)
    return cs
