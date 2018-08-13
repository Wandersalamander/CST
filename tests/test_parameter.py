import unittest
import os
import shutil
from pycst import pycst
# import numpy as np
# import pandas as pd


def testfilepath():
    p = os.path.abspath(__file__)
    p = os.path.dirname(p)
    file = os.path.join(p, "testfile", "test.cst")
    if not os.path.isfile(file):
        raise FileNotFoundError(file)
    return file


class tests(unittest.TestCase):
    file = testfilepath()
    folder = os.path.join(os.path.dirname(file), "test")

    def test_nofolder(self):
        shutil.rmtree(tests.folder)
        self.assertFalse(os.path.exists(tests.folder))
        pycst.CstModel(tests.file)
        self.assertTrue(os.path.exists(tests.folder))

    def test_no_parameters(self):
        model = pycst.CstModel(tests.file)
        pars = model.get_parameters()
        self.assertEqual(len(pars), 0)

    # def test_write_parameters(self):
    #     model = pycst.CstModel(tests.file)
    #     parameter_name = "test1"
    #     parameter_value = 13
    #     model.add_parameters({parameter_name: parameter_value})
    #     pars = model.get_parameters()
    #     self.assertEqual(pars[parameter_name], parameter_value)


if __name__ == "__main__":
    unittest.main()
