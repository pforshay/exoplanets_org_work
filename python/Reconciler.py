"""
:title:  Reconciler.py
:author:  Peter Forshay
:contact:  pforshay@stsci.edu

This code is intended to replicate the IDL reconciler code from exoplanets.org
in Python.  This includes classes and functions for finalizing exoplanet files
(.pln files especially) and routines for executing these functions on batches
of files.

..class::  Reconciler
..synopsis::  This is a subclass of ExoPlanet that provides additional methods
              specifically for running final checks, updates, and
              calculations before writing a final .pln file.

..class::  ReconcilerSession
..synopsis::  This class defines commonly-desired routines to run during
              finalization of sets of .pln files.  This includes a decorator
              class to loop through multiple pln files and a recipe for
              Reconciler methods to execute before writing a .pln file.
"""

from bin.add_nasa_data import add_nasa_data
from lib.CustomNASA import CustomNASA
from lib.CustomSimbad import CustomSimbad
from astropy import units as u
from astropy.coordinates import SkyCoord
import csv
from decimal import Decimal
from Exoplanet import ExoParameter, ExoPlanet
from bin.is_empty import is_empty, is_valid
import json
import math
import numpy as np
import os
import pandas as pd
from scrape_nasa import read_nasa_data
import time

# --------------------


class Reconciler(ExoPlanet):
    """
    Create an ExoPlanet subclass with special methods for running final checks,
    updates, and calculations before writing a final .pln file.

    ..module::  _add_simbad_coords
    ..synopsis::  Add RA and Dec information from a Simbad query to an
                  ExoPlanet object.

    ..module::  _add_simbad_mags
    ..synopsis::  Add a number of flux magnitude values from a Simbad query to
                  an ExoPlanet object.

    ..module::  _calculate_rhostar
    ..synopsis::  If needed, calculate RHOSTAR using MSTAR and RSTAR if
                  available.

    ..module::  _calculate_t0_from_m0
    ..synopsis::  Use M0, PER, and REFTIME to calculate T0.

    ..module::  _calculate_t0_from_tt
    ..synopsis::  Use PER, TT, and OM to calculate T0.

    ..module::  _check_ar
    ..synopsis::  If the AR value is empty, clear the reference & url
                  parameters.

    ..module::  _check_dist_par
    ..synopsis::  If both DIST and PAR are provided, clear DIST to be
                  calculated from PAR.

    ..module::  _fix_coord_strings
    ..synopsis::  Make sure RA_STRING and DEC_STRING are using spaces and not
                  colons.

    ..module::  _remove_bin_refs
    ..synopsis::  Remove reference info from BINARY if it is not set.

    ..module::  _remove_et_al
    ..synopsis::  Remove 'et al.' from any reference strings.

    ..module::  _remove_lint
    ..synopsis::  Remove a few last fields.

    ..module::  add_simbad_info
    ..synopsis::  Query Simbad for coordinates and magnitude values of the
                  current exoplanet, then add the results to the ExoPlanet
                  object.

    ..module::  apply_pln_recipe
    ..synopsis::  Construct a recipe for finalizing an ExoPlanet before
                  writing a final .pln file.

    ..module::  check_t0
    ..synopsis::  If T0 is empty, try to calculate it from a couple different
                  methods if either is available.

    ..module::  clear_values
    ..synopsis::  Reset any attributes that were not assigned values, and
                  force any included in vals_to_clear.
    """

    finished_dir = "../finished_pln/"
    ingested_file = "ref/ingested_pln.txt"
    input_dir = "../generated_pln/"
    nasa_data_file = "../catalogs/nasa_archive_v2.csv"

    def __init__(self, planet=None, file=None):

        # If an ExoPlanet object is provided, make sure it has a pln_filename.
        if planet:
            planet.save_to_pln()
            file = planet.pln_filename

        super().__init__(path=file)

        # Keep track of fields containing reference information.
        self.refs = ["firstref", "orbref", "transitref", "specref"]

        # These values get cleared by default for reconciler calculation.
        self.vals_to_clear = ["a", "msini"]

    def _add_nasa_value(self, frame, attr):
        """
        Add values from a CustomNASA object to an ExoPlanet object.

        :param frame:  The ingested NASA Archive .csv file.
        :type frame:  CustomNASA

        :param attr:  The ExoPlanet attribute to be updated.
        :type attr:  ExoParameter
        """

        # Look up the appropriate field to look for in the CustomNASA object.
        # If nasa_field is empty, return immediately.
        nasa_str = attr.nasa_field
        if is_empty(nasa_str):
            return

        # Get the current ExoParameter attached to attr, and update the
        # new value.
        attr.value = frame.read_val(nasa_str)
        if is_valid(attr.value):
            print("Updated {0} for {1}".format(attr.parameter,
                                               self.name.value
                                               ))

        # Update error values for this attribute.
        hi, lo = frame.read_errors(nasa_str)
        attr.uncertainty_upper = hi
        attr.uncertainty_lower = lo

        # Get the reference and url strings for this attribute.
        attr.reference, attr.url = frame.read_refs()

    def _add_simbad_coords(self, query):
        """
        Add RA and Dec information from a Simbad query to an ExoPlanet object.

        :param query:  The Simbad query object.
        :type query:  CustomSimbad
        """

        # Get the coordinate values from the query object.
        ra, dec = query.get_coordinates()

        # If either coordinate is empty, exit the function.
        if is_empty(ra) or is_empty(dec):
            pl = self.name.value
            print("Could not find Simbad coordinates for {0}".format(pl))
            return

        # Set the ExoPlanet coordinate string values to these figures.
        self.ra_string.value = str(ra)
        self.dec_string.value = str(dec)

        # Use astropy SkyCoord to convert these into coordinates in hours and
        # degrees.
        coord = SkyCoord(" ".join([ra, dec]), unit=(u.hourangle, u.deg))

        # Round the numerical coordinates to a reasonable length and set the
        # ExoPlanet attributes.
        self.ra.value = round(Decimal(coord.ra.hour), 10)
        self.dec.value = round(Decimal(coord.dec.degree), 10)

        # Set the COORDREF value to 'Simbad'.
        self.coordref.value = "Simbad"

        # Convert special characters in the SIMBADNAME to HTML friendly characters.
        ident = self.simbadname.value.replace("+", "%2B")
        ident = ident.replace(" ", "+")

        # Construct the Simbad target url and update COORDURL.
        simbad_url = "http://simbad.u-strasbg.fr/simbad/sim-basic?ident="
        self.coordurl.value = "".join([simbad_url, ident])

    def _add_simbad_mags(self, query):
        """
        Add a number of flux magnitude values from a Simbad query to an
        ExoPlanet object.

        :param query:  The Simbad query object.
        :type query:  CustomSimbad
        """

        # Construct a list of filters to look for in the query results.  .pln
        # files list a B-V value instead of B magnitude.
        filters = query.filters
        filters.remove('B')
        filters.append('BMV')

        # Iterate through each filter.
        for f in filters:

            # Get the magnitude value and error from the Simbad results.
            val, err = query.get_magnitude(f)

            # Simbad uses 'K' while .pln files use 'KS'.
            filt_name = ('ks' if f.lower() == 'k' else f.lower())

            # Get the current ExoParameter object for this filter.
            mag = getattr(self, filt_name)

            # Set the value.
            mag.value = val
            mag.uncertainty = err

            # Reset the ExoPlanet filter attribute to the updated ExoParameter.
            setattr(self, filt_name, mag)

    def _calculate_rhostar(self):
        """
        If needed, calculate RHOSTAR using MSTAR and RSTAR if available.
        """

        if (is_empty(self.rhostar.value)
            and is_valid(self.mstar.value)
            and is_valid(self.rstar.value)
            ):

            mstar = Decimal(self.mstar.value)
            rstar = Decimal(self.rstar.value)
            density = (mstar * (Decimal(1.41) / (rstar ** 3)))

            mu = Decimal(self.mstar.uncertainty)
            ru = Decimal(self.rstar.uncertainty)
            if is_valid(mu) and is_valid(ru):
                du = (mu * (Decimal(1.41) / (ru ** 3)))
            else:
                du = 'NaN'

            self.rhostar.value = round(density, len(str(mstar)))
            self.rhostar.uncertainty = du
            self.rhostar.reference = "Calculated from MSTAR and RSTAR"
            self.rhostar.url = str(self.mstar.url)

    def _calculate_t0_from_m0(self):
        """
        Use M0, PER, and REFTIME to calculate T0.
        """

        bjd = Decimal(self.reftime.value)
        m0 = Decimal(self.m0.value)
        per = Decimal(self.per.value)
        self.t0.value = (bjd - ((m0 / Decimal(360)) * per))
        self.t0.reference = "Computed from M0"
        self.t0.url = self.m0.url

    def _calculate_t0_from_tt(self):
        """
        Use PER, TT, and OM to calculate T0.
        """

        p = float(self.per.value)
        sig = len(str(self.tt.value))
        tc = float(self.tt.value)
        rad = np.radians(float(self.om.value))
        f = (np.pi / 2) - rad
        if f != 0:
            ec = float(self.ecc.value)
            ea = 2 * np.arctan(np.tan(f / 2) * np.sqrt((1 - ec) / (1 + ec)))
            tp = tc - (p / (2 * np.pi)) * (ea - ec * np.sin(ea))
            tp = np.round(tp, decimals=(sig - 6))
            self.t0.value = Decimal(str(tp))
            self.t0.uncertainty = self.tt.uncertainty
            self.t0.uncertainty_upper = self.tt.uncertainty_upper
            self.t0.reference = "Computed from TT"
            self.t0.url = self.per.url

    def _check_ar(self):
        """
        If the AR value is empty, clear the reference & url parameters.
        """

        if is_empty(self.ar.value):
            self.ar.reference = "Calculated"
            self.ar.url = None

    def _check_dist_par(self):
        """
        If both DIST and PAR are provided, clear DIST to be calculated from
        PAR.
        """

        d = self.dist.value
        p = self.par.value
        if (is_valid(self.dist.value) and is_valid(self.par.value)):
            self.dist.reset_parameter(force=True)
            print("Resetting DIST for {0}".format(self.name.value))

    def _fix_coord_strings(self):
        """
        Make sure RA_STRING and DEC_STRING are using spaces and not colons.
        """

        cur_ra = self.ra_string.value
        cur_dec = self.dec_string.value
        if cur_ra:
            self.ra_string.value = cur_ra.replace(":", " ")
        if cur_dec:
            self.dec_string.value = cur_dec.replace(":", " ")

    def _remove_bin_refs(self):
        """
        Remove reference info from BINARY if it is not set.
        """

        if str(self.binary.value) == "0":
            self.binary.remove_refs()

    def _remove_et_al(self):
        """
        Remove 'et al.' from any reference strings.
        """

        for r in self.refs:
            exo_param = getattr(self, r)
            chunks = exo_param.value.split(" ")
            excess = ["et", "al.", "al"]
            [chunks.remove(x) for x in excess if x in chunks]
            exo_param.value = " ".join(chunks)
            setattr(self, r, exo_param)

    def _remove_lint(self):
        """
        Remove a few last fields.
        """

        self.massrat.uncertainty = None
        self.massrat.uncertainty_upper = None
        self.kde.reference = None
        self.kde.url = None

    def add_nasa_info(self, nasa_frame):
        """
        Add values from a scraped NASA Archive table to self.

        :param nasa_frame:  The scraped NASA Archive data object for this
                            planet.
        :type nasa_frame:  CustomNASA
        """

        # Keep a list of ExoPlanet attributes to update with NASA data.
        fields_to_update = ["rhostar"]

        for f in fields_to_update:

            # Get the current value of this field.
            current = getattr(self, f)

            # If there is currently no value listed for this field, look for
            # one from the provided NASA data object.
            if is_empty(current.value):
                self._add_nasa_value(nasa_frame, current)

    def add_simbad_info(self):
        """
        Query Simbad for coordinates and magnitude values of the current
        exoplanet, then add the results to the ExoPlanet object.
        """

        # Execute the Simbad query using the SIMBADNAME parameter.
        query_obj = CustomSimbad(self.simbadname.value)

        # Add coordinates and magnitude values from the query results.
        self._add_simbad_coords(query_obj)
        self._add_simbad_mags(query_obj)

    def apply_pln_recipe(self):
        """
        Construct a recipe for finalizing an ExoPlanet before writing a final
        .pln file.
        """

        # Calculate RHOSTAR if it still hasn't been populated.
        # self._calculate_rhostar()

        # Remove ref & url from any empty AR entries.
        self._check_ar()

        # Reset DIST if PAR is provided.
        self._check_dist_par()

        # Remove any remaining ':' from coordinate strings.
        self._fix_coord_strings()

        # Remove ref & url from BINARY unless the flag is set.
        self._remove_bin_refs()

        # Remove any 'et al' strings in reference fields.
        self._remove_et_al()

        # Remove extraneous fields.
        self._remove_lint()

        # Add coordinates and magnitudes from Simbad.
        self.add_simbad_info()

        # Reset any fields that are still null back to defaults.
        self.clear_values()

        # Force a reset of MASS unless this is a microlensing target.
        if self.microlensing.value == 0:
            self.mass.reset_parameter(force=True)

        # Force a reset of R unless this is an imaging target.
        if self.imaging.value == 0:
            self.r.reset_parameter(force=True)

        # Run ExoPlanet verification function.
        self.verify_pln()

        print("{0} updated!".format(self.name.value))

    def check_t0(self):
        """
        If T0 is empty, try to calculate it from a couple different methods if
        either is available.
        """

        if is_empty(self.t0.value):
            if (is_valid(self.tt.value)
                        and is_valid(self.om.value)
                        and is_valid(self.ecc.value)
                    ):
                self._calculate_t0_from_tt()
            elif (is_valid(self.m0.value)
                  and is_valid(self.reftime.value)
                  and is_valid(self.per.value)
                  and self.ecc.value == Decimal(0)
                  ):
                self._calculate_t0_from_m0()

    def clear_values(self):
        """
        Reset any attributes that were not assigned values, and force any
        included in vals_to_clear.
        """

        for att in self.attributes:
            force = att in self.vals_to_clear
            xp = getattr(self, att)
            xp.reset_parameter(force=force)
            setattr(self, att, xp)

