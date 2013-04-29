from document import Document
from changeset import Changeset
from op import Op

d = Document()
d.add_op(Op('set', [], val='ABC123456DEFG'))
d.close_changeset()
d.add_op(Op('sd', [], val=3, offset=6))
d.close_changeset()


init_hash = d.changesets[0]
second_hash = d.changesets[1]
d_id = d.id_
cs1 = Changeset(d_id, 'NOT RITCHIE', [init_hash])
cs1.add_op(Op('sd', [], val=3, offset=3))
d.recieve_changeset(cs1)

for i in d.changesets:
    print("=========")
    for j in i.ops:
        print(j.action)

print (d.snapshot)
print('\n\n\n\n\n\n\n')
