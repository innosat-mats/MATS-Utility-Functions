from skyfield.framelib import itrs
from skyfield.positionlib import Geocentric, ICRF
from skyfield.units import Distance
from numpy.linalg import norm
from scipy.optimize import minimize_scalar
from skyfield.api import wgs84 
from skyfield.api import load
from skyfield.units import Distance
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import CubicSpline
from mats_l1_processing.pointing import pix_deg
import numpy as np

def funheight(s, t, pos, FOV):
    newp = pos + s * FOV
    newp = ICRF(Distance(m=newp).au, t=t, center=399)
    return wgs84.subpoint(newp).elevation.m


def findtangent(t, pos, FOV):
    res = minimize_scalar(funheight, args=(t, pos, FOV), bracket=(1e5, 3e5))
    return res


def col_heights(ccditem, x, nheights=None, spline=False):
    if nheights == None:
        nheights = ccditem['NROW']
    d = ccditem['EXP Date']
    ts = load.timescale()
    t = ts.from_datetime(d)
    ecipos = ccditem['afsGnssStateJ2000'][0:3]
    q = ccditem['afsAttitudeState']
    quat = R.from_quat(np.roll(q, -1))
    qprime = R.from_quat(ccditem['qprime'])
    ypixels = np.linspace(0, ccditem['NROW'], nheights)
    ths = np.zeros_like(ypixels)
    xdeg, ydeg = pix_deg(ccditem, x, ypixels)
    for iy, y in enumerate(ydeg):
        los = R.from_euler('XYZ', [0, y, xdeg], degrees=True).apply([1, 0, 0])
        ecivec = quat.apply(qprime.apply(los))
        ths[iy] = findtangent(t, ecipos, ecivec).fun
    if spline:
        return CubicSpline(ypixels, ths)
    else:
        return ths


def heights(ccditem):
    ths = np.zeros([ccditem['NROW'], ccditem['NCOL']+1])
    for col in range(ccditem['NCOL']+1):
        ths[ :,col] = col_heights(ccditem, col)
    return ths


def satpos(ccditem):
    """Function giving the GPS position in lat lon alt.. 

   
    Arguments:
        ccditem or dataframe with the 'afsGnssStateJ2000'

    Returns:
        satlat: latitude of satellite (degrees)
        satlon: longitude of satellite (degrees)
        satheight: Altitude in metres 
        
    """
    ecipos = ccditem['afsGnssStateJ2000'][0:3]
    d = ccditem['EXP Date']
    ts = sfapi.load.timescale()
    t = ts.from_datetime(d)
    satpos = Geocentric(position_au=Distance(
        m=ccditem['afsGnssStateJ2000'][0:3]).au, t=t)
    satlat, satlong, satheight = satpos.frame_latlon(itrs)
    return (satlat.degrees, satlong.degrees, satheight.m)