# --------------------


class ReconcilerSession(object):
    """
    This class defines commonly-desired routines to run during finalization of
    sets of .pln files.

    ..class::  NewPlnDecorator
    ..synopsis::  Create a class to define a decorator that we'll use to
                  access and loop through custom pln files.

    ..class::  OriginalPlnDecorator
    ..synopsis::  Create a class to define a decorator that we'll use to
                  access and loop through original pln files.

    ..module::  check_planet_names
    ..synopsis::  Look for exoplanet name duplicates within a collection of
                  pln files.

    ..module::  find_commas
    ..synopsis::  Scan ExoPlanet attributes for any ',' characters that may
                  cause errors in CSV files.

    ..module::  find_coords
    ..synopsis::  Collect all target coordinates within a set of pln files.

    ..module::  find_old_pln
    ..synopsis::  Scan for any '-999' RA values.

    ..module::  find_simbad_names
    ..synopsis::  Look for any SIMBADNAME values that may contain a planet
                  designation letter.

    ..module::  run_pln_reconciler
    ..synopsis::  Execute modules to add Simbad data, NASA archive data, and
                  final pln verification routines.
    """

    class NewPlnDecorator(object):
        """
        We want to define a decorator that will loop through some or all of
        the .pln files we've created, since just about every finalization
        routine will need to do this.  New subclasses can be defined for
        different file schemes.

        ..module::  _get_list_to_skip
        ..synopsis::  Read in a list of planets that have already been
                      ingested to EOD so we can skip these.

        ..module::  loop_all_files
        ..synopsis::  Insert the provided function into a loop that iterates
                      through all .pln files found in input_dir.

        ..module::  loop_files_not_added
        ..synopsis::  Insert the provided function into a loop that iterates
                      through all .pln files found in input_dir that are not
                      listed in ingested_file.
        """

        # Define file paths for new or corrected pln files in /generated_pln/.
        finished_dir = "../finished_pln/"
        ingested_file = "ref/ingested_pln.txt"
        input_dir = "../generated_pln/"
        nasa_data_file = "../catalogs/nasa_archive_v2.csv"

        @classmethod
        def _get_list_to_skip(cls):
            """
            Read in a list of planets that have already been ingested to EOD
            so we can skip these.
            """

            temp_list = []
            with open(cls.ingested_file) as txt:
                for line in txt:
                    temp_list.append(line.rstrip())
            return list(sorted(temp_list))

        @classmethod
        def loop_all_files(cls, decorated):
            """
            Insert the provided function into a loop that iterates through all
            .pln files found in input_dir.
            """

            # Construct the wrapper loop function.
            def wrapper_loop(*args, **kwargs):

                # Get a list of files in input_dir.
                pln_list = os.listdir(cls.input_dir)

                # Read in the content of the NASA archive file.
                cls.nasa_frame = CustomNASA(cls.nasa_data_file, *args)

                # Initialize empty results list.
                results_list = []

                # Loop through all files in input_dir.
                for pln in pln_list:

                    # Skip file if name does not end in '.pln' or contains
                    # 'none' (used for testing).
                    if not pln.endswith(".pln"):
                        continue
                    elif "none" in pln.lower():
                        continue

                    # Get the full filepath and create a new Reconciler object
                    # from the pln file.
                    xplanet_path = os.path.join(cls.input_dir, pln)
                    xplanet = Reconciler(file=xplanet_path)

                    # Execute the decorated function.
                    results = decorated(cls, xplanet, results_list)

                print("...scanned {0} pln files!".format(len(pln_list)))
                return results

            return wrapper_loop

        @classmethod
        def loop_files_not_added(cls, decorated):
            """
            Insert the provided function into a loop that iterates through all
            .pln files found in input_dir that are not listed in ingested_file.
            """

            # Construct the wrapper loop function.
            def wrapper_loop(*args, **kwargs):

                # Get a list of files in input_dir.
                pln_list = os.listdir(cls.input_dir)

                # Read in the list of already-ingested pln files to skip.
                skip_list = cls._get_list_to_skip()

                # Read in the content of the NASA archive file.
                cls.nasa_frame = read_nasa_data(cls.nasa_data_file)

                # Initialize empty results list.
                results_list = []

                # Loop through all files in input_dir.
                for pln in pln_list:

                    # Skip file if name is contained in skip_list, does not
                    # end in '.pln', or contains 'none' (used for testing).
                    if pln.split("_", 1)[-1] in skip_list:
                        print("Skipping {0}".format(pln))
                        continue
                    elif not pln.endswith(".pln"):
                        continue
                    elif "none" in pln.lower():
                        continue

                    # Get the full filepath and create a new Reconciler object
                    # from the pln file.
                    xplanet_path = os.path.join(cls.input_dir, pln)
                    xplanet = Reconciler(file=xplanet_path)

                    # Execute the decorated function.
                    results = decorated(cls, xplanet, results_list)

                print("...scanned {0} pln files!".format(len(pln_list)))
                return results

            return wrapper_loop

    class OriginalPlnDecorator(NewPlnDecorator):
        """
        This subclass updates the file paths to look at original files already
        in EOD as of June 2018.
        """

        # Define file paths for original pln files.
        finished_dir = "../finished_pln/"
        ingested_file = "ref/ingested_pln.txt"
        input_dir = "../original_files/exoplanet_pln_dir/"
        nasa_data_file = "../catalogs/nasa_archive_v2.csv"

    def __init__(self, dir=None):
        self._dir = dir
        self.coords_dict = {}

    @OriginalPlnDecorator.loop_all_files
    def check_planet_names(loop_class, xplanet, results_list):
        """
        Decorator will loop through all original pln files.  This function
        will collect all name values from the current exoplanet, and compare
        those with the contents of results_list.  If any duplicates are found,
        print an alert.

        :param loop_class:  The class decorating this function being used to
                            loop through files.
        :type loop_class: ReconcilerSession.OriginalPlnDecorator

        :param xplanet:  The current ExoPlanet object being examined.
        :type xplanet:  ExoPlanet

        :param results_list:  A list to collect results from this function.
        :type results_list:  list
        """

        target_names = xplanet.find_all_names()
        target_names = list(set(target_names))
        for name in target_names:
            if name in results_list and xplanet.star.value not in results_list:
                print("{0} duplicated in {1}".format(name, xplanet.name.value))
            else:
                results_list.append(name)
        return results_list

    @NewPlnDecorator.loop_files_not_added
    def find_commas(loop_class, xplanet, results_list):
        """
        Decorator will loop through all new or corrected files not listed in
        'ingested_pln.txt'.  Search all attributes of this exoplanet for any
        commas that may cause errors in a CSV file.

        :param loop_class:  The class decorating this function being used to
                            loop through files.
        :type loop_class: ReconcilerSession.NewPlnDecorator

        :param xplanet:  The current ExoPlanet object being examined.
        :type xplanet:  ExoPlanet

        :param results_list:  A list to collect results from this function.
        :type results_list:  list
        """

        for param in xplanet.attributes:
            param_obj = getattr(xplanet, param)
            for val in param_obj.__dict__.values():
                if "," in str(val):
                    print("Found comma in planet={0}, field={1}".format(
                        xplanet.name.value, val))

    @OriginalPlnDecorator.loop_all_files
    def find_coords(loop_class, xplanet, results_list):
        """
        Decorator will loop through all original pln files.  Write coordinates
        from an exoplanet into a .txt file.

        :param loop_class:  The class decorating this function being used to
                            loop through files.
        :type loop_class: ReconcilerSession.OriginalPlnDecorator

        :param xplanet:  The current ExoPlanet object being examined.
        :type xplanet:  ExoPlanet

        :param results_list:  A list to collect results from this function.
        :type results_list:  list
        """

        coord_str = ", ".join([xplanet.ra_string.value,
                               xplanet.dec_string.value])
        if len(coord_str) < 10:
            print("No coordinates found for {0}".format(xplanet.name.value))
            return
        else:
            coord_str = ", ".join([xplanet.name.value, coord_str])
            with open('coords.txt', 'a') as f:
                f.write((coord_str + "\n"))

    @NewPlnDecorator.loop_files_not_added
    def find_old_pln(loop_class, xplanet, results_list):
        """
        Decorator will loop through all new or corrected files not listed in
        'ingested_pln.txt'.  Print an alert for an ExoPlanet with an RA value
        of '-999'.

        :param loop_class:  The class decorating this function being used to
                            loop through files.
        :type loop_class: ReconcilerSession.NewPlnDecorator

        :param xplanet:  The current ExoPlanet object being examined.
        :type xplanet:  ExoPlanet

        :param results_list:  A list to collect results from this function.
        :type results_list:  list
        """

        if str(xplanet.ra.value) == "-999":
            print("Found old pln file:  {0}".format(xplanet.name.value))

    @NewPlnDecorator.loop_files_not_added
    def find_simbad_names(loop_class, xplanet, results_list):
        """
        Decorator will loop through all new or corrected files not listed in
        'ingested_pln.txt'.  Print an alert for an ExoPlanet with a SIMBADNAME
        value that has a single character ending (may be inadvertant exoplanet
        designation).

        :param loop_class:  The class decorating this function being used to
                            loop through files.
        :type loop_class: ReconcilerSession.NewPlnDecorator

        :param xplanet:  The current ExoPlanet object being examined.
        :type xplanet:  ExoPlanet

        :param results_list:  A list to collect results from this function.
        :type results_list:  list
        """

        chunks = xplanet.simbadname.value.split(" ")
        if len(chunks[-1]) == 1:
            print("Found suspicious simbad name: {0}".format(
                xplanet.name.value))

    @NewPlnDecorator.loop_files_not_added
    def run_pln_reconciler(loop_class, xplanet, results_list):
        """
        Decorator will loop through all new or corrected files not listed in
        'ingested_pln.txt'.  Ready an ExoPlanet for final writing to a .pln
        file.

        :param loop_class:  The class decorating this function being used to
                            loop through files.
        :type loop_class: ReconcilerSession.NewPlnDecorator

        :param xplanet:  The current ExoPlanet object being examined.
        :type xplanet:  ExoPlanet

        :param results_list:  A list to collect results from this function.
        :type results_list:  list
        """

        # Add Simbad coordinates and magnitude values.
        xplanet.add_simbad_info()

        # Read the NASA Archive data file and add values from this.
        nasa_frame = CustomNASA(loop_class.nasa_data_file, xplanet.name.value)
        if nasa_frame.valid:
            xplanet.add_nasa_info(nasa_frame)

        # Apply the final .pln recipe and save the file.
        xplanet.apply_pln_recipe()
        xplanet.save_to_pln(dir=loop_class.finished_dir, disp=False)

