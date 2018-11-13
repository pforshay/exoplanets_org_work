"""
:title:  exoplanet_gui.py
:author:  Peter Forshay
:contact:  pforshay@stsci.edu

This code uses the PyQt library to construct a GUI for reading, modifying, and
writing files containing exoplanet data.  It does this using methods provided
by the ExoParameter and ExoPlanet classes.  This is intended to make editing
exoplanet files easier, faster, and more reliable, with some automatic
triggering of data-checking methods.

..class::  ExoParameterRow
..synopsis::  This class can construct a GUI row to contain information on a
              single expolanet parameter, and return the information contained
              in the row.

..class::  ExoPlanetPanel
..synopsis::  This widget will be used in the QScrollArea object to construct
              a series of ExoParameterRow objects.

..class::  ScrollWindow
..synopsis::  This class constructs a QScrollArea so the GUI will be able to
              scroll nicely along the many parameters used to define an
              exoplanet.

..class::  MainGUI
..synopsis::  This class defines the main body of a GUI for adding and
              updating exoplanet information to and from .pln files.  Methods
              are provided to read and write information between the GUI and
              these .pln files.
"""

from decimal import Decimal, InvalidOperation
from Exoplanet import ExoParameter, ExoPlanet
import os
import sys

try:
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
except ImportError:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *

# --------------------


class ExoParameterRow(QWidget):
    """
    This class can construct a GUI row to contain information on a single
    expolanet parameter, and return the information contained in the row.

    ..module::  return_parameter
    ..synopsis::  Read information from a row in the GUI and return it as a
                  dictionary.
    """

    # Set available reference and url pointers.
    refs = ["",
            "__FIRSTREF",
            "__ORBREF",
            "__INDEPORBREF",
            "__TRANSITREF",
            "__SPECREF",
            ]
    urls = ["",
            "__FIRSTURL",
            "__ORBURL",
            "__TRANSITURL",
            "__SPECURL",
            ]

    def __init__(self, parent=None, parameter=None):
        """
        Construct a new GUI row.

        :param parent:  A PyQt parent for the new GUI element.
        :type parent:  QWidget

        :param parameter:  Optionally pass the GUI an already-constructed
                           exoplanet parameter to populate the GUI elements.
        :type parameter:  ExoParameter
        """

        # Initialize as a QWidget object and set the background attribute to
        # allow alternating row coloring.
        super().__init__(parent)
        self.setAutoFillBackground(True)

        # Set GUI pixel widths.
        digits_width = 125
        text_width = 175

        # Initialize GUI elements.
        self.field = QLabel()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignRight)
        self.value = QLineEdit()
        self.value.setFixedWidth(digits_width)
        self.units = QLabel()
        self.units.setFixedWidth(85)
        self.uncertainty = QLineEdit()
        self.uncertainty.setFixedWidth(digits_width)
        self.uncertainty_upper = QLineEdit()
        self.uncertainty_upper.setFixedWidth(digits_width)
        self.uncertainty_lower = QLineEdit()
        self.uncertainty_lower.setFixedWidth(digits_width)
        self.reference = QComboBox()
        self.reference.addItems(self.refs)
        self.reference.setEditable(True)
        self.reference.setFixedWidth(text_width)
        self.url = QComboBox()
        self.url.addItems(self.urls)
        self.url.setEditable(True)
        self.url.setFixedWidth(text_width)

        # If an ExoParameter has been provided via parameter, use this to
        # populate the new GUI elements.
        if isinstance(parameter, ExoParameter):
            self.field.setText(parameter.parameter)
            self.label.setText(parameter.label)
            self.value.setText(str(parameter.value))
            self.units.setText(parameter.units)
            self.uncertainty.setText(str(parameter.uncertainty))
            self.uncertainty_upper.setText(str(parameter.uncertainty_upper))
            self.uncertainty_lower.setText(str(parameter.uncertainty_lower))

            # If parameter provides a new reference add this to the
            # self.reference dropdown, otherwise select the matching reference.
            ref = self.reference.findText(str(parameter.reference))
            if ref == -1:
                self.reference.insertItem(1, parameter.reference)
                self.reference.setCurrentIndex(1)
            else:
                self.reference.setCurrentIndex(ref)

            # If parameter provides a new link add this to the self.url
            # dropdown, otherwise select the matching link.
            url = self.url.findText(str(parameter.url))
            if url == -1:
                self.url.insertItem(1, parameter.url)
                self.url.setCurrentIndex(1)
            else:
                self.url.setCurrentIndex(url)

            # If parameter does not accept uncertainties, disable these GUI
            # elements.
            if not parameter.uncertain_flag:
                self.uncertainty.setText("N/A")
                self.uncertainty.setAlignment(Qt.AlignHCenter)
                self.uncertainty.setEnabled(False)
                self.uncertainty_upper.setText("N/A")
                self.uncertainty_upper.setAlignment(Qt.AlignHCenter)
                self.uncertainty_upper.setEnabled(False)
                self.uncertainty_lower.setText("N/A")
                self.uncertainty_lower.setAlignment(Qt.AlignHCenter)
                self.uncertainty_lower.setEnabled(False)

        # Construct the GUI layout.
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 3, 0, 3)
        hbox.addWidget(self.field)
        hbox.addWidget(self.label)
        hbox.addWidget(self.value)
        hbox.addWidget(self.units)
        hbox.addWidget(self.uncertainty)
        hbox.addWidget(self.uncertainty_upper)
        hbox.addWidget(self.uncertainty_lower)
        hbox.addWidget(self.reference)
        hbox.addWidget(self.url)

        # Add the layout to the row object.
        self.setLayout(hbox)

    def return_parameter(self):
        """
        Read information from a row in the GUI and return it as a dictionary.
        """

        # Initialize the dictionary and add the initial parameter information.
        d = {}
        d["parameter"] = self.field.text()

        # Add the value information as a Decimal if possible.
        val = self.value.text()
        try:
            d["value"] = Decimal(val)
        except InvalidOperation:
            d["value"] = val

        # Add the uncertainty information as a Decimal if possible.
        unc = self.uncertainty.text()
        try:
            d["uncertainty"] = Decimal(unc)
        except InvalidOperation:
            d["uncertainty"] = None

        # Add the uncertainty upper limit information as a Decimal if possible.
        unc_hi = self.uncertainty_upper.text()
        try:
            d["uncertainty_upper"] = Decimal(unc_hi)
        except InvalidOperation:
            d["uncertainty_upper"] = None

        # Add the uncertainty lower limit information as a Decimal if possible.
        unc_lo = self.uncertainty_lower.text()
        try:
            d["uncertainty_lower"] = Decimal(unc_lo)
        except InvalidOperation:
            d["uncertainty_lower"] = None

        # Add the reference and link information.
        d["reference"] = self.reference.currentText()
        d["url"] = self.url.currentText()

        return d

