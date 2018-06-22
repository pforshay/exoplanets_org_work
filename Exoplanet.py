import yaml


class ExoParameter(object):
    """
    The ExoParameter class is intended to define an exoplanet parameter and a
    number of other properties that go along with it.  This includes value
    uncertainties, default values, and units.  Not a lot has been done with
    this class in practice yet.
    """

    def __init__(self, parameter, value=None, default=None, units=None):
        self.parameter = str(parameter).upper()
        self.default = default
        self.value = value if value else default
        self.units = units
        self.comments = []
        self.nasa_field = None
        self.eu_field = None
        self.uncertainty = None
        self.uncertainty_spread = None
        self.uncertainty_upper = None

    def __str__(self):
        return "<ExoParameter>: {0}".format(self.__dict__)

    def add_comment(self, comment):
        self.comments.append(comment)

    def rm_comment(self, index):
        del self.comments[index]


class Exoplanet(object):
    """
    The Exoplanet class is intended to hold a number of parameters that define
    an exoplanet within the exoplanets.org workflow.  This includes functions
    for reading and writing parameters in .pln text files, and may be extended
    to additional formats and parameter calculations.
    """

    def __init__(self, parameters=None, path=None):
        """
        Create an exoplanet object and optionally seed it with parameters
        already in hand.

        :param parameters:  If the user already has exoplanet parameters
                            stored in a dictionary, they may pass it during
                            creation using this field.
        :type parameters:  dict

        :param path:  A filepath may be supplied to create an Exoplanet object
                      from an existing .pln file.
        :type path:  str
        """

        # Ingest parameters from either the parameters variable or a .pln file
        # supplied in path.
        self.parameters = parameters if parameters else {}
        if path:
            self.read_from_pln(path)

        # The pln template should define the major sections of the file and
        # where to store / find each parameter.  This could become a class
        # property, though it is lengthy.
        pln_template_file = "pln_template.yaml"
        with open(pln_template_file, 'r') as yamlstream:
            self.pln_template = yaml.load(yamlstream)

    def __str__(self):
        """
        Return the self.parameters dictionary if a user tries to print an
        Exoplanet object.
        """

        return "<Exoplanet>: {0}".format(self.parameters)

    def find_all_names(self):
        """
        Aggregate all the potential exoplanet names stored in pln file fields.
        """

        if self.parameters is None:
            return None

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
                name = self.parameters[field]
            except KeyError:
                continue
            if name == "":
                continue
            all_names.append(name)

        # Store the list of names as a new object attribute, in addition to
        # returning the list.
        self.all_names = list(set(all_names))
        return self.all_names

    def read_from_pln(self, path):
        """
        Read exoplanet parameters from a .pln file assuming certain commenting
        and text structures.  This can be done without a .pln template.

        :param path:  File path to the desired .pln file.
        :type path:  str
        """

        with open(path, encoding='latin-1') as f:
            for line in f:
                line = line.strip()

                # Parameter names and values are separated by whitespace, so
                # split the line on this.
                keyword_value_pair = [x.strip() for x in line.split(' ', 1)]

                # Comment lines begin with '#'.
                if not keyword_value_pair[0].startswith('#'):
                    num = len(keyword_value_pair)

                    # Skip if this line is empty.
                    if num == 0:
                        continue

                    # Use an empty string if this keyword has no value.
                    keyword = keyword_value_pair[0]
                    if num == 1:
                        value = ''

                    # Assign the value if present.
                    elif num == 2:
                        value = keyword_value_pair[1]

                        # Try turning the value into an integer or float.
                        try:
                            value = (int(value) if float(value).is_integer()
                                     else float(value)
                                     )
                        except ValueError:
                            pass

                    # Add this pair to the parameters dictionary.
                    self.parameters[keyword] = value

    def save_to_pln(self, path=None):
        """
        Save an Exoplanet object into a .pln text file.  Needs more work to
        ensure significant digits are preserved.  A .pln template is needed
        here to recreate the sections of the text file and where to write each
        parameter.

        :param path:  The file path for the resulting .pln file.  This will be
                      automatically set to the exoplanet name if not provided,
                      but the user may supply a different path for testing.
        :type path:  str
        """

        # Set the file path to the exoplanet name if not provided.
        if not path:
            path = ".".join([self.parameters['NAME'], "pln"])

        with open(path, 'w') as new_pln:
            print("writing to {0}".format(path))

            # Use the pln_template dictionary to create the file sections and
            # look up the names that may be in the parameters dictionary.
            for section, fields in self.pln_template.items():

                # Recreate the section header for each new section.
                comment = "#* "
                separator = "=" * 48
                new_pln.write("".join([comment, separator, "\n"]))
                new_pln.write("".join([comment, section, "\n"]))
                new_pln.write("".join([comment, separator, "\n"]))

                # Look for parameters in the parameters dictionary that match
                # the field names defined in the .pln template.
                for f in fields:
                    try:
                        value = str(self.parameters[f])
                    except KeyError:
                        continue

                    # Add whitespace between the keyword and value, then write
                    # a new line to the .pln file.
                    p_str = "{:25}".format(f)
                    new_pln.write("".join([p_str, value, "\n"]))

    def save_to_yaml(self):
        pass


def __test__():
    p = ExoParameter("Name", value="new")
    p.add_comment("TBD")
    print(p)

    testfile = "HD 209458 b.pln"
    ep = Exoplanet(path=testfile)
    ep.save_to_pln(path="rewrite.pln")


if __name__ == "__main__":
    __test__()
