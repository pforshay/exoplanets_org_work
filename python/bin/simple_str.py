def simple_str(name):
    """
    Reduce a provided string to lower-case letters and numbers.

    :param name:  The target name to reduce.
    :type name:  str
    """

    # Remove any preceeding or following whitespace and reduct to lower case.
    name = str(name).strip().lower()

    # Remove any symbols or spaces from the string.
    name = "".join(n for n in name if n.isalnum())

    return name
