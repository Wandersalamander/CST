import functions as f
from cst_optimizer_machinlearning import genXY
import sklearn
from matplotlib import pyplot as plt
from scipy.optimize import minimize
import pyswarm
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression
path = "C:/Users/Simon/Desktop/JANOPT/"
files = f.get_files(path, ".log")
X, Y = genXY(files)
print("best cost in data", np.min(Y), "\n")
X, Y = X[Y < 23], Y[Y < 23]

# rgsr = MLPRegressor(hidden_layer_sizes=x,
#                     learning_rate_init=1e-1,
#                     early_stopping=True,
#                     momentum=.99)
rgsrs = [
    make_pipeline(PolynomialFeatures(2), sklearn.linear_model.Ridge()),
    sklearn.linear_model.LassoLars(),
    sklearn.linear_model.BayesianRidge(),
    sklearn.linear_model.Lasso(),
    sklearn.linear_model.Ridge(),
    sklearn.linear_model.ElasticNet(),
    sklearn.svm.SVR(),
    sklearn.ensemble.RandomForestRegressor(),
    sklearn.ensemble.AdaBoostRegressor(
        sklearn.ensemble.RandomForestRegressor()),
    sklearn.linear_model.SGDRegressor(),
    GaussianProcessRegressor(),
    # IsotonicRegression(),
    GradientBoostingRegressor(),
    MLPRegressor(),
    sklearn.ensemble.AdaBoostRegressor(sklearn.svm.SVR()),
    sklearn.ensemble.AdaBoostRegressor(sklearn.svm.SVR(C=5)),
    sklearn.ensemble.AdaBoostRegressor(sklearn.linear_model.Ridge()),
    sklearn.ensemble.AdaBoostRegressor(sklearn.linear_model.Lasso()),
    sklearn.ensemble.AdaBoostRegressor(sklearn.linear_model.ElasticNet()),
]
for rgsr in rgsrs:
    # rgsr.fit(X, Y, 1/ Y)
    # score = rgsr.score(X, Y, 1 / Y)
    print(str(rgsr)[:str(rgsr).index("(")])
    score = cross_val_score(rgsr, X, Y, scoring="neg_mean_absolute_error")
    print("Regressor Score", np.mean(score))
    print()

def cost(x):
    C, epsilon, n_estimators, degree = x
    n_estimators = int(n_estimators)
    degree = int(degree)

    rgsr = sklearn.ensemble.AdaBoostRegressor(
        sklearn.svm.SVR(C=C, epsilon=epsilon, degree=degree),
        n_estimators=n_estimators
    )
    cost = -cross_val_score(rgsr, X, Y, scoring="explained_variance")
    cost = np.mean(cost)
    if -cost > 0.01:
        print("score", -cost)
    return cost


# xopt, fopt = pyswarm.pso(cost, lb=[1e-12, 0, 1, 1], ub=[100, 100, 100, 100], swarmsize=10, maxiter=100)
# print(xopt, fopt)

C, epsilon, n_estimators, degree = [59.73595138, 40.37750171, 1., 63.24630029]
n_estimators = int(n_estimators)
degree = int(degree)
rgsr = sklearn.ensemble.AdaBoostRegressor(
    sklearn.svm.SVR(C=C, epsilon=epsilon, degree=degree),
    n_estimators=n_estimators
)
rgsr.fit(X, Y)
scr = rgsr.score(X, Y)
print("regressor score", scr)
# scr = rgsr.score(X, Y, 1 / Y, scoring="neg_mean_absolute_error")
# print("regressor abs error", scr)

def show_data():
    print(X.shape, Y.shape)
    pars_n = X.shape[1]
    for i in range(pars_n):
        plt.subplot(pars_n, 1, i + 1)
        plt.plot(X[:, i], Y, "o")
    plt.show()
