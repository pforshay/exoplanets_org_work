"""
:title:  read_pln_file.py
:author:  Peter Forshay
:contact:  pforshay@stsci.edu

This code can be used to read a .pln formatted file used by exoplanets.org into
a Python dictionary object.  This is used by the ExoPlanet class for the
initial file ingestion step, and further translation steps are done in-class.

..module::  read_pln_file
..synopsis::  Read a .pln formatted file into a dictionary.
"""

from decimal import Decimal, InvalidOperation

# --------------------


def read_pln_file(path):
    """
    Read a .pln formatted file into a dictionary.

    :param path:  The file path of the target .pln file.
    :type path:  str
    """

    # Prepare an empty results dictionary.
    pln_dict = {}

    # Open the given file and begin stepping through line by line.
    with open(path, encoding='latin-1') as f:
        for line in f:
            line = line.strip()

            # Comment lines begin with '#', so skip these.
            if line.startswith('#'):
                continue

            # Parameter names and values are separated by whitespace, so
            # split the line on this.
            keyword_value_pair = [x.strip() for x in line.split(' ', 1)]
            num = len(keyword_value_pair)

            # Skip if this line is empty.
            if num == 0:
                continue

            # Use an empty string if this keyword has no value.
            if num == 1:
                value = ''

            # Assign the value if present.
            elif num == 2:
                value = str(keyword_value_pair[1])
                value = (None if value == "None" else value)

                # Try turning the value into a Decimal (this will
                # preserve significant figures).
                try:
                    value = Decimal(value)
                except (InvalidOperation, TypeError):
                    pass

            # Add the new keyword / value to the results dictionary.
            keyword = keyword_value_pair[0].lower()
            pln_dict[keyword] = value

    return pln_dict
