from decimal import Decimal, InvalidOperation
import numpy as np
import os
import pandas as pd
import yaml

# --------------------


class ExoParameter(object):
    """
    The ExoParameter class is intended to define a single exoplanet parameter
    and a number of other properties that go along with it.  This includes
    value, uncertainties, default values, and units.
    """

    def __init__(self, parameter, attr_dict=None, from_template=None):
        """
        Initialize an ExoParameter object.

        :param parameter:  The name of this parameter, as expected by .pln
                           convention.
        :type parameter:  str

        :param attr_dict:  Optionally provide a dictionary to update the
                           attributes of this ExoParameter upon initialization.
        :type attr_dict:  dict

        :param from_template:  Use this flag if the ExoParameter is being
                               constructed from a template file.
        :type from_template:  bool
        """

        # --- Attributes currently in use ---
        # .pln files expect parameter names in all caps.
        self.parameter = str(parameter).upper()
        # Default parameter value.
        self.default = None
        # Where to find this parameter in data from http://exoplanet.eu .
        self.eu_field = None
        # A label to describe this parameter in exoplanet_gui.py .
        self.label = "N/A"
        # Where to find this parameter in data from
        # https://exoplanetarchive.ipac.caltech.edu .
        self.nasa_field = None
        # Which section this parameter falls under in standard .pln file
        # formatting.
        self.parent = "General Information"
        # Reference information for this parameter.  May be a paper label
        # (Forshay 2018) or a pointer (__FIRSTREF).
        self.reference = None
        # Store the default template information from exoparam_template.yaml .
        self.template = None
        # Flag whether or not this parameter can accept uncertainty
        # information.
        self.uncertain_flag = False
        # The mean +/- value uncertainty.
        self.uncertainty = None
        # The lower (-) value uncertainty.
        self.uncertainty_lower = None
        # The upper (+) value uncertainty.
        self.uncertainty_upper = None
        # The value units expected by .pln files for display in
        # exoplanet_gui.py .
        self.units = None
        # Reference link for this parameter.  This may be a url or a pointer
        # (__FIRSTURL).
        self.url = None
        # The value associated with this parameter.
        self.value = None
        # A flag to track whether this parameter is well-constrained.
        self.well_constrained = True

        # --- Attributes not currently in use ---
        # A list to store notes and curation decisions.
        self.comments = list()
        # Attributes to track acceptable limits and how to handle violations.
        self.limit_action = "warn"
        self.limit_lower = None
        self.limit_upper = None
        # Flag whether this parameter is required for exoplanet acceptance.
        self.required = False

        # If an attribute dictionary is provided, use the provided method to
        # update the attributes with this information.
        if attr_dict:
            self.set_from_template(attr_dict)

            # If this attribute is being constructed from a template, store
            # the attr_dict to reset back to template values if needed.
            if from_template:
                self.template = attr_dict

    def __lt__(self, another):
        """
        Define 'less than' for an ExoParameter object to allow for sorting by
        parameter name (not sure this is used currently).

        :param another:  Another ExoParameter to compare this one to.
        :type another:  ExoParameter
        """

        # Compare the parameter attributes of these objects if available.  If
        # not available, raise a TypeError.
        if isinstance(another, ExoParameter):
            return (self.parameter < another.parameter)
        else:
            raise TypeError("Tried to compare an ExoParameter object with "
                            "another class!")

    def __str__(self):
        """
        Construct a string representation for an ExoParameter if printed.
        """

        return "<ExoParameter>: {0}".format(self.__dict__)

    def calculate_uncertainties(self):
        """
        Calculate the uncertainties of this parameter.
        """

        # If this parameter does not allow uncertainties, set them to None.
        if not self.uncertain_flag:
            self.uncertainty = None
            self.uncertainty_lower = None
            self.uncertainty_upper = None
            return

        # If all uncertainties are empty, reset them to uncertainties provided
        # by the initial template construction.
        elif (is_empty(self.uncertainty) and
              is_empty(self.uncertainty_lower) and
              is_empty(self.uncertainty_upper)
              ):
            self.reset_uncertainties()
            return

        # If upper and lower uncertainties are provided, calculate the mean
        # uncertainty.
        elif (is_valid(self.uncertainty_lower)
              and is_valid(self.uncertainty_upper)
              ):
            u_hi = Decimal(self.uncertainty_upper)
            u_lo = Decimal(self.uncertainty_lower)
            u_avg = (u_lo + u_hi) / 2
            self.uncertainty = Decimal(u_avg)

        # If mean and upper uncertainties are provided, calculate ther lower
        # uncertainty.
        elif (is_valid(self.uncertainty) and is_valid(self.uncertainty_upper)):
            u_hi = Decimal(self.uncertainty_upper)
            u_avg = Decimal(self.uncertainty)
            u_lo = (2 * u_avg) - u_hi
            self.uncertainty_lower = Decimal(u_lo)

        # If only an upper uncertainty is provided, treat this as the mean.
        elif (is_empty(self.uncertainty) and is_valid(self.uncertainty_upper)):
            self.uncertainty = self.uncertainty_upper

        # If only a lower uncertainty is provided, treat this as the mean.
        elif (is_empty(self.uncertainty) and is_valid(self.uncertainty_lower)):
            self.uncertainty = self.uncertainty_lower

        else:
            return

    def check_constrained(self):
        """
        Set the well-constrained flag based on relative uncertainty percent.
        (not currently used)
        """

        # Set the 'well-constrained' limit at 10% (arbitrary).
        limit = 10

        if is_empty(self.value) or is_empty(self.uncertainty):
            return False
        elif self.uncertainty > (Decimal(self.value) / limit):
            self.well_constrained = False
        else:
            self.well_constrained = True
        return self.well_constrained

    def check_limits(self):
        """
        Compare the current value attribute to any limits provided for this
        parameter.  (not currently used)
        """

        too_hi = False
        too_lo = False
        if is_empty(self.value):
            return None

        # Check for limit violations.
        if not is_empty(self.limit_lower):
            too_lo = (self.value < self.limit_lower)
        if not is_empty(self.limit_upper):
            too_hi = (self.value > self.limit_upper)

        # If a limit is violated, return the designated limit action.
        if too_hi or too_lo:
            return self.limit_action
        else:
            return None

    def copy_values(self, another):
        """
        Copy data values from another ExoParameter without overwriting critical
        attributes.
        """

        # Copy all value, uncertainty, and source information from the other
        # ExoParameter object.
        if isinstance(another, ExoParameter):
            self.reference = another.reference
            self.uncertainty = another.uncertainty
            self.uncertainty_lower = another.uncertainty_lower
            self.uncertainty_upper = another.uncertainty_upper
            self.units = another.units
            self.url = another.url
            self.value = another.value
        else:
            raise TypeError("Cannot copy values from a non-ExoParameter obj!")

    def reset_parameter(self):
        """
        Reset this parameter to the original template attributes.
        """

        # Set self to a new ExoParameter using the original self.template
        # dictionary.
        self = ExoParameter(self.parameter, attr_dict=self.template)

    def reset_uncertainties(self):
        """
        Reset the uncertainty values of this parameter from the original
        template uncertainties.
        """

        # Make a new temporary ExoParameter using the original self.template
        # dictionary and copy the uncertainty values.
        blank = ExoParameter("fake", attr_dict=self.template)
        self.uncertainty = blank.uncertainty
        self.uncertainty_lower = blank.uncertainty_lower
        self.uncertainty_upper = blank.uncertainty_upper

    def set_from_template(self, attribute_dict):
        """
        Update the attributes of this ExoParameter using a provided dictionary.
        """

        # Iterate through each attribute / value pair in the dictionary.
        for attr, value in attribute_dict.items():

            # Use None if this is not a current attribute of self.
            try:
                old_value = getattr(self, attr)
            except AttributeError:
                old_value = None

            # Uncertainty values from the GUI will either be None or Decimals.
            # We want to prevent overwriting "NaN" with None.
            if (value is None and is_empty(old_value)):
                continue

            # Update self.
            setattr(self, attr, value)

        # If no value is provided, set to default.
        if self.value is None:
            self.value = self.default

