from astropy.coordinates import SkyCoord
import astropy.units as u
import csv
from Exoplanet import Exoplanet, ExoParameter
import os
import pandas as pd
import sqlite3

EOD_PATH = "exoplanets.csv"
ENC_PATH = "exoplanet_eu_catalog.csv"
ARC_PATH = "nasa_archive_confirmed.csv"
SKIP_TXT = "skip_planets.txt"


def check_ra_dec(eod, missing, drop_far=True):
    eod_ra = eod["RA"].tolist()
    eod_dec = eod["DEC"].tolist()
    eod_coords = list(tuple(zip(eod_ra, eod_dec)))
    eod_coords = [interpret_coords(c, u.hourangle, u.deg) for c in eod_coords]
    eod_dict = {}
    for c in eod_coords:
        if c is None:
            continue
        eod_ra = int(c.ra.deg)
        if eod_ra in eod_dict.keys():
            eod_dict[eod_ra].append(c)
        else:
            eod_dict[eod_ra] = [c]
    missing.insert(len(missing.columns), "checked_coords", None)
    missing.insert(len(missing.columns), "min_distance", "Too far")
    print("len(missing.index) = {0}".format(len(missing.index)))
    far_targets = []
    for n, row in missing.iterrows():
        ra = "ra" if drop_far else "ra_x"
        dec = "dec" if drop_far else "dec_x"
        coords = (row[ra], row[dec])
        coords = interpret_coords(coords, u.deg, u.deg)
        missing.at[n, "checked_coords"] = str(coords)
        ra_deg = int(coords.ra.deg)
        ra_deg = (ra_deg-1, ra_deg, ra_deg+1)
        nearby = []
        for ra in ra_deg:
            if ra in eod_dict.keys():
                nearby.extend(eod_dict[ra])
        if len(nearby) == 0:
            far_targets.append(n)
            #print("Dropped row {0} (none nearby)".format(n))
            continue
        distance = [c.separation(coords).arcsecond for c in nearby]
        distance = min(distance)
        missing.at[n, "min_distance"] = distance
        if distance > 10:
            far_targets.append(n)
    if drop_far:
        all_nearby = missing.drop(far_targets)
        final_frame = all_nearby[["# name",
                                  "alternate_names",
                                  "star_name",
                                  "star_alternate_names",
                                  "ra",
                                  "dec",
                                  "checked_coords",
                                  "min_distance",
                                  ]]
    else:
        final_frame = missing[missing.index.isin(far_targets)]
    return final_frame


def create_sqlite_file():
    filename = "exoplanets.db"
    if os.path.isfile(filename):
        os.remove(filename)
    conn = sqlite3.connect(filename)
    return conn


def interpret_coords(coord_tup, unit_ra, unit_dec):
    ra, dec = coord_tup
    if str(ra) == "nan" or str(dec) == "nan":
        coords = None  # (ra, dec)
    else:
        coords = SkyCoord(ra, dec, unit=(unit_ra, unit_dec))
    return coords


def read_csv_to_pdframe(path):
    new_pdframe = pd.DataFrame()
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        head = reader[0]
        for row in reader:
            pd_row = pd.DataFrame(columns=head, data=[row])
            pd.concat([new_pdframe, pd_row])

    return new_pdframe


