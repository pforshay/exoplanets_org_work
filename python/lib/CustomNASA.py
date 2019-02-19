"""
:title:  CustomNASA.py
:author:  Peter Forshay
:contact:  pforshay@stsci.edu

This code is intended to ingest data from the NASA Exoplanet Archive for use
in ExoPlanet object operations.

..class::  CustomNASA
..synopsis::  This class can be used to read data from a CSV file downloaded
              from the NASA Exoplanet Archive, and return requested values
              from that data.
"""

import pandas as pd
from bin.simple_str import simple_str

# --------------------


class CustomNASA(object):
    """
    This class can be used to read data from a CSV file downloaded from the
    NASA Exoplanet Archive, and return requested values from that data.

    ..module::  read_errors
    ..synopsis::  Read value errors out of the data pulled from the NASA file.

    ..module::  read_refs
    ..synopsis::  Parse the reference string associated with the data pulled
                  from the NASA file.

    ..module::  read_val
    ..synopsis::  Read a certain value out of the data pulled from the NASA
                  file.
    """

    def __init__(self, path, planet_name):
        """
        Read a provided CSV filepath into a pandas DataFrame.

        :param path:  The filepath to the NASA CSV file with data for multiple
                      planets.
        :type path:  str

        :param planet_name:  The exoplanet to pull data from the NASA file
                             for.
        :type planet_name:  str
        """

        # Use the pandas read_csv function to read the file into a DataFrame.
        nasa_frame = pd.read_csv(path, comment='#', dtype=str)

        # Get a simplified version of the requested exoplanet name (all
        # lowercase, no symbols or spaces)
        simple_pl = simple_str(planet_name)

        # Initialize self.frame with an empty DataFrame.
        self.frame = pd.DataFrame()

        # Stepping through the NASA DataFrame, look for a match of the
        # simplified planet names.
        for n in nasa_frame.index:
            simple_name = simple_str(nasa_frame.at[n, "pl_name"])
            if simple_name == simple_pl:

                # If a match is found, add this index to self.frame and stop
                # searching.
                self.frame = nasa_frame.iloc[n]
                break

        # Set a self.valid flag based on the search results.
        if self.frame.shape[0] > 0:
            self.valid = True
        else:
            self.valid = False
            print("Couldn't find {0} in nasa data...".format(planet_name))

    def read_errors(self, key):
        """
        Read value errors out of the data pulled from the NASA file.

        :param key:  The key to look for in the results DataFrame.
        :type key:  str
        """

        if self.valid:

            # The NASA CSV file uses a ''<attribute>err1' naming structure for
            # error field names.
            err1 = self.read_val("".join([key, 'err1']))
            err2 = self.read_val("".join([key, 'err2']))

            # NASA records lower uncertainty values as a negative number.
            err2 = (err2 * -1 if err2 else err2)
        else:
            err1 = err2 = None

        return (err1, err2)

    def read_refs(self):
        """
        Parse the reference string associated with the data pulled from the
        NASA file.  Example NASA reflink string:
        <a refstr="LIU ET AL. 2008"
        href=http://adsabs.harvard.edu/cgi-bin/nph/
        bib_query?bibcode=2008ApJ...
        672..553L target=ref> Liu et al. 2008 </a>
        """

        if self.valid:

            # We don't need anything up to the 'href=' string, so cut that
            # off.
            reflink = self.read_val("pl_def_reflink").split("href=")[-1]

            # Split the remaining string on 'target=ref>' and cut off the </a>
            # tag.
            link, ref = reflink[:-4].split("target=ref>", 1)

            # Replace the bibcode query in the link with a direct link.
            link = link.split("cgi-bin/nph-bib_query?bibcode=")
            link = "abs/".join(link)

            # Remove 'et al.' from the reference string.
            ref = ref.split(" ")
            ref_str = ""
            for chunk in ref:
                if (chunk == "et" or chunk == "al."):
                    continue
                else:
                    ref_str = " ".join([ref_str, chunk])

            # Strip any remaining leading or following spaces.
            ref_str = ref_str.strip()
            link = link.strip()

        else:
            ref_str = link = None

        return (ref_str, link)

    def read_val(self, key):
        """
        Read a certain value out of the data pulled from the NASA file.

        :param key:  The key to look for in the results DataFrame.
        :type key:  str
        """

        if self.valid:
            return self.frame[key]
        else:
            return None

# --------------------


def test():
    path = "../catalogs/nasa_archive_v2.csv"
    x = CustomNASA(path, "24 Boo b")
    print(x.frame.shape[0])
    print(x.read_refs())


# --------------------


if __name__ == "__main__":
    test()
