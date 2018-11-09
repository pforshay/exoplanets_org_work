def is_empty(var):
    """
    Various Exoplanet attributes use 'NaN', 'None', or '' for empty values.
    Check for all these cases.
    """

    as_str = str(var).lower()
    if (as_str == "nan" or as_str == "none" or as_str == ""):
        return True
    else:
        return False


def is_valid(var):
    """
    Just return the opposite of is_empty().  This is easier to keep track of
    in more complex boolean statements.
    """

    return (not is_empty(var))
