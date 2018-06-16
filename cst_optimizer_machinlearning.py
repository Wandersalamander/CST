import numpy as np
import sklearn
from sklearn.ensemble import RandomForestRegressor
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
import cst_model_reader as cmr
import cst_optimizer_draft as cst_opt
import os


def read_fuckfile(path):
    '''reads this stange logfile formart

    Note
    ----
    All files in path a taken into accout
    so make sure all logfiles in this dictionary
    belong to the same cst structure

    Returns
    -------
    ndarray, ndarray
        X and Y as used in sklearn
    '''
    assert ".log" in path
    X, Y = [], []
    with open(path, "r") as file:
        for line in file.readlines():
            line = line.replace("\n", "")
            y_raw, x_raw = line.split("\t\t")
            y = float(y_raw)
            x = x_raw.replace("[", "").replace("]", "").split(" ")
            x = list(map(float, x))
            X.append(x)
            Y.append(y)
    X = np.array(X)
    Y = np.array(Y)
    return X, Y


def genXY(paths):
    '''Reads all logfiles and generates X and Y

    Returns
    -------
    ndarray, ndarray
        X and Y as used in sklearn
    '''
    Xs, Ys = [], []
    for p in paths:
        Xi, Yi = read_fuckfile(p)
        Xs.append(Xi)
        Ys.append(Yi)
    X = np.concatenate(Xs, axis=0)
    Y = np.concatenate(Ys, axis=0)
    return X, Y


class MachineLearningModel:
    '''

    Parameters
    ----------
    paths:
        paths to logfiles to be used
        for fitting the regressor
    regressor:
        initialized sklearn regressor
    '''

    def __init__(self, paths, regressor=Ridge()):
        X, Y = genXY(paths)
        self.rgsr = regressor
        self.rgsr.fit(X, Y)

    def cost(self, x):
        '''Predicts cost based on all logfiles'''
        cost = self.rgsr.predict([x])
        return np.abs(cost)  # as ´Ridge regressor can yield negative values


def suggest(path, regressor=Ridge()):
    '''Predicts a optimum

    Notes
    -----
    Refreshs all logfiles
    Refreshs Machine learner on new logfiles
    Predicts then

    Parameters
    ----------
    path: str
        path where logfiles are placed
    regressor:
        initialized sklearn regressor

    Returns
    -------
    ndarray
        x of yopt
        parameters of optimum
    '''
    if path[-1] != "/":
        path += "/"
    paths = os.listdir(path)
    paths = [path + p for p in paths if ".log" in p]
    X, Y = genXY(paths)
    x0 = X[0]
    m = MachineLearningModel(paths, regressor=regressor)
    res = minimize(m.cost, x0)
    print("deviation from mean parameters",
          (1 - res.x / np.mean(X, axis=0)) * 100)
    return res.x


def optimize(path, cost_target=1):
    '''Optimizes a cst file using machine learning

    Notes
    -----
    path should also contain all previous results
    represented in the variouse logfiles "strangenumber.log"
    '''
    assert ".cst" in path
    p1 = "/".join(path.split("/")[:-1])
    x = suggest(p1)
    cost = cst_opt.opt1(path).cost(x)
    while cost > cost_target:
        x = suggest(p1)
        cost = cst_opt.opt1(path).cost(x)
        print("COST", cost)
        print("\n" * 3)
    return x


if __name__ == "__main__":
    # path to file to be optimized
    path = "C:/Users/Simon/Desktop/JANOPT/IH_7b_7Gaps.cst"
    # this path should also contain all previous results
    # represented in the variouse logfiles "strangenumber.log"
    optimize(path)