def read_csv_to_exoplanets(path):
    as_objs = []
    with open(path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            new_exoplanet = Exoplanet(parameters=row)
            as_objs.append(new_exoplanet)
    return as_objs


def read_skip_planets_txt(path):
    skip = []
    with open(path, 'r') as skipfile:
        for line in skipfile:
            skip.append(line.strip())
    return skip


def get_all_eod_names(eod_frame):
    name_fields = ["NAME",
                   "OTHERNAME",
                   "JSNAME",
                   "EANAME",
                   "CPSNAME",
                   "SMENAME",
                   "TABLENAME",
                   "SIMBADNAME",
                   "ETDNAME"]
    all_names = []
    for field in name_fields:
        try:
            all_names.extend(eod_frame[field].tolist())
        except KeyError:
            continue
    all_names = filter(None, all_names)
    return list(set(all_names))


def merge_missing_frames(arc_missing, eu_missing):
    name_field = ExoParameter("NAME")
    eu_name = "# name"
    nasa_name = "pl_name"
    arc_missing[nasa_name] = arc_missing[nasa_name].map(
        lambda x: simple_str(x))
    eu_missing[eu_name] = eu_missing[eu_name].map(lambda x: simple_str(x))
    merged_frame = pd.merge(arc_missing,
                            eu_missing,
                            how='inner',
                            left_on=nasa_name,
                            right_on=eu_name)
    merged_frame = merged_frame[["pl_name",
                                 "# name",
                                 "ra_x",
                                 "ra_y",
                                 "dec_x",
                                 "dec_y",
                                 "st_vj",
                                 "mag_v",
                                 "pl_bmassj",
                                 "mass_sini",
                                 "pl_radj",
                                 "radius",
                                 "pl_orbper",
                                 "orbital_period",
                                 "pl_orbsmax",
                                 "semi_major_axis",
                                 "pl_orbeccen",
                                 "eccentricity",
                                 "pl_def_reflink",
                                 "pl_disc_reflink",
                                 ]]
    return merged_frame


def missing_from_archive(eod_names, arc):
    names = [simple_str(n) for n in eod_names]
    names.extend(read_skip_planets_txt(SKIP_TXT))
    arc_names = arc["pl_name"].map(lambda x: simple_str(x))
    #arc_names = [a for a in arc_names if a not in skip_planets]
    missing = arc[~(arc_names.isin(names))]
    return missing


def missing_from_encyclopedia(eod_names, enc):
    names = [simple_str(n) for n in eod_names]
    names.extend(read_skip_planets_txt(SKIP_TXT))
    enc_names = enc["# name"].map(lambda x: simple_str(x))
    #enc_names = [e for e in enc_names if e not in skip_planets]
    missing = enc[~(enc_names.isin(names))]
    #missing = [ind for ind in diff.index if diff.iloc[ind] == False]
    #missing = [encyc.iloc[n] for n in missing]
    return missing


def compare_exo_names(exo_frame):
    diff = exo_frame[(exo_frame["EANAME"] != exo_frame["NAME"])]
    diff = diff[["EANAME", "JSNAME", "NAME"]]
    return diff


def simple_str(name):
    name = str(name).strip().lower()
    name = "".join(n for n in name if n.isalnum())
    return name


def run():
    conn = create_sqlite_file()
    eod_frame = pd.read_csv(EOD_PATH)
    enc_frame = pd.read_csv(ENC_PATH)
    arc_frame = pd.read_csv(ARC_PATH, comment='#')
    eod_names = get_all_eod_names(eod_frame)
    eod_frame.to_sql("EOD", conn)
    enc_missing = missing_from_encyclopedia(eod_names, enc_frame)
    enc_missing.to_sql("EU entries not in EOD", conn)
    arc_missing = missing_from_archive(eod_names, arc_frame)
    arc_missing.to_sql("Archive entries not in EOD", conn)
    match = merge_missing_frames(arc_missing, enc_missing)
    match.to_sql("Merged Archive & EU frames", conn)
    match_with_distances = check_ra_dec(eod_frame, match, drop_far=False)
    match_with_distances.to_sql("Merged frames w/ no close EOD targets", conn)
    near_missing = check_ra_dec(eod_frame, enc_missing)
    near_missing.to_sql("EU entries with nearby EOD targets", conn)
    diff = compare_exo_names(eod_frame)
    diff.to_sql("Name Discrepancies", conn)
    conn.close()


if __name__ == "__main__":
    run()
    #a = read_csv_to_exoplanets(EOD_PATH)
    # print(a[-1].parameters)
