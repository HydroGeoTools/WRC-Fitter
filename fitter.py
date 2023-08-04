import numpy as np
import scipy.optimize
from scipy.interpolate import CubicSpline

###
# Model to fit
###

model_output_name = {
    "Van Genuchten (1980)": ["Saturation WC", "alpha VG", "n VG", "Residual WC"],
    "Brooks and Corey (1964)": ["Saturation WC", "Air Entry Value", "Lambda BC", "Residual WC"],
    "Fredlund and Xing (1994)": ["Saturation WC", "alpha FX", "n FX", "m FX"],
}
  
def VanGenuchten(psi, tets, a, n, tetr):
    # https://doi.org/10.2136/sssaj1980.03615995004400050002x
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
    

def BrooksCorey(psi, tets, psi_d, l, tetr):
    # from https://www.pc-progress.com/Documents/programs/retc.pdf
    # and https://www.nature.com/articles/s41598-019-54449-8
    cond = np.where(psi < psi_d, 1, (psi/psi_d)**l)
    return tetr + (tets - tetr) * cond 

def BrooksCorey_initial_parameters(xdata, ydata):
    tets = np.max(ydata)
    tetr = np.min(ydata)
    index = np.argmin(ydata < 0.8 * tets)
    psi_d = max(xdata[index],1e-6)
    l = -2
    return tets, psi_d, l, tetr


def FredlundXing(psi, tets, a, n, m):
    # https://doi.org/10.1139/t94-061
    return tets * (np.log(np.e + (psi/a)**n))**(-m)

def FredlundXing_initial_parameters(xdata, ydata):
    tets = np.max(ydata)
    tetr = np.min(ydata)
    # we found the inflexion point using a simplified procedure with sat=0.7
    index = np.argmin(np.abs(ydata-(tets-tetr) * 0.7 - tetr))
    psi_i = xdata[index]
    teti = ydata[index]
    # slope is calculated with sat=0.3 and sat=0.7
    index = np.argmin(np.abs(ydata-(tets-tetr) * 0.3 - tetr))
    psi_p = xdata[index]
    s = teti / (psi_p - psi_i)
    # from equation 32 to 35
    a = psi_i
    m = 3.67 * np.log(tets/teti)
    n = 1.31**(m+1) / (m * tets) * 3.72 * psi_i * s
    return tets, a, n, m



###
# Error functions
###

def MSE(x, CRE_model, xdata, ydata):
    y_th = CRE_model(xdata, x)
    residual = y_th - ydata
    MSE = 1 / len(xdata) * np.sum(residual**2)
    return MSE

def quantile_loss(x, model, xdata, ydata, quantile):
    y_th = model(xdata, x)
    residual = y_th - ydata
    L = np.where(residual < 0, - quantile * residual, - (quantile-1)* residual)
    return 1/len(xdata) * np.sum(L)


###
# Main fit function
###

def get_WRC_function(model="Van Genuchten (1980)"):
    if model == "Van Genuchten (1980)":
        func_l = lambda x,params: VanGenuchten(x, *params)
    elif model == "Brooks and Corey (1964)":
        func_l = lambda x,params: BrooksCorey(x, *params)
    elif model == "Fredlund and Xing (1994)":
        func_l = lambda x,params: FredlundXing(x, *params)
    return func_l

def fit(xdata, ydata, model, quantile=None):
    tol = 0.3
    if model == "Van Genuchten (1980)":
        func_l = lambda x,params: VanGenuchten(x, *params)
        tets, a, n, tetr, abounds = VanGenuchten_initial_parameters(xdata, ydata)
        x0 = [tets,a,n,tetr]
        bounds=[
            (tets*(1-tol),min((1+tol)*tets,1)),
            abounds,
            (1,50),
            (tetr*(1-tol),min((1+tol)*tetr,1))
        ]
    elif model == "Brooks and Corey (1964)":
        func_l = lambda x,params: BrooksCorey(x, *params)
        tets, psi_d, l, tetr = BrooksCorey_initial_parameters(xdata, ydata)
        x0 = [tets, psi_d, l, tetr]
        bounds = [
            (tets*(1-tol),min((1+tol)*tets,1)), #tets
            (max(np.min(xdata),1e-6), np.max(xdata)),
            (-10,0),
            (tetr*(1-tol),min((1+tol)*tetr,1)), #tetr
        ]
    elif model == "Fredlund and Xing (1994)":
        func_l = lambda x,params: FredlundXing(x, *params)
        tets, a, n, m = FredlundXing_initial_parameters(xdata, ydata)
        x0 = [tets, a, n, m]
        bounds = [
            (tets*(1-tol),min((1+tol)*tets,1)),
            (np.min(xdata), np.max(xdata)),
            (0,30),
            (0,30),
        ]
    
    if quantile is not None:
        #Make a quantile regression
        res = scipy.optimize.differential_evolution(
            quantile_loss,
            bounds=bounds,
            args=[func_l, xdata, ydata, quantile],
            x0=x0,
            maxiter=1000,
            popsize=24
        )
    else:
        #Make a best fit calibration
        res = scipy.optimize.dual_annealing(MSE, bounds=bounds, args=[func_l, xdata, ydata], x0=x0, maxiter=1000)
    return res, func_l


