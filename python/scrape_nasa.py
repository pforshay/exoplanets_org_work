from Exoplanet import Exoplanet, ExoParameter
import os
import pandas as pd

LIST = "ref/new_exoplanets_to_add.csv"
NASA = "../catalogs/nasa_archive_v2.csv"
ENTERED_DIR = "../generated_pln/"


def edit_pln_list(full_list):
    already_done = os.listdir(ENTERED_DIR)
    for pln in already_done:
        if not pln.endswith(".pln"):
            continue
        pln = simple_str(pln[4:-4])
        if pln in full_list:
            full_list.remove(pln)
    return full_list


def get_pl_name_list(csv_to_add):
    add_frame = pd.read_csv(csv_to_add)
    nasa_names = add_frame["pl_name"]
    return nasa_names.tolist()


def simple_str(name):
    """
    Reduce a provided string to lower-case letters and numbers.

    :param name:  The target name to reduce.
    :type name:  str
    """

    name = str(name).strip().lower()
    name = "".join(n for n in name if n.isalnum())

    return name


def read_nasa_data(nasa_csv):
    nasa_frame = pd.read_csv(nasa_csv, comment='#', dtype=str)
    nasa_frame.insert(len(nasa_frame.columns), "simple_name", None)

    for n in nasa_frame.index:
        nasa_frame.at[n, "simple_name"] = simple_str(nasa_frame.at[n,
                                                                   "pl_name"
                                                                   ]
                                                     )
    return nasa_frame


def make_nasa_files(list_to_add, nasa_frame):
    test_list = []
    print("Looping through {0} names...".format(len(list_to_add)))
    for name in list_to_add:
        match = nasa_frame[(nasa_frame["simple_name"] == name)]
        if len(match.index) == 1:
            new_planet = Exoplanet()
            ind = match.index[0]
            row = match.iloc[0]
            new_planet.read_from_nasa(row)
            new_planet.verify_pln()
            test_list.append(row.pl_name)
            new_planet.save_to_pln(dir="../scraped_pln/scrape_nasa_v14/")
    return test_list


def run():
    add = get_pl_name_list(LIST)
    add = edit_pln_list(add)
    nasa_frame = read_nasa_data(NASA)
    results = make_nasa_files(add, nasa_frame)
    print(results)


if __name__ == "__main__":
    run()
