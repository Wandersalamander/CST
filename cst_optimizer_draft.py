import sys
from multiprocessing import Pool
import os
import time
from matplotlib import pyplot as plt
import argparse
from scipy.optimize import minimize
from shutil import copyfile, copytree, rmtree
import numpy as np
# cst model reader path here
sys.path.append("C:/Users/Simon/Documents/CST")
import cst_model_reader as cmr
from cst_model_reader_config import config
import json
import functions as funcs

# def persist_to_file(file_name):

#     def decorator(original_func):

#         try:
#             cache = json.load(open(file_name, 'r'))
#         except (IOError, ValueError):
#             cache = {}

#         def new_func(*args, **kwargs):
#             key = args + tuple(sorted(kwargs.items()))
#             if key not in cache:
#                 cache[key] = original_func(*args, **kwargs)
#                 json.dump(cache, open(file_name, 'w'))
#             return cache[key]

#         return new_func

#     return decorator


class monitor():
    '''shall display changes in parameters and cost function'''
    num = 0

    def __init__(self, ylabels):
        plt.figure(monitor.num)
        monitor.num += 1
        plt.ion()
        plt.show()
        self.x = 0
        for i, ylabel in enumerate(ylabels):
            plt.subplot(len(ylabels), 1, i + 1)
            plt.ylabel(ylabel)
            plt.xlabel("run")
            plt.draw()
            plt.pause(0.1)

    def plot(self, ys):
        for i, y in enumerate(ys):
            plt.subplot(len(ys), 1, i + 1)
            plt.semilogy(self.x, y, "o", c="C%d" % i)
            plt.draw()
            plt.pause(0.1)
        self.x += 1


