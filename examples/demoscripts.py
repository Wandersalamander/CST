from multiprocessing import pool
import sys
sys.path.append("C:\\Users\\Simon\\Documents\\CST")
# print(sys.path)
from pycst import pycst


def collapsedict(dct: dict, i: int):
    '''selects key:value[i] for all keys'''
    res = {}
    for key in dct.keys():
        res[key] = dct[key][i]
    return res


def show_params():
    model = pycst.CstModel(
        "C:/Users/Simon/Desktop/Test2018/testfile2018.cst", autoanswer="n")
    params = model.get_parameters()
    for par in params:
        print(par, params[par])


def sweep():
    model = pycst.CstModel(
        "C:/Users/Simon/Desktop/Test2018/testfile2018.cst",
        autoanswer="n")

    sweep_dict = {"sp_Tuner": [66, 77, 88],
                  "sp_Shell_height": [777, 888, 999]
                  }

    for i in range(3):
        dct_tmp = collapsedict(sweep_dict, i)
        model.edit_parameters(dct_tmp)
        for key in sweep_dict:
            print(key, model.get_parameters()[key])
        # model.cst_run_eigenmode()
        print()


def sweep_parallel():
    # this can also be automated
    p0 = "C:/Users/Simon/Desktop/Test2018/file1.cst"
    p1 = "C:/Users/Simon/Desktop/Test2018/file2.cst"
    p2 = "C:/Users/Simon/Desktop/Test2018/file3.cst"
    files = [p0, p1, p2]
    p = pool(len(files))
    p.map(do_something, files)
    return


def do_something(path: str):
    model = pycst.CstModel(path)
    model.csv_name = "ThreeFileResults.csv"
    if "file0" in path:
        sweep_dict = {
            "sp_Tuner": 11,
            "sp_Shell_height": 10,
        }
    elif "file1" in path:
        sweep_dict = {
            "sp_Tuner": 20,
            "sp_Shell_height": 10,
        }
    elif "file2" in path:
        sweep_dict = {
            "sp_Tuner": 55,
            "sp_Shell_height": 10,
        }
    model.edit_parameters(sweep_dict)
    model.cst_run_eigenmode()

# show_params()

sweep()