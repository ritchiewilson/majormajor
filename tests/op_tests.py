from op import Op
from changeset import Changeset
import unittest


class TestOT(unittest.TestCase):

    def setUp(self):
        pass

    def test_si_si(self):
        op1 = Op('si', [], offset=3, val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # op2 happens at a lower offset, so should not be affected
        op2 = Op('si', [], offset=2, val="XYZ")
        op2.ot(cs1)
        self.assertEqual(op2.t_offset, 2)

        # op3 happens at an equal offset, so should be pushed forward
        op2 = Op('si', [], offset=3, val="XYZ")
        op2.ot(cs1)
        self.assertEqual(op2.t_offset, 6)

        # op4 happens at a later offset, so should be pushed forward
        op2 = Op('si', [], offset=5, val="XYZ")
        op2.ot(cs1)
        self.assertEqual(op2.t_offset, 8)
        

    def test_si_sd(self):
        op1 = Op('si', [], offset=3, val="ABC")
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # insertion was at a later index than this delete. No change
        op2 = Op('sd', [], offset=0, val=3)
        op2.ot(cs1)
        self.assertEqual(op2.t_offset, 0)
        self.assertEqual(op2.t_val, 3)

        # this deletion should expand to delete inserted text as well.
        op3 = Op('sd', [], offset=2, val=2)
        op3.ot(cs1)
        self.assertEqual(op3.t_offset, 2)
        self.assertEqual(op3.t_val, 5)

        # edge case, don't delete text if don't have have to. Shift
        # delete range.
        op4 = Op('sd', [], offset=3, val=2)
        op4.ot(cs1)
        self.assertEqual(op4.t_offset, 6)
        self.assertEqual(op4.t_val, 2)

        # insertion was at lower index. shift delete range forward.
        op5 = Op('sd', [], offset=4, val=2)
        op5.ot(cs1)
        self.assertEqual(op5.t_offset, 7)
        self.assertEqual(op5.t_val, 2)
        
    def test_sd_sd(self):
        op1 = Op('sd', [], offset=3, val=3)
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)
        

        # op1 deletes a range after op2, so should not affect it
        op2 = Op('sd', [], offset=1, val=2)
        op2.ot(cs1)
        self.assertEqual(op2.t_offset, 1)
        self.assertEqual(op2.t_val, 2)

        # The end of op3 overlaps the start of op 1
        op3 = Op('sd', [], offset=2, val=2)
        op3.ot(cs1)
        self.assertEqual(op3.t_offset, 2)
        self.assertEqual(op3.t_val, 1)

        # op1 range is encompased by op 4 range
        op4 = Op('sd', [], offset=2, val=6)
        op4.ot(cs1)
        self.assertEqual(op4.t_offset, 2)
        self.assertEqual(op4.t_val, 3)

        # op5 range is encompased by op1 range
        op5 = Op('sd', [], offset=4, val=2)
        op5.ot(cs1)
        self.assertEqual(op5.t_offset, 3)
        self.assertEqual(op5.t_val, 0)

        # start of op6 range overlaps end of op1 range
        op6 = Op('sd', [], offset=5, val=3)
        op6.ot(cs1)
        self.assertEqual(op6.t_offset, 3)
        self.assertEqual(op6.t_val, 2)

        # start of op7 range is after start of op1 range
        op7 = Op('sd', [], offset=8, val=3)
        op7.ot(cs1)
        self.assertEqual(op7.t_offset, 5)
        self.assertEqual(op7.t_val, 3)


    def test_sd_si(self):
        op1 = Op('sd', [], offset=3, val=3)
        cs1 = Changeset('doc_id', 'author', [])
        cs1.add_op(op1)

        # delete range has greater index than this insert. Do nothing
        op2 = Op('si', [], offset=2, val="ABC")
        op2.ot(cs1)
        self.assertEqual(op2.t_offset, 2)
        self.assertEqual(op2.t_val, "ABC")

        # edge case. avoid deleting
        op3 = Op('si', [], offset=3, val="ABC")
        op3.ot(cs1)
        self.assertEqual(op3.t_offset, 3)
        self.assertEqual(op3.t_val, "ABC")

        # text was put into delete range, so get rid of it.
        op4 = Op('si', [], offset=4, val="ABC")
        op4.ot(cs1)
        self.assertEqual(op4.t_offset, 3)
        self.assertEqual(op4.t_val, "")

        # text is at edge after delete range
        op5 = Op('si', [], offset=6, val="ABC")
        op5.ot(cs1)
        self.assertEqual(op5.t_offset, 3)
        self.assertEqual(op5.t_val, "ABC")
        

if __name__ == '__main__':
    unittest.main()

