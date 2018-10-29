from add_nasa_data import add_nasa_data
from add_simbad_info import add_simbad_info
from decimal import Decimal
from Exoplanet import ExoParameter, Exoplanet
import os
import pandas as pd
from scrape_nasa import read_nasa_data
import time

BLANK_PLN = Exoplanet()
FINISH = "../finished_pln/"
INGESTED = "ref/ingested_pln.txt"
INPUT = "../generated_pln/"
NASA_DATA = "../catalogs/nasa_archive_v2.csv"
VARS_TO_CLEAR = ["a", "msini"]


def remove_et_al(exoplanet):
    refs = ["firstref", "orbref", "transitref", "specref"]
    for r in refs:
        exo_param = getattr(exoplanet, r)
        chunks = exo_param.value.split(" ")
        if len(chunks) < 4:
            continue
        try:
            chunks.remove("et")
            chunks.remove("al.")
            chunks.remove("al")
        except ValueError:
            pass
        exo_param.value = " ".join(chunks)
        setattr(exoplanet, r, exo_param)
    return exoplanet


def check_ar(xplanet):
    ar = str(xplanet.ar.value)
    if ar == "NaN":
        xplanet.ar.reference = "Calculated"
        xplanet.ar.url = None
    return xplanet


def check_dist_par(exoplanet):
    d = str(exoplanet.dist.value).lower()
    p = str(exoplanet.par.value).lower()
    if d == "nan" or p == "nan":
        return exoplanet
    else:
        exoplanet.dist.copy_values(BLANK_PLN.dist)
        print("Resetting DIST for {0}".format(exoplanet.name.value))
        return exoplanet


def clean_A(exoplanet):
    blank_a = getattr(BLANK_PLN, "a")
    exoplanet.a.copy_values(blank_a)
    return exoplanet


def clear_parameter(exoplanet, param):
    blank_param = getattr(BLANK_PLN, param)
    current_param = getattr(exoplanet, param)
    current_param.copy_values(blank_param)
    setattr(exoplanet, param, current_param)
    return exoplanet


def fix_coord_strings(exoplanet):
    cur_ra = exoplanet.ra_string.value
    cur_dec = exoplanet.dec_string.value
    if cur_ra:
        exoplanet.ra_string.value = cur_ra.replace(":", " ")
    if cur_dec:
        exoplanet.dec_string.value = cur_dec.replace(":", " ")
    return exoplanet


def remove_bin_refs(exoplanet):
    if str(exoplanet.binary.value) == "0":
        exoplanet.binary.reference = None
        exoplanet.binary.url = None
    return exoplanet


def remove_lint(exoplanet):
    exoplanet.massrat.uncertainty_upper = None
    exoplanet.kde.reference = None
    exoplanet.kde.url = None
    return exoplanet


def final_updates(xplanet):
    xplanet = remove_et_al(xplanet)
    xplanet = check_ar(xplanet)
    [clear_parameter(xplanet, v) for v in VARS_TO_CLEAR]
    if xplanet.microlensing.value == 0:
        clear_parameter(xplanet, "mass")
    if xplanet.imaging.value == 0:
        clear_parameter(xplanet, "r")
    xplanet = fix_coord_strings(xplanet)
    xplanet = remove_bin_refs(xplanet)
    xplanet = remove_lint(xplanet)
    xplanet = check_dist_par(xplanet)
    xplanet.verify_pln()
    xplanet.save_to_pln(dir=FINISH, disp=False)
    print("{0} updated!".format(xplanet.name.value))


def find_commas(xplanet):
    for param in xplanet.attributes:
        param_obj = getattr(xplanet, param)
        for val in param_obj.__dict__.values():
            if "," in str(val):
                print("Found comma in planet={0}, field={1}".format(
                    xplanet.name.value, val))


def find_old_pln(xplanet):
    if str(xplanet.ra.value) == "-999":
        print("Found old pln file:  {0}".format(xplanet.name.value))


def find_simbad_names(xplanet):
    chunks = xplanet.simbadname.value.split(" ")
    if len(chunks[-1]) == 1:
        print("Found suspicious simbad name: {0}".format(xplanet.name.value))


def get_list_to_skip():

    skip_list = []
    with open(INGESTED) as txt:
        for line in txt:
            skip_list.append(line.rstrip())
    return sorted(skip_list)


def run_through_files():

    pln_list = os.listdir(INPUT)
    skip_list = get_list_to_skip()
    nasa_frame = read_nasa_data(NASA_DATA)
    for pln in pln_list:
        if pln.split("_", 1)[-1] in skip_list:
            print("Skipping {0}".format(pln))
            continue
        elif not pln.endswith(".pln"):
            continue
        elif "none" in pln.lower():
            continue
        xplanet = Exoplanet(path=os.path.join(INPUT, pln))
        # print("pln={0}, xplanet={1}".format(pln, xplanet.attributes))
        xplanet = add_simbad_info(xplanet)
        xplanet = add_nasa_data(xplanet, nasa_frame)
        final_updates(xplanet)
        # find_commas(xplanet)
        # find_old_pln(xplanet)
        # find_simbad_names(xplanet)
    print("...scanned {0} pln files!".format(len(pln_list)))


if __name__ == "__main__":
    run_through_files()