# --------------------


class ExoPlanetPanel(QWidget):
    """
    This widget will be used in the QScrollArea object to construct a series
    of ExoParameterRow objects.
    """

    def __init__(self, parent=None, planet=None):
        """
        Add all necessary rows to define an ExoPlanet.

        :param parent:  A PyQt parent for the new GUI element.
        :type parent:  QWidget

        :param planet:  Optionally pass the GUI an already-constructed
                        exoplanet object to populate the GUI elements.
        :type planet:  ExoPlanet
        """

        # Initialize as a QWidget object.
        super().__init__(parent)

        # If an ExoPlanet object is not provided, use an empty ExoPlanet.
        if not planet:
            planet = ExoPlanet()

        # Define the GUI layout for this widget.
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Add rows according to the ExoPlanet.pln_template dictionary.  Each
        # key is a section heading with a list of parameters as the value.
        n = 0
        for section, children in planet.pln_template.items():

            # Create a section separator row in the GUI.  Change the
            # background color depending on how far in we are.
            section_font = QFont()
            section_font.setBold(True)
            section_row = QLabel(section)
            section_row.setFont(section_font)
            if n == 0:
                section_row.setStyleSheet("background-color: #FFADAD")
            elif n == 1:
                section_row.setStyleSheet("background-color: #FFE1AD")
            elif n == 2:
                section_row.setStyleSheet("background-color: #EBFFAD")
            elif n == 3:
                section_row.setStyleSheet("background-color: #ADFFD0")
            elif n == 4:
                section_row.setStyleSheet("background-color: #ADE7FF")
            elif n == 5:
                section_row.setStyleSheet("background-color: #ADC0FF")
            elif n == 6:
                section_row.setStyleSheet("background-color: #CAADFF")
            self.scroll_layout.addWidget(section_row)

            # Now add a new GUI row for each parameter listed in children.
            light = True
            for attr in children:

                # Get the current ExoParameter object or skip if none is found.
                try:
                    exo_param = getattr(planet, attr.lower())
                except AttributeError:
                    continue

                # Create the new ExoParameterRow.
                new_row = ExoParameterRow(parent=parent, parameter=exo_param)

                # Alternate GUI row coloring between light and dark gray.
                if light:
                    light = not light
                else:
                    p = new_row.palette()
                    p.setColor(new_row.backgroundRole(), Qt.lightGray)
                    new_row.setPalette(p)
                    light = not light

                # Add the new row to the layout.
                self.scroll_layout.addWidget(new_row)

            n += 1

        self.setLayout(self.scroll_layout)

