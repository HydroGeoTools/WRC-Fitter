import numpy as np
import scipy.optimize
from scipy.interpolate import CubicSpline

###
# Model to fit
###

def VanGenuchten(psi, params):
    # https://doi.org/10.2136/sssaj1980.03615995004400050002x
    tets, a, n, tetr = params
    return tetr+((tets-tetr)/(1+(((a*psi)**n)**(1-(1/n)))))

def VanGenuchten_initial_parameters(xdata, ydata):
    # min and max water content for tets tetr
    tets = np.max(ydata)
    tetr = np.min(ydata)
    # estimate a
    #when a * psi = 1, the denominator of the fraction is between 1 and 2
    #so consider 1.5
    tetmid = (tets-tetr) / 1.5 + tetr
    tetlow = (tets-tetr) / 2 + tetr
    index = np.argmin(np.abs(ydata-tetmid))
    a = 1 / xdata[index]
    amax = 100
    index = np.argmin(np.abs(ydata-tetlow))
    amin = 1 / xdata[index]
    n = 5
    return tets, a, n, tetr, [amin/2, amax]
    

def BrooksCorey(psi, params):
    # from https://www.pc-progress.com/Documents/programs/retc.pdf
    # and https://www.nature.com/articles/s41598-019-54449-8
    tets, psi_d, l, tetr = params
    cond = np.where(psi < psi_d, 1, (psi/psi_d)**l)
    return tetr + (tets - tetr) * cond 

def BrooksCorey_initial_parameters(xdata, ydata):
    tets = np.max(ydata)
    tetr = np.min(ydata)
    index = np.argmin(ydata < 0.8 * tets)
    psi_d = xdata[index]
    l = 2
    return tets, psi_d, l, tetr


def FredlungXing(psi, params):
    # https://doi.org/10.1139/t94-061
    print(params)
    tets, a, n, m = params
    return tets * (np.log(np.e + (psi/a)**n))**(-m)

def FredlungXing_initial_parameters(xdata, ydata):
    tets = np.max(ydata)
    tetr = np.min(ydata)
    # differentiate to find the inflexion point
    #interpol = CubicSpline(np.sort(xdata),ydata)
    #grad1 = interpol.derivative(1)
    #grad2 = interpol.derivative(2)
    index = np.argmin(np.abs(ydata-(tets-tetr) * 0.7 + tetr))
    x0 = xdata[index]
    #psi_i = scipy.optimize.root_scalar(grad2, x0=x0)
    teti = ydata[index]
    psi_i = x0
    # from equation 32 to 35
    a = psi_i
    m = 3.67 * np.log(tets/teti)
    n = 1.31**(m+1) / (m * tets) * 3.72 * (-1) * psi_i
    return tets, a, n, m



###
# Error functions
###

def MSE(x, CRE_model, xdata, ydata):
    y_th = CRE_model(xdata, x)
    residual = y_th - ydata
    MSE = np.sum(residual**2)
    return MSE


###
# Main fit function
###
def fit(xdata, ydata, model="Van Genuchten"):
    tol = 0.3
    if model == "Van Genuchten":
        func = VanGenuchten
        tets, a, n, tetr, abounds = VanGenuchten_initial_parameters(xdata, ydata)
        x0 = [tets,a,n,tetr]
        bounds=[
            (tets*(1-tol),min((1+tol)*tets,1)),
            abounds,
            (1,50),
            (tetr*(1-tol),min((1+tol)*tetr,1))
        ]
    elif model == "Brooks and Corey":
        func = BrooksCorey
        tets, psi_d, l, tetr = BrooksCorey_initial_parameters(xdata, ydata)
        x0 = [tets, psi_d, l, tetr]
        bounds = [
            (tets*(1-tol),min((1+tol)*tets,1)), #tets
            (np.min(xdata), np.max(xdata)),
            (-10,0),
            (tetr*(1-tol),min((1+tol)*tetr,1)), #tetr
        ]
    elif model == "Fredlung and Xing":
        func = FredlungXing
        tets, a, n, m = FredlungXing_initial_parameters(xdata, ydata)
        x0 = [tets, a, n, m]
        bounds = [
            (tets*(1-tol),min((1+tol)*tets,1)),
            (np.min(xdata), np.max(xdata)),
            (0,30),
            (0,30),
        ]
    res = scipy.optimize.dual_annealing(MSE, bounds=bounds, args=[func, xdata, ydata], x0=x0, maxiter=1000)
    print(res)
    return res   
