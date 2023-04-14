import numpy as np
import scipy.optimize
import pandas as pd

def VanGenuchten(psi, tets, a, n, tetr):
    return tetr+((tets-tetr)/(1+(((a*psi)**n)**(1-(1/n)))))

def RMSE(x, CRE_model, xdata, ydata):
    y_th = CRE_model(xdata, *x)
    residual = y_th - ydata
    RMSE = np.sum(np.sqrt(residual**2))
    return RMSE

def VanGenuchten_initial_parameters(xdata, ydata):
    # min and max water content for tets tetr
    tets = np.max(ydata)
    tetr = np.min(ydata)
    # estimate a
    #when a * psi = 1, the denominator of the fraction is between 1.4 and 2
    #so consider 1.7
    tetmid = (tets - tetr / 1.7)
    index = np.argmin(np.abs(ydata-tetmid))
    a = 1 / xdata[index]
    
    #dy = np.gradient(ydata, xdata)
    #plt.plot(xdata, dy)
    #plt.show()
    
    n = 5
    return tets, a, n, tetr

def fit(xdata, ydata):
    func = VanGenuchten
    tets, a, n, tetr = VanGenuchten_initial_parameters(xdata, ydata)
    tol = 0.3
    bounds=[(tets*(1-tol),min((1+tol)*tets,1)), (0,100), (1,50), (tetr*(1-tol),min((1+tol)*tetr,1))]
    res = scipy.optimize.dual_annealing(RMSE, bounds=bounds, args=[func, xdata, ydata])
    print(res)
    return res   