# --------------------


class ScrollWindow(QScrollArea):
    """
    This class constructs a QScrollArea so the GUI will be able to scroll
    nicely along the many parameters used to define an exoplanet.
    """

    def __init__(self, parent=None, planet=None):
        """
        Fill the QScrollArea with an ExoPlanetPanel widget.

        :param parent:  A PyQt parent for the new GUI element.
        :type parent:  QWidget

        :param planet:  Optionally pass the GUI an already-constructed
                        exoplanet object to populate the GUI elements.
        :type planet:  ExoPlanet
        """

        # Initialize as a QScrollArea object.
        super().__init__(parent)

        # Populate the scroll area with an ExoPlanetPanel and allow the user
        # to resize it as needed.
        self.setWidget(ExoPlanetPanel(parent=parent, planet=planet))
        self.setWidgetResizable(True)
        self.setFixedHeight(800)

# --------------------


class MainGUI(QWidget):
    """
    This class defines the main body of a GUI for adding and updating exoplanet
    information to and from .pln files.  Methods are provided to read and
    write information between the GUI and these .pln files.

    ..module::  _update_form
    ..synopsis::  Display an ExoPlanet object in the GUI.

    ..module::  clear_form
    ..synopsis::  Reset the GUI to an empty state.

    ..module::  load_pln
    ..synopsis::  Load information from an existing .pln file into the GUI.

    ..module::  write_pln
    ..synopsis::  Write the information currently displayed in the GUI to a
                  .pln file.
    """

    def __init__(self):

        # Initialize as a QWidget.
        super().__init__()

        current_dir = os.path.dirname(os.getcwd())
        self.default_dir = "/".join([current_dir, "generated_pln"])
        self.default_pref = "gen"

        # GUI elements for buttons to control resetting, loading, and reading
        # data to / from the GUI.
        clear = QPushButton("Clear the .pln Form")
        load = QPushButton("Load .pln File")
        save = QPushButton("Save As .pln File")
        dir_label = QLabel("Save Directory: ")
        self.dir_edit = QLineEdit()
        self.dir_edit.setText(self.default_dir)
        pref_label = QLabel("File Prefix: ")
        self.pref_edit = QLineEdit()
        self.pref_edit.setText(self.default_pref)

        # Arrange the input/output elements at the top of the GUI.
        self.top_panel = QGridLayout()
        self.top_panel.addWidget(load, 0, 0)
        self.top_panel.addWidget(dir_label, 0, 1)
        self.top_panel.addWidget(self.dir_edit, 0, 2)
        self.top_panel.addWidget(clear, 0, 3)
        self.top_panel.addWidget(save, 1, 0)
        self.top_panel.addWidget(pref_label, 1, 1)
        self.top_panel.addWidget(self.pref_edit, 1, 2)

        # GUI elements to add column header labels.  Widths are fixed
        # arbitrarily to line up with element placement in the ExoParameterRow
        # objects in the QScrollArea.
        bold = QFont()
        bold.setBold(True)
        h0 = QLabel("PARAMETER:")
        h0.setFixedWidth(450)
        h0.setFont(bold)
        h1 = QLabel("DESCRIPTION:")
        h1.setFixedWidth(100)
        h1.setFont(bold)
        h2 = QLabel("VALUE:")
        h2.setFixedWidth(120)
        h2.setFont(bold)
        h3 = QLabel("UNITS:")
        h3.setFixedWidth(90)
        h3.setFont(bold)
        h4 = QLabel("UNCERT(+/-):")
        h4.setFixedWidth(125)
        h4.setFont(bold)
        h5 = QLabel("ASYM_UNC(+):")
        h5.setFixedWidth(125)
        h5.setFont(bold)
        h6 = QLabel("ASYM_UNC(-):")
        h6.setFixedWidth(130)
        h6.setFont(bold)
        h7 = QLabel("REFERENCE:")
        h7.setFont(bold)
        h8 = QLabel("URL:")
        h8.setFont(bold)

        # Construct a layout for the column header labels.
        header = QHBoxLayout()
        header.addWidget(h0)
        header.addWidget(h1)
        header.addWidget(h2)
        header.addWidget(h3)
        header.addWidget(h4)
        header.addWidget(h5)
        header.addWidget(h6)
        header.addWidget(h7)
        header.addWidget(h8)

        # Add the main scrolling information display area.
        self.scroll = ScrollWindow(parent=self)

        # Construct the overall GUI layout.
        self.grid = QGridLayout()
        self.grid.addLayout(self.top_panel, 0, 0, 1, -1)
        self.grid.addLayout(header, 1, 0, 1, -1)
        self.grid.addWidget(self.scroll, 2, 0, 1, -1)

        # Connect the three action buttons.
        clear.clicked.connect(self.clear_form)
        load.clicked.connect(self.load_pln)
        save.clicked.connect(self.write_pln)

        # Display the GUI.
        self.setLayout(self.grid)
        self.resize(1600, 900)
        self.show()

    def _update_form(self, planet):
        """
        Display an ExoPlanet object in the GUI.

        :param planet:  The exoplanet to display in the GUI.
        :type planet:  ExoPlanet
        """

        # Delete the current scroll area by setting parent to None.
        self.scroll.setParent(None)

        # Construct a new ScrollWindow using the provided ExoPlanet.
        new_window = ScrollWindow(parent=self, planet=planet)

        # Add the new ScrollWindow to the GUI.
        self.scroll = new_window
        self.grid.addWidget(self.scroll, 2, 0, 1, -1)
        self.setLayout(self.grid)

    def clear_form(self):
        """
        Reset the GUI to an empty state.
        """

        # Update the GUI with an empty ExoPlanet object.
        planet = ExoPlanet()
        self._update_form(planet)

    def load_pln(self):
        """
        Load information from an existing .pln file into the GUI.
        """

        dir = self.dir_edit.text()

        # Use a popup dialog to get a .pln filename.
        loadit = QFileDialog.getOpenFileName(self,
                                             "Load a .pln file",
                                             dir
                                             )
        filename = loadit[0]

        # If no file is chosen, do nothing.  Otherwise, use the file to
        # construct an ExoPlanet.
        if filename == "":
            return
        else:
            planet = ExoPlanet(path=filename)

        # Add the new ExoPlanet object to the GUI.
        self._update_form(planet)

    def write_pln(self):
        """
        Write the information currently displayed in the GUI to a .pln file.
        """

        dir = self.dir_edit.text()
        dir = (self.default_dir if dir == "" else dir)
        if not os.path.isdir(dir):
            os.makedirs(dir)

        pref = self.pref_edit.text()

        # Initialize a new empty ExoPlanet object.
        new_planet = ExoPlanet()

        # Iterate through each ExoParameterRow in the ScrollWindow area.
        exo_panel = self.scroll.widget()
        rows = exo_panel.scroll_layout.count()
        for n in range(rows):
            exo_row = exo_panel.scroll_layout.itemAt(n).widget()

            # Use the ExoParameterRow method to read the information to a
            # dictionary.
            if isinstance(exo_row, ExoParameterRow):
                exo_dict = exo_row.return_parameter()
            else:
                continue

            # Use the ExoParameter method to update with the information in
            # the dictionary.
            parameter_name = exo_dict["parameter"].lower()
            exo_param = getattr(new_planet, parameter_name)
            exo_param.set_from_dict(exo_dict)

            # Update the ExoPlanet object with the updated ExoParameter.
            setattr(new_planet, parameter_name, exo_param)

        # Use ExoPlanet methods to verify and save the object to a .pln file.
        new_planet.verify_pln()
        new_planet.save_to_pln(dir=dir, pref=pref)

# --------------------


def __test__():
    test = ExoPlanet()
    app = QApplication(sys.argv)
    # w = ScrollWindow(planet=test)
    w = MainGUI()
    sys.exit(app.exec_())
    sys.stdout = sys.__stdout__

# --------------------


if __name__ == "__main__":
    __test__()
