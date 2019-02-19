"""
:title:  CustomSimbad.py
:author:  Peter Forshay
:contact:  pforshay@stsci.edu

This code can be used to query Simbad for a given exoplanet (just need a name
string) in order to add coordinate and magnitude information.

..class::  CustomSimbad
..synopsis::  This class constructs and executes a custom query to Simbad to
              retrieve target coordinates and magnitude values.
"""

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Column, Table
from astroquery.simbad import Simbad
from decimal import Decimal
import numpy as np
import time

# --------------------


class CustomSimbad(object):
    """
    This class constructs and executes a custom query to Simbad to retrieve
    target coordinates and magnitude values.

    ..module::  _add_bmv_info
    ..synopsis::  Computes B-V figures if possible and adds these to the
                  query results.

    ..module::  _read_val
    ..synopsis::  Read a value out of the results Table.

    ..module::  get_coordinates
    ..synopsis::  Return the RA and Dec coordinates found by a Simbad query.

    ..module::  get_magnitude
    ..synopsis::  Return the flux magnitude and flux error of a given filter.
    """

    def __init__(self, targ_name):
        """
        Construct and execute a Simbad query object.

        :param targ_name:  The SIMBADNAME value for the current exoplanet.
        :type targ_name:  str
        """

        # Initialize an astroquery Simbad class object.
        simbad_info = Simbad()

        # Set up the list of filters and errors to query.
        self.filters = ['B', 'V', 'J', 'H', 'K']
        f = ['flux({0})'.format(x) for x in self.filters]
        fe = ['flux_error({0})'.format(y) for y in self.filters]
        fields = f + fe

        # Add the list of filters and errors to the fields queried.
        [simbad_info.add_votable_fields(f) for f in fields]

        # Execute the Simbad query.  self.results is now an astropy Table
        # object if valid results were returned.
        self.results = simbad_info.query_object(targ_name)

        # Convert masked values to NaN (some flux values return '--').
        for col in self.results.colnames:
            if self.results[col][0] is np.ma.masked:
                self.results[col][0] = np.nan

        # Add BMV info to the results Table.
        self._add_bmv_info()

        # Wait to avoid a Simbad IP blacklist (somewhere around 4-5
        # queries/sec)
        time.sleep(0.4)

    def _add_bmv_info(self):
        """
        Computes B-V values if possible and adds these to the query results.
        """

        # Get B and V flux values.
        b_mag, b_err = self.get_magnitude('b')
        v_mag, v_err = self.get_magnitude('v')

        # Set bmv to NaN if either B or V are unavailable.  Otherwise calculate
        # B-V.
        if (str(b_mag).lower() == 'nan' or str(v_mag).lower() == 'nan'):
            bmv = np.nan
        else:
            bmv = np.round(b_mag - v_mag, decimals=len(str(v_mag)))

        # Store the bmv results in a new astropy Column.
        bmv_col = Column(name='FLUX_BMV', data=[bmv])

        # Do the same steps for bmv errors if available.
        if (str(b_err).lower() == 'nan' or str(v_err).lower() == 'nan'):
            bmv_err = np.nan
        else:
            bmv_err = np.round(b_err + v_err, decimals=len(str(v_err)))
        bmv_err_col = Column(name='FLUX_ERROR_BMV', data=[bmv_err])

        # Add the new columns to the results Table.
        self.results.add_columns([bmv_col, bmv_err_col])

    def _read_val(self, key):
        """
        Read a value out of the results Table.

        :param key:  The field to look up.
        :type key:  str
        """

        try:
            val = self.results[key][0]
        except KeyError:
            val = None

        return val

    def get_coordinates(self):
        """
        Return the RA and Dec coordinates found by a Simbad query.
        """

        ra = self._read_val('RA')
        dec = self._read_val('DEC')

        return (ra, dec)

    def get_magnitude(self, filt):
        """
        Return the flux magnitude and flux error of a given filter.

        :param filt:  The requested filter.
        :type filt:  str
        """

        flux_str = "_".join(["FLUX", filt.upper()])
        err_str = "_".join(["FLUX_ERROR", filt.upper()])

        mag = self._read_val(flux_str)
        err = self._read_val(err_str)

        return (mag, err)
