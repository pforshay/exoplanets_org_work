from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Column, Table
from astroquery.simbad import Simbad
from decimal import Decimal
import numpy as np
import time


class CustomSimbad(object):

    def __init__(self, targ_name):

        simbad_info = Simbad()
        self.filters = ['B', 'V', 'J', 'H', 'K']
        f = ['flux({0})'.format(x) for x in self.filters]
        fe = ['flux_error({0})'.format(y) for y in self.filters]
        fields = f + fe
        [simbad_info.add_votable_fields(f) for f in fields]
        self.results = simbad_info.query_object(targ_name)
        for col in self.results.colnames:
            if self.results[col][0] is np.ma.masked:
                self.results[col][0] = np.nan

    def add_bmv_info(self):

        b = self.results['FLUX_B'][0]
        v = self.results['FLUX_V'][0]
        if (str(b).lower() == 'nan' or str(v).lower() == 'nan'):
            bmv = np.nan
        else:
            bmv = np.round(b - v, decimals=len(str(v)))
        bmv_col = Column(name='FLUX_BMV', data=[bmv])
        b_err = self.results['FLUX_ERROR_B'][0]
        v_err = self.results['FLUX_ERROR_V'][0]
        if (str(b_err).lower() == 'nan' or str(v_err).lower() == 'nan'):
            bmv_err = np.nan
        else:
            bmv_err = np.round(b_err + v_err, decimals=len(str(v_err)))
        bmv_err_col = Column(name='FLUX_ERROR_BMV', data=[bmv_err])
        self.results.add_columns([bmv_col, bmv_err_col])


def add_mag_fluxes(xplanet, results, filt):

    filt_name = ('ks' if filt.lower() == 'k' else filt.lower())
    mag = getattr(xplanet, filt_name)
    val = results['FLUX_{0}'.format(filt)][0]
    if isinstance(val, str):
        results['FLUX_{0}'.format(filt)][0] = np.nan
    else:
        mag.value = val
        unc = results['FLUX_ERROR_{0}'.format(filt)][0]
        if isinstance(unc, str):
            results['FLUX_ERROR_{0}'.format(filt)][0] = np.nan
        else:
            mag.uncertainty = unc
    setattr(xplanet, filt_name, mag)


def add_ra_dec(xplanet, results):

    ra = results['RA'][0]
    dec = results['DEC'][0]
    xplanet.ra_string.value = ra
    xplanet.dec_string.value = dec
    coord = SkyCoord(" ".join([ra, dec]), unit=(u.hourangle, u.deg))
    xplanet.ra.value = round(Decimal(coord.ra.hour), 8)
    xplanet.dec.value = round(Decimal(coord.dec.degree), 8)
    xplanet.coordref.value = "Simbad"
    url = "http://simbad.u-strasbg.fr/simbad/sim-basic?ident={0}".format(
        xplanet.simbadname.value.replace(" ", "+"))
    xplanet.coordurl.value = url


def add_simbad_info(xplanet):

    query = CustomSimbad(xplanet.simbadname.value)
    if not query.results:
        print("!!!Simbad query failed for {0}!!!".format(xplanet.name.value))
    elif len(query.results) == 1:
        query.add_bmv_info()
        filters = query.filters
        filters.remove('B')
        filters.append('BMV')
        for filt in filters:
            add_mag_fluxes(xplanet, query.results, filt)
        add_ra_dec(xplanet, query.results)
    time.sleep(0.5)
    return xplanet
