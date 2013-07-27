
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

from ops.op import Op
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

