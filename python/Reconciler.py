from add_nasa_data import add_nasa_data
from add_simbad_info import add_simbad_info
from astropy import units as u
from astropy.coordinates import SkyCoord
import csv
from decimal import Decimal
from Exoplanet import ExoParameter, Exoplanet
from bin.is_empty import is_empty, is_valid
import json
import math
import numpy as np
import os
import pandas as pd
from scrape_nasa import read_nasa_data
import time

# --------------------


class Reconciler(Exoplanet):
    """
    Create an Exoplanet subclass with special methods for running final checks,
    updates, and calculations before writing a final .pln file.
    """

    finished_dir = "../finished_pln/"
    ingested_file = "ref/ingested_pln.txt"
    input_dir = "../generated_pln/"
    nasa_data_file = "../catalogs/nasa_archive_v2.csv"

    def __init__(self, planet=None, file=None):

        # If an Exoplanet object is provided, make sure it has a pln_filename.
        if planet:
            planet.save_to_pln()
            file = planet.pln_filename

        super().__init__(path=file)

        # Keep track of fields containing reference information.
        self.refs = ["firstref", "orbref", "transitref", "specref"]

        # These values get cleared by default for reconciler calculation.
        self.vals_to_clear = ["a", "msini"]

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

        bjd = Decimal(self.reftime.value)
        m0 = Decimal(self.m0.value)
        per = Decimal(self.per.value)
        self.t0.value = (bjd - ((m0 / Decimal(360)) * per))
        self.t0.reference = "Computed from M0"
        self.t0.url = self.m0.url

    def _calculate_t0_from_tt(self):

        p = float(self.per.value)
        sig = len(str(self.tt.value))
        tc = float(self.tt.value)
        rad = np.radians(float(self.om.value))
        f = (np.pi / 2) - rad
        if f != 0:
            ec = float(self.ecc.value)
            ea = 2 * np.arctan(np.tan(f/2) * np.sqrt((1-ec) / (1+ec)))
            tp = tc - (p / (2*np.pi)) * (ea - ec * np.sin(ea))
            tp = np.round(tp, decimals=(sig-6))
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
            try:
                chunks.remove("et")
                chunks.remove("al.")
                chunks.remove("al")
            except ValueError:
                pass
            exo_param.value = " ".join(chunks)
            setattr(self, r, exo_param)

    def _remove_lint(self):
        """
        Remove a few last fields.
        """

        self.massrat.uncertainty_upper = None
        self.kde.reference = None
        self.kde.url = None

    def apply_pln_recipe(self):
        """
        Construct a recipe for finalizing an Exoplanet before writing a final
        .pln file.
        """

        self._remove_et_al()
        self._check_ar()
        self._calculate_rhostar()
        self.clear_values()
        if self.microlensing.value == 0:
            self.mass.reset_parameter()
        if self.imaging.value == 0:
            self.r.reset_parameter()
        self._fix_coord_strings()
        self._remove_bin_refs()
        self._remove_lint()
        self._check_dist_par()
        self.verify_pln()
        print("{0} updated!".format(self.name.value))

    def check_t0(self):

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
    """

    class NewPlnDecorator(object):
        """
        We want to define a decorator that will loop through some or all of
        the .pln files we've created, since just about every finalization
        routine will need to do this.  New subclasses can be defined for
        different file schemes.
        """

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

            def wrapper_loop(*args, **kwargs):
                pln_list = os.listdir(cls.input_dir)
                cls.nasa_frame = read_nasa_data(cls.nasa_data_file)
                results_list = []
                for pln in pln_list:
                    if not pln.endswith(".pln"):
                        continue
                    elif "none" in pln.lower():
                        continue
                    xplanet_path = os.path.join(cls.input_dir, pln)
                    xplanet = Reconciler(file=xplanet_path)
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

            def wrapper_loop(*args, **kwargs):
                pln_list = os.listdir(cls.input_dir)
                skip_list = cls._get_list_to_skip()
                cls.nasa_frame = read_nasa_data(cls.nasa_data_file)
                results_list = []
                for pln in pln_list:
                    if pln.split("_", 1)[-1] in skip_list:
                        print("Skipping {0}".format(pln))
                        continue
                    elif not pln.endswith(".pln"):
                        continue
                    elif "none" in pln.lower():
                        continue
                    xplanet_path = os.path.join(cls.input_dir, pln)
                    xplanet = Reconciler(file=xplanet_path)
                    results = decorated(cls, xplanet, results_list)
                print("...scanned {0} pln files!".format(len(pln_list)))
                return results
            return wrapper_loop

    class OriginalPlnDecorator(NewPlnDecorator):
        """
        This subclass updates the file paths to look at original files already
        in EOD as of June 2018.
        """

        finished_dir = "../finished_pln/"
        ingested_file = "ref/ingested_pln.txt"
        input_dir = "../original_files/exoplanet_pln_dir/"
        nasa_data_file = "../catalogs/nasa_archive_v2.csv"

    def __init__(self, dir=None):
        self._dir = dir
        self.coords_dict = {}

    @OriginalPlnDecorator.loop_all_files
    def check_planet_names(loop_class, xplanet, results_list):

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
        Search all attributes of an Exoplanet for any commas that may cause
        errors in a CSV file.
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
        Write coordinates from an Exoplanet into a .txt file.
        """

        coord_str = ", ".join([xplanet.ra_string.value,
                               xplanet.dec_string.value])
        if len(coord_str) < 10:
            print("No coordinates found for {0}".format(xplanet.name.value))
            return
        else:
            coord_str = ", ".join([xplanet.name.value, coord_str])
            with open('coords.txt', 'a') as f:
                f.write((coord_str+"\n"))

    @NewPlnDecorator.loop_files_not_added
    def find_old_pln(loop_class, xplanet, results_list):
        """
        Print an alert for an Exoplanet with an RA value of '-999'.
        """

        if str(xplanet.ra.value) == "-999":
            print("Found old pln file:  {0}".format(xplanet.name.value))

    @NewPlnDecorator.loop_files_not_added
    def find_simbad_names(loop_class, xplanet, results_list):
        """
        Print an alert for an Exoplanet with a SIMBADNAME value that has a
        single character ending (may be inadvertant exoplanet designation).
        """

        chunks = xplanet.simbadname.value.split(" ")
        if len(chunks[-1]) == 1:
            print("Found suspicious simbad name: {0}".format(
                xplanet.name.value))

    @NewPlnDecorator.loop_files_not_added
    def run_pln_reconciler(loop_class, xplanet, results_list):
        """
        Ready an Exoplanet for final writing to a .pln file.
        """

        finished_file = add_simbad_info(xplanet)
        finished_file = add_nasa_data(finished_file, loop_class.nasa_frame)
        finished_file.apply_pln_recipe()
        finished_file.save_to_pln(dir=loop_class.finished_dir, disp=False)

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
        f.write(json.dumps(matching_dict))

# --------------------


def finish_new_plns():
    x = ReconcilerSession()
    x.run_pln_reconciler()

# --------------------


if __name__ == "__main__":
    # check_for_name_matches()
    finish_new_plns()