class opt1:
    '''optimizes tuner and everything'''

    def __init__(self, path: str):
        self.path = path
        self.xopt = None
        self.fopt = np.inf
        self.PARAMS = [
            "sp_Shell_height",
            "sp_Shell_width",
            "sp_Tuner_Beam_dist_at0",
            "sp_Tuner_x",
            "sp_Tuner_y",
            "sp_Undercut",
        ]
        # self.monitor0 = monitor(["cost"] + self.PARAMS)
        assert path[-4:] == ".cst"
        self.files = [
            path,
            path.replace(".cst", "tnr-40.cst"),
            path.replace(".cst", "tnr+40.cst"),
        ]
        _par = [
            -40,
            +40,
        ]
        for i, file in enumerate(self.files[1:]):
            copyfile(path, file)
            copytree(path[:-4], file[:-4])
            m2 = cmr.CST_Model(file, autoanswer="n")
            m2.editParam("sp_Tuner", _par[i])
            del m2  # deletes python-object, not file

    def __str__(self):
        return "Opt1 " + self.path

    def __del__(self):
        for i, file in enumerate(self.files[1:]):
            os.remove(file)
            rmtree(file[:-4])

    def run(self):
        '''starts minimizer'''
        def gen_x0():
            x0 = []
            with cmr.CST_Model(self.files[0], autoanswer="n") as model:
                for par in self.PARAMS:
                    x0.append(model.getParam(par)[2])
            return x0

        def gen_simplex():
            _path = "/".join(self.path.split("/")[:-1]) + "/"
            paths = os.listdir(_path)
            paths = [_path + p for p in paths if ".log" in p]
            X, Y = funcs.genXY(paths)
            arr1inds = Y.argsort()
            X_sorted = X[arr1inds, :]
            initial_simplex = X_sorted[:X_sorted.shape[1] + 1, :]
            return initial_simplex

        x0 = gen_x0()
        assert len(x0) == len(self.PARAMS)
        try:
            initial_simplex = gen_simplex()
            res = minimize(self.cost, x0, method="Nelder-Mead",
                           options={"initial_simplex": initial_simplex})
            print(res.x)
            print(self.xopt)
            self.xopt = res.x
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        print("best parameters", self.xopt)
        with cmr.CST_Model(self.files[0]) as model:
            for i, par in enumerate(self.PARAMS):
                model.editParam(par, self.xopt[i])

    def cost(self, x: np.ndarray):
        def value(file: str, pattern: str):
            '''searches for result matching your pattern'''
            result_tmp = []
            ress = results[file]
            for name, val in ress:
                if pattern == name and len(pattern) == len(name):
                    result_tmp.append(val)
            if len(result_tmp) != 1:
                print(result_tmp, pattern)
                raise Exception(
                    "Pattern matches multible results\nPattern:%s\nAvailable Results:%s"
                    % (pattern, ress))
            return result_tmp[0]

        def compute_cost(self):
            costs = []

            tunerhub = abs(value(self.files[1], "Frequency (Mode 1)") -
                           value(self.files[2], "Frequency (Mode 1)"))
            target = 1
            weight = 1
            costs.append(abs((tunerhub - target) * weight))

            frequency0 = value(self.files[0], "Frequency (Mode 1)")
            target = 108.408
            weight = 10
            costs.append(abs((frequency0 - target) * weight))

            frequency01 = abs(value(self.files[0], "Frequency (Mode 1)") -
                              value(self.files[0], "Frequency (Mode 2)"))
            target = 5
            weight = 10
            if frequency01 < target:
                costs.append(abs((frequency01 - target) * weight))
            else:
                costs.append(0)

            U_deviation_mean = abs(value(self.files[0], "U_deviation_mean"))
            target = 0
            weight = 100
            costs.append(abs((U_deviation_mean - target) * weight))

            U_deviation_mean_max = max(
                abs(value(self.files[0], "U_deviation_mean")),
                abs(value(self.files[1], "U_deviation_mean")),
                abs(value(self.files[2], "U_deviation_mean")),
            )
            target = 0.1
            weight = 10 * 100
            if U_deviation_mean_max > target:
                costs.append(abs((U_deviation_mean_max - target) * weight))
            else:
                costs.append(0)

            # "U_deviation Gap",
            for i in range(12):
                U_deviation_G = abs(
                    value(self.files[0], "U_deviation Gap%d" % (i + 1)))
                target = 0.05
                weight = 100
                if U_deviation_G > target:
                    costs.append(abs((U_deviation_G - target) * weight))
                else:
                    costs.append(0)
            # "delta_mean",
            # for i in range(12):
            #     delta_mean = abs(value(self.files[0], "delta_mean"))
            #     target = 0.05
            #     weight = 1
            #     if delta_mean > target:
            #         costs.abs(append((delta_mean - target) * weight))

            # "Tuner_min_pos",
            Tuner_min_pos = abs(value(self.files[0], "Tuner_min_pos_%"))
            target = 80
            weight = 1
            if Tuner_min_pos > target:
                costs.append(abs((Tuner_min_pos - target) * weight))
            else:
                costs.append(0)

            # "Mode_Indicator",
            Mode_Indicator = abs(value(self.files[0], "Mode_Indicator"))
            target = 6
            weight = 1
            if Mode_Indicator < target:
                costs.append(abs((Mode_Indicator - target) * weight))
            else:
                costs.append(0)

            # "P_ges_plus10%_plus20%",
            P_ges = abs(value(self.files[0], "P_ges_plus10%_plus20%"))
            target = 6
            weight = 1
            if P_ges < target:
                costs.append(abs((P_ges - target) * weight))
            else:
                costs.append(0)
            # self.monitor0.plot([np.sum(costs)] + list(x))
            print("cost:", np.sum(costs), list(costs))
            return np.sum(costs)

        WANTEDRESULTS = [
            "U_deviation_mean",
            "Frequency (Mode 1)",
            "Frequency (Mode 2)",
            "U_deviation Gap",
            "delta_mean",
            "Tuner_min_pos_%",
            "Mode_Indicator",
            "P_ges_plus10%_plus20%",
        ]
        p = Pool(3)
        try:
            argss = [{
                "x": x,
                "PATH": f,
                "PARAMS": self.PARAMS,
                "WANTEDRESULTS": WANTEDRESULTS
            } for f in self.files]
            print("pooling")
            results = p.map(gen_results, argss)
            p.close()
            print("end pooling")
            results = dict(zip(self.files, results))
            cost = compute_cost(self)
            if self.fopt > cost:
                self.fopt = cost
                self.xopt = x
            print("writing cost")
            p = self.path.replace("\\", "/")
            p = p.split("/")[:-1]
            p = "/".join(p) + "/"
            with open(p + "%s.log" % str(hash(self.files[0])), "a") as objf:
                objf.write(str(cost) + "\t\t" +
                           "[" + " ".join(str(xi) for xi in x) + "]\n")
            return cost
        except KeyboardInterrupt:
            p.terminate()


