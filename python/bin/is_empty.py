"""
:title:  is_empty.py
:author:  Peter Forshay
:contact:  pforshay@stsci.edu

Different operations within the ExoPlanet and ExoParameter classes use
differing values for empty / null results.  These include 'NaN', None, and ''.
In many of these operations, we want to simply filter for any of these values.

..module::  is_empty
..synopsis::  Various ExoPlanet attributes use 'NaN', 'None', or '' for empty
              values.  Check for all these cases.

..module::  is_valid
..synopsis::  Just return the opposite of is_empty().  This is easier to keep
              track of in more complex boolean statements.
"""


def is_empty(var):
    """
    Various ExoPlanet attributes use 'NaN', 'None', or '' for empty values.
    Check for all these cases.

    :param var:  Variable value to check.
    :type var:  various
    """

    # Get the lowercase string value of var.
    as_str = str(var).lower()

    # Look for instances 'nan', 'none', or ''.
    if (as_str == "nan" or as_str == "none" or as_str == ""):
        return True
    else:
        return False


def is_valid(var):
    """
    Just return the opposite of is_empty().  This is easier to keep track of
    in more complex boolean statements.

    :param var:  Variable value to check.
    :type var:  various
    """

    return (not is_empty(var))
