import numpy as np
import sys
import scipy as sp
import time
from scipy.optimize import minimize
import sys
sys.path.append("C:/Users/Simon/Documents/CST")
import cst_model_reader as cmr
import copy


class optimizer():
    def __init__(self, path):
        if path[-3:] != "cst":
            raise Exception("path does not end on .cst")
        # assert path[-3:] == "cst"
        self.path = path.replace("\\", "/")
        self.variables = []  # list of strings
        self.goals = goals()
        self.goals_set = False
        self.variables_set = False
        self.cst_model = cmr.CST_Model(path)
        self.dc = None  # distributet computing

    def set_variable(self, var):
        if isinstance(var, str):
            self.variables.append(var)
        elif isinstance(var, list):
            for itm in var:
                assert isinstance(itm, str)
                self.variables.append(itm)
        else:
            raise TypeError("var must be list or str")
        self.variables_set = True

    def set_goal(self, name, operator, target, weight=1.0):
        self.goals.add(name=name, operator=operator, target=target, weight=1.0)
        self.goals_set = True
        pass

    def start_minimizer(self):
        if not self.goals_set:
            raise Exception("use set_goal first")
        if not self.variables_set:
            raise Exception("use set_variable first")
        # initialize x0 with the current parameters
        x0 = []
        for i, Paramname in enumerate(self.variables):
            triple = self.cst_model.getParam(Paramname)
            x0.append(triple[2])
        # start minimization
        minimize(self.cost_jac, x0, method="Newton-CG", jac=True)

    def set_solver_server(self, ip, port):
        '''use this to activate distributed computing'''
        self.dc = str(ip) + ":" + str(port)

    def cost_jac(self, x, delta=1e-12):
        ''' x: input vectior
            delta: float, difference to compute
                   jacoby matrix numerically

            return:s float, numpy array, this is
                     the cost funtion and the jacoby martix'''
        jac = []
        cost = self.__cost(x)
        for i, val in enumerate(x):
            x_delta = copy.deepcopy(x)
            x_delta[i] = x_delta[i] + delta
            cost_delta = self.__cost(x_delta)
            derivate = (cost_delta - cost) / delta
            jac.append(derivate)
        print("parameter\t", x)
        print("cost and jacobian", cost, np.array(jac))
        return cost, np.array(jac)

    def __cost(self, x):
        ''' x: vector

            returns float, cost-value'''
        t0 = time.time()
        # x[i] corresponds to self.variables[i]
        # here x variables are applied to the cst model
        for i, Paramname in enumerate(self.variables):
            value = x[i]
            self.cst_model.editParam(Paramname, value, method="scary")
        # rebuild, that the parameter changes take effect
        self.cst_model.cst_rebuild()
        # run solver to generate results
        self.cst_model.cst_run_eigenmode(dc=self.dc)
        # reinitiallize to obtain current parameter and results
        self.cst_model = cmr.CST_Model(path)
        # computing the cost function
        cost = 0
        for goal in self.goals.get():
            name = goal[0]
            operator = goal[1]
            target = goal[2]
            weight = goal[3]
            current_value = self.cst_model.getResult(name)
            if operator == ">":
                if current_value < target:
                    cost += weight * abs(current_value - target)
            elif operator == "<":
                if current_value > target:
                    cost += weight * abs(current_value - target)
            elif operator == "=":
                cost += weight * abs(current_value - target)
            else:
                pass
        # print("cost \t", cost)
        print("\truntime cost \t", (time.time() - t0) // 60, "min.")
        print()
        return cost


class goals():
    memory = []
    operators = [">", "<", "="]

    def add(self, name, operator, target, weight=1.0):
        assert operator in goals.operators
        assert isinstance(target, float)
        assert isinstance(weight, float)
        assert weight > 0
        goals.memory.append([name, operator, target, weight])

    def get(self):
        return goals.memory


path = "C:/Users/Simon/Desktop/PyOpt/IH_8a_7Gaps.cst"
opt = optimizer(path)
opt.set_variable([
    "sp_Shell_width",
    "sp_Shell_height",
])

opt.set_goal(name="Frequency (Mode 1)", operator="=", target=108.408)

opt.set_solver_server("141.2.245.144", "36000")
opt.start_minimizer()