class opt2:
    '''optimizes frequenzy'''

    def __init__(self, path: str):
        self.xopt = None
        self.fopt = np.inf
        self.PARAMS = [
            "sp_Shell_height",
            "sp_Shell_width",
        ]
        self.monitor0 = monitor(["cost"] + self.PARAMS)
        assert path[-4:] == ".cst"
        self.files = [
            path,
        ]

    def __del__(self):
        pass

    def run(self):
        '''starts minimizer'''
        def gen_x0():
            x0 = []
            with cmr.CST_Model(self.files[0], autoanswer="n") as model:
                for par in self.PARAMS:
                    x0.append(model.getParam(par)[2])
            return x0
        x0 = gen_x0()
        assert len(x0) == len(self.PARAMS)
        try:
            res = minimize(self.cost, x0)
            print(res.x)
            print(self.xopt)
            self.xopt = res.x
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        print("best parameters", self.xopt)
        with cmr.CST_Model(self.files[0]) as model:
            for i, par in enumerate(self.PARAMS):
                model.editParam(par, self.xopt[i])

    def cost(self, x: np.ndarray):
        def value(file: str, pattern: str):
            '''searches for result matching your pattern'''
            result_tmp = []
            ress = results[file]
            for name, val in ress:
                if pattern == name and len(pattern) == len(name):
                    result_tmp.append(val)
            if len(result_tmp) != 1:
                print(result_tmp, pattern)
                raise Exception(
                    "Pattern matches multible results\nPattern:%s\nAvailable Results:%s"
                    % (pattern, ress))
            return result_tmp[0]

        def compute_cost(self):
            costs = []

            frequency0 = value(self.files[0], "Frequency (Mode 1)")
            target = 108.408
            weight = 100
            costs.append(abs((frequency0 - target) * weight))

            U_deviation_mean = abs(value(self.files[0], "U_deviation_mean"))
            target = 0
            weight = 1
            costs.append(abs((U_deviation_mean - target) * weight))

            # "U_deviation Gap",
            for i in range(12):
                U_deviation_G = abs(
                    value(self.files[0], "U_deviation Gap%d" % (i + 1)))
                target = 0.05
                weight = 1
                if U_deviation_G > target:
                    costs.append(abs((U_deviation_G - target) * weight))
                else:
                    costs.append(0)
            return np.sum(costs)

        WANTEDRESULTS = [
            "U_deviation_mean",
            "Frequency (Mode 1)",
            "U_deviation Gap",
        ]
        argss = [{
            "x": x,
            "PATH": f,
            "PARAMS": self.PARAMS,
            "WANTEDRESULTS": WANTEDRESULTS
        } for f in self.files]
        results = [gen_results(argss[0])]
        results = dict(zip(self.files, results))
        cost = compute_cost(self)
        if self.fopt > cost:
            self.fopt = cost
            self.xopt = x
        return cost


def gen_results(keywordarguments: dict):
    '''collects results'''
    def match(itm: str, lst: list):
        '''checks if itm is contained in substrings of lst'''
        itm = itm.lower()
        lst = [l.lower() for l in lst]
        for l in lst:
            if l in itm:
                return True
        return False

    x = keywordarguments["x"]  # this is the input vector from scipy minimizer
    PATH = keywordarguments["PATH"]
    PARAMS = keywordarguments["PARAMS"]
    WANTEDRESULTS = keywordarguments["WANTEDRESULTS"]
    model = cmr.CST_Model(PATH, autoanswer="n")
    for i, parname in enumerate(PARAMS):
        model.editParam(parname, x[i])
    model.cst_rebuild()
    returncode = model.cst_run_eigenmode()
    iteration = 0
    while returncode != 0:
        print("Eigenmode computation failed\nRetry", iteration)
        model.cst_run_eigenmode(timeout=30 * 60)
        time.sleep(60 * 5)
        iteration += 1
        if iteration == 6:
            break
    resultnames = model.getResultNames()
    resultnames = [_x for _x in resultnames if match(_x, WANTEDRESULTS)]
    results = []
    for resname in resultnames:
        results.append([resname, model.getResult(resname)])
    return results


# if __name__ == "__main__":
#     paths = ["C:/Users/Simon/Desktop/Optimizer-test/optf0test.cst"]
#     for path in paths:
#         opt2(path).run()
