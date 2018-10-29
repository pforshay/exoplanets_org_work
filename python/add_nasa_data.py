from scrape_nasa import simple_str


def add_nasa_data(xplanet, nasa_frame):

    simple_name = simple_str(xplanet.name.value)
    match = nasa_frame[(nasa_frame["simple_name"] == simple_name)]
    if len(match.index) == 1:
        # xplanet.bmv.value = match["st_bmvj"].values[0]
        check = str(xplanet.rhostar.value).lower()
        if xplanet.transit.value == 1 and check == 'nan':
            xplanet.rhostar.value = match["st_dens"].values[0]
            xplanet.rhostar.uncertainty_upper = match["st_denserr1"].values[0]
            xplanet.rhostar.uncertainty_lower = (
                match["st_denserr2"].values[0] * -1)
            reflink = match["pl_def_reflink"].values[0].split("href=")[-1]
            link, ref = reflink[:-4].split("target=ref>", 1)
            link = link.split("cgi-bin/nph-bib_query?bibcode=")
            link = "abs/".join(link)
            ref = ref.split(" ")
            ref_str = ""
            for chunk in ref:
                if (chunk == "et" or chunk == "al."):
                    pass
                else:
                    ref_str = " ".join([ref_str, chunk])
            if not str(xplanet.rhostar.value).lower() == 'nan':
                xplanet.rhostar.reference = ref_str.lstrip().rstrip()
                xplanet.rhostar.url = link.lstrip().rstrip()
                print("Added rhostar values to {0}".format(xplanet.name.value))
            else:
                print("No rhostar found for {0}".format(xplanet.name.value))

    return xplanet
