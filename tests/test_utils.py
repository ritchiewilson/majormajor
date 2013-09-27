# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from majormajor.ops.op import Op
from majormajor.changeset import Changeset


def build_changesets_from_tuples(css_data, doc):
    """
    When testing its easiest to write the desired changesets as tuples, then
    this will convert that list of tuples into a list of changesets for the
    desired doc.
    """
    css = []
    for cs_data in css_data:
        action, offset, val, deps, _id = cs_data
        deps = [doc.get_root_changeset() if dep == 'root' else dep
                for dep in deps]
        cs = Changeset(doc.get_id(), 'u1', deps)
        cs.add_op(Op(action, [], offset=offset, val=val))
        cs.set_id(_id)
        css.append(cs)
    return css


def add_switches(params, n):
    """
    When parameterizing a test, it is helpful to run all the tests one way, and
    then another. For example, running OT with branch A ordered first, then
    again with branch B ordered first. This takes a list of params, and
    multiplies it by adding every combination of n boolean switches to the
    params.
    """
    switches = [(i, n) for i in xrange(pow(2, n))]
    bool_switches = [parse_switches(s) for s in switches]
    params = [p + s for p in params for s in bool_switches]
    return params


def parse_switches(switches):
    n, total = switches
    bn = str(bin(n))[2:]
    bn = ('0' * (total - len(bn))) + bn
    return [True if x == '0' else False for x in bn]