# --------------------


class Exoplanet(object):
    """
    The Exoplanet class is intended to hold a number of parameters that define
    an exoplanet within the exoplanets.org workflow.  This includes functions
    for reading and writing parameters in .pln text files, and may be extended
    to additional formats and parameter calculations.
    """

    # Point to exissting template files.
    pln_template_file = "ref/pln_template.yaml"
    template_file = "ref/exoparam_template.yaml"

    def __init__(self, path=None):
        """
        Create an exoplanet object and optionally seed it with parameters
        already in hand.

        :param path:  A filepath may be supplied to create an Exoplanet object
                      from an existing .pln file.
        :type path:  str
        """

        # Initialize the Exoplanet object with an empty 'attributes' list.
        self.attributes = []

        # Load the YAML-formatted template file.
        with open(self.template_file, 'r') as template:
            template_parameters = yaml.load(template)

        # For each attribute defined in the template file, add this attribute
        # to the Exoplanet object and link it to a new ExoParameter defined
        # by the information supplied.
        for param, attributes in template_parameters.items():
            setattr(self, param.lower(), ExoParameter(param,
                                                      attr_dict=attributes,
                                                      from_template=True,
                                                      )
                    )
            self.attributes.append(param.lower())

        # If an existing .pln file is provided, read this file information.
        if path:
            self.read_from_pln(path)

        # Add the YAML-formatted contents of 'self.pln_template_file' to an
        # attribute of this object.
        with open(self.pln_template_file, 'r') as yamlstream:
            self.pln_template = yaml.load(yamlstream)

    def __str__(self):
        """
        Format an Exoplanet string if requested.
        """

        return "<Exoplanet>: {0}".format(self.__dict__)

    def _populate_uncertainties(self):
        """
        Trigger uncertainty calculations for all attributes.
        """

        # Use the ExoParameter method to calculate uncertainties for all
        # attributes of self.
        for att in self.attributes:
            exo_param = getattr(self, att)
            exo_param.calculate_uncertainties()

    def _write_pln_line(self, file, field, value):
        """
        Format a line with whitespace and write this to the .pln file.

        :param file:  The .pln file being written to.
        :type file:  str

        :param field:  The keyword being written (should already be all-caps).
        :type field:  str

        :param value:  The value being written.
        :type field:  various
        """

        field_str = "{:25}".format(field)
        value_str = str(value)
        value_str = ("" if value_str == "None" else value_str)
        value_str = ("NaN" if value_str == "nan" else value_str)
        file.write("".join([field_str, value_str, "\n"]))

    def exclude(self):
        """
        Set the two data inclusion flags to 0 so this exoplanet does not appear
        in EOD.
        """

        self.eod.value = 0
        self.public.value = 0

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
                       "SIMBADNAME",
                       ]
        all_names = []

        for field in name_fields:
            field = field.lower()
            if field in self.attributes:
                parameter = getattr(self, field)
                name = parameter.value
            if name == "":
                continue
            all_names.append(name)

        # Store the list of names as a new object attribute, in addition to
        # returning the list.
        self.all_names = list(set(all_names))
        return self.all_names

    def read_from_nasa(self, nasa_series):
        """
        Construct an Exoplanet from data scraped from the NASA Exoplanet
        Archive.
        """

        # Transform the Pandas Series containing NASA parameters into a dict.
        nasa_dict = nasa_series.to_dict()

        # Look for every attribute added during Exoplanet initialization.
        for att in self.attributes:

            # getattr will return an ExoParameter object for this attribute.
            exo_param = getattr(self, att)

            # Check for a corresponding data field in the NASA data.
            nasa_field = exo_param.nasa_field
            if nasa_field is None:
                continue

            # Get the NASA value and apply some changes based on which
            # ExoParameter we are working on.
            new_value = nasa_dict[nasa_field]
            if is_empty(new_value):
                new_value = exo_param.default
            elif nasa_field == "dec_str":
                new_value = new_value.replace("d", " ")
                new_value = new_value.replace("m", " ")
                new_value = new_value[:-1]
            elif nasa_field == "hd_name":
                new_value = " ".join(new_value.split(" ")[1:])
            elif nasa_field == "hip_name":
                new_value = " ".join(new_value.split(" ")[1:])
            elif nasa_field == "pl_trandep" and not is_empty(new_value):
                new_value = Decimal(new_value) / 100
            elif nasa_field == "ra_str":
                new_value = new_value.replace("h", " ")
                new_value = new_value.replace("m", " ")
                new_value = new_value[:-1]
            elif nasa_field == "st_nrvc" and new_value == "0":
                new_value = -1

            # Try changing the new value into a Decimal.
            try:
                exo_param.value = Decimal(new_value)
            except (InvalidOperation, TypeError):
                exo_param.value = new_value

            # Try looking for corresponding uncertainty values in the NASA
            # data.
            if exo_param.uncertain_flag:
                nasa_err1 = "".join([nasa_field, "err1"])
                nasa_err2 = "".join([nasa_field, "err2"])
                try:
                    shi = str(nasa_dict[nasa_err1])
                    exo_param.uncertainty_upper = Decimal(shi)
                    slo = str(nasa_dict[nasa_err2])
                    exo_param.uncertainty_lower = Decimal(slo) * -1
                except KeyError:
                    pass

            # Reset the current Exoplanet attribute to the now-updated
            # ExoParameter.
            setattr(self, att, exo_param)

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
                if keyword_value_pair[0].startswith('#'):
                    continue

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

                # Examine the keyword.  Current .pln formatting specifies the
                # uncertainty keywords begin with 'U', uncertainty
                # upper-limits end with 'D', references end with 'REF', and
                # links end with 'URL'.
                keyword = keyword_value_pair[0].lower()
                if "transit" in keyword:
                    attribute = "value"
                elif keyword[0] == "u" and keyword[1:] in self.attributes:
                    keyword = keyword[1:]
                    attribute = "uncertainty"
                elif (keyword[0] == "u"
                      and keyword[-1] == "d"
                      and keyword[1:-1] in self.attributes):
                    keyword = keyword[1:-1]
                    attribute = "uncertainty_upper"
                elif (keyword[-3:] == "ref"
                      and keyword[:-3] in self.attributes):
                    keyword = keyword[:-3]
                    attribute = "reference"
                elif (keyword[-3:] == "url"
                      and keyword[:-3] in self.attributes):
                    keyword = keyword[:-3]
                    attribute = "url"
                else:
                    attribute = "value"

                # If this keyword exists as an ExoParameter, set the
                # designated attribute and value.
                try:
                    param = getattr(self, keyword)
                    setattr(param, attribute, value)
                except AttributeError:
                    pass

        self._populate_uncertainties()

    def save_to_pln(self, name=None, dir=None, gui=False, disp=True):
        """
        Save an Exoplanet object into a .pln text file.  A .pln template is
        needed here to recreate the sections of the text file and where to
        write each parameter.

        :param name:  The file name for the resulting .pln file.  This will be
                      automatically set to the exoplanet name if not provided,
                      but the user may supply a different name for testing.
        :type name:  str

        :param gui:  Flag used to alter the filename if this file is being
                     generated by the GUI.
        :type gui:  bool
        """

        # Set the file name to the exoplanet name if not provided.
        if not name:
            name = ".".join([self.name.value, "pln"])
        if gui:
            name = "_".join(["gen", name])
        if dir:
            name = os.path.join(dir, name)
            home = os.getcwd()
            name = os.path.join(home, name)

        if os.path.isfile(name):
            os.remove(name)

        with open(name, 'w') as new_pln:
            if disp:
                print("writing to {0}".format(name))

            # Use the pln_template dictionary to create the file sections and
            # look up the names that may be in the parameters dictionary.
            for section, fields in self.pln_template.items():

                # Recreate the section header for each new section.
                comment = "#* "
                separator = "=" * 48
                new_pln.write("".join([comment, separator, "\n"]))
                new_pln.write("".join([comment, section, "\n"]))
                new_pln.write("".join([comment, separator, "\n"]))

                # Look for attributes that match the field names defined in
                # the .pln template.
                for f in fields:
                    try:
                        exo_param = getattr(self, f.lower())
                    except AttributeError:
                        continue

                    # exo_param is now an ExoParameter object.  Add the
                    # keyword & value pair to the .pln file.
                    if is_empty(exo_param.value):
                        exo_param.value = exo_param.default
                    self._write_pln_line(new_pln, f, exo_param.value)

                    # Add additional keywords for uncertainties and references
                    # if they are present in the current ExoParameter.
                    if exo_param.uncertainty:
                        uf = "".join(["U", f])
                        self._write_pln_line(new_pln,
                                             uf,
                                             exo_param.uncertainty
                                             )
                    if exo_param.uncertainty_upper:
                        ufd = "".join(["U", f, "D"])
                        self._write_pln_line(new_pln,
                                             ufd,
                                             exo_param.uncertainty_upper
                                             )
                    if exo_param.reference:
                        fref = "".join([f, "REF"])
                        self._write_pln_line(new_pln,
                                             fref,
                                             exo_param.reference
                                             )
                    if exo_param.url:
                        furl = "".join([f, "URL"])
                        self._write_pln_line(new_pln,
                                             furl,
                                             exo_param.url
                                             )

    def save_to_yaml(self, path=None):
        """
        Save an Exoplanet object to a YAML-formatted file.  This is not
        currently in use by any routines.

        :param path:  An optional kwarg to specify a certain file name/path to
                      save the resulting YAML file.
        :type path:  str
        """

        if not path:
            path = ".".join([self.name.value, "yaml"])

        planet_dict = {}
        for a in sorted(self.attributes):
            exo_param = getattr(self, a)
            param_dict = exo_param.__dict__
            param_dict = {k: str(v)
                          for k, v in param_dict.items()
                          if v and len(str(v)) > 0}
            planet_dict[a] = param_dict

        with open(path, 'w') as yamlfile:
            yaml.dump(planet_dict, yamlfile, default_flow_style=False)

    def verify_pln(self):
        """
        Some last-second tweaks are needed for proper .pln file formatting.
        """

        warnings = []

        self._populate_uncertainties()

        # The transitref and transiturl actually end up stored in the 'transit'
        # ExoParam due to the ref and url splits.  Pull these out and set the
        # transit entries to the proper pointers.
        if self.transit.value == 1:
            if is_empty(self.transit.reference):
                self.transit.reference = "__TRANSITREF"
            if is_empty(self.transit.url):
                self.transit.url = "__TRANSITURL"

        # If the transit depth is not provided, but an Rp/R* ratio is,
        # calculate the depth value.
        if is_empty(self.depth.value) and not is_empty(self.rr.value):
            self.depth.value = self.rr.value ** 2
            if isinstance(self.rr.uncertainty, Decimal):
                self.depth.uncertainty = self.rr.uncertainty * 2
            if isinstance(self.rr.uncertainty_upper, Decimal):
                self.depth.uncertainty_upper = self.rr.uncertainty_upper * 2
            self.depth.reference = "Calculated from Rp/R*"
            self.depth.url = None

        # If the orbital eccentricity value is 0 and a TT value is provided,
        # use the same values for T0 as well.
        if self.ecc.value == Decimal(0) and is_empty(self.om.value):
            self.om.value = Decimal(90)
            self.om.reference = "Set to 90 deg with ecc~0"
            print("set omega to 90")
            if str(self.tt.value) != "NaN":
                print("copying TT to T0")
                self.t0.copy_values(self.tt)
        # OM may already be set to 90.
        elif self.ecc.value == 0 and self.om.value == 90:
            if str(self.tt.value) != "NaN":
                print("copying TT to T0")
                self.t0.copy_values(self.tt)

        # Set the FREEZE_ECC flag if ECC=0 and no uncertainty is provided.
        if self.ecc.value == 0 and is_empty(self.ecc.uncertainty):
            self.freeze_ecc.value = 1

        # Set the MULT flag if NCOMP is more than 1 planet.
        if self.ncomp.value > 1:
            self.mult.value = 1

        # Set the TREND flag if a DVDT value is provided.
        if not is_empty(self.dvdt.value):
            self.trend.value = 1

        # Exclude planets with period uncertainty >10%.
        if not self.per.well_constrained:
            self.exclude()
            warnings.append("<uncertain PER>")

        # Warn of planets with K speeds <2 m/s.
        if not is_empty(self.k.value):
            if self.k.value < 2:
                # self.exclude()
                warnings.append("<low K value>")

        # Make sure RA string uses colons.
        if not is_empty(self.ra_string.value):
            if "h" in self.ra_string.value:
                new_value = self.ra_string.value.replace("h", " ")
                new_value = new_value.replace("m", " ")
                new_value = new_value.replace("s", "")
                self.ra_string.value = new_value

        # Make sure DEC string uses colons.
        if not is_empty(self.dec_string.value):
            if "d" in self.dec_string.value:
                new_value = self.dec_string.value.replace("d", " ")
                new_value = new_value.replace("m", " ")
                new_value = new_value.replace("s", "")
                self.dec_string.value = new_value

        # Display warnings generated by final adjustments.
        if len(warnings) > 0:
            print("<<<{0} GOT {1} WARNING(S)>>>".format(self.name.value,
                                                        len(warnings)
                                                        )
                  )
            [print(x) for x in warnings]

        """
        if (is_empty(self.t0.value)
                and not is_empty(self.tt.value)
                and not is_empty(self.om.value)
                and not is_empty(self.ecc.value)):
            p = float(self.per.value)
            sig = len(str(self.tt.value))
            tc = float(self.tt.value)
            rad = np.radians(float(self.om.value))
            f = (np.pi / 2) - rad
            if f != 0:
                ec = float(self.ecc.value)
                ea = 2 * np.arctan(np.tan(f/2) * np.sqrt((1-ec) / (1+ec)))
                tp = tc - (p / (2*np.pi)) * (ea - ec * np.sin(ea))
                tp = np.round(tp, decimals=(sig-6))
                print("------------{}".format(tp))
                self.t0.value = Decimal(str(tp))
                self.t0.uncertainty = self.tt.uncertainty
                self.t0.uncertainty_upper = self.tt.uncertainty_upper
                self.t0.reference = "Computed from TT"
                self.t0.url = None
                print("T0 computed from TT")
        """

# --------------------


def is_valid(var):
    """
    Just return the opposite of is_empty().  This is easier to keep track of
    in more complex boolean statements.
    """

    return (not is_empty(var))


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

# --------------------


def __test__():
    p = ExoParameter("Name")
    p.add_comment("TBD")
    print(p)

    testfile = "HD 209458 b.pln"
    ep = Exoplanet(path=testfile)
    ep.save_to_yaml(path="rewrite.yaml")


def __test_exoparameter__():
    template = "exoparam_template.yaml"
    with open(template, 'r') as yamlstream:
        param_template = yaml.load(yamlstream)
    results = [ExoParameter(k, attr_dict=v) for k, v in param_template.items()]
    [print(r) for r in sorted(results)]


def __test_exoplanet_from_template__():
    testfile = "HD 209458 b.pln"
    new_planet = Exoplanet(path=testfile)
    print(new_planet.per)

# --------------------


if __name__ == "__main__":
    __test__()