# --------------------


def check_for_name_matches():

    x = ReconcilerSession()
    results = x.check_planet_names()
    print(len(results))

# --------------------


def check_for_matching_coords():
    coords_dict = {}
    matching_dict = {}
    with open("coords.txt") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            c = SkyCoord(" ".join([row[1], row[2]]), unit=(u.hourangle, u.deg))
            coords_dict[row[0]] = c

    coords_copy = dict(coords_dict)
    n = 0
    start = time.time()
    print("Started at {0}".format(start))
    for name, c in coords_dict.items():
        matching_dict[name] = []
        parent1 = " ".join(name.split(" ")[:-1])
        for candidate, comparison in coords_copy.items():
            parent2 = " ".join(candidate.split(" ")[:-1])
            if (candidate == name or parent2 == parent1):
                continue
            sep = c.separation(comparison).arcsecond
            if sep < 10:
                matching_dict[name].append((candidate, sep))
                print("Found {0} close to {1}".format(candidate, name))
        if len(matching_dict[name]) == 0:
            del matching_dict[name]
            del coords_copy[name]
        n += 1
        if (n % 100) == 0:
            print("Up to {0}".format(name))
            time_per_chunk = ((time.time() - start) / (n / 100))
            remaining = ((((3200 - n) / 100) * time_per_chunk) / 60)
            print("{0} min remaining".format(remaining))
    with open('matching.txt', 'w') as f:
        f.write(json.dumps(matching_dict,
                           sort_keys=True,
                           indent=4 * ' '
                           ))

# --------------------


def finish_new_plns():
    """
    Run the pln reconciler routine.
    """

    x = ReconcilerSession()
    x.run_pln_reconciler()

# --------------------


if __name__ == "__main__":
    # check_for_name_matches()
    finish_new_plns()
