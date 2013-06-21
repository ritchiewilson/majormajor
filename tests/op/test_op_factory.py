"""
Testing operational transformation with each combination of
possible opperations.
"""

from majormajor.op import *
from majormajor.changeset import Changeset

class TestOT:

    def test_inheritance(self):
        si_op = Op('si', [], offset=3, val="ABC")
        assert isinstance(si_op, Op)
        assert isinstance(si_op, StringInsertOp)

        sd_op = Op('sd', [], offset=3, val=2)
        assert isinstance(sd_op, Op)
        assert isinstance(sd_op, StringDeleteOp)
        assert not isinstance(sd_op, StringInsertOp)

        set_op = Op('set', [], val="ABC")
        assert isinstance(set_op, Op)
        assert isinstance(set_op, SetOp)
        assert not isinstance(set_op, StringDeleteOp)
        assert not isinstance(set_op, StringInsertOp)
