from decimal import Decimal, InvalidOperation
from Exoplanet import ExoParameter, Exoplanet
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
    expolanet parameter.  Methods are provided to read and write information
    between the GUI and Exoplanet objects.
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
            ref = self.reference.findText(parameter.reference)
            if ref == -1:
                self.reference.insertItem(1, parameter.reference)
                self.reference.setCurrentIndex(1)
            else:
                self.reference.setCurrentIndex(ref)

            # If parameter provides a new link add this to the self.url
            # dropdown, otherwise select the matching link.
            url = self.url.findText(parameter.url)
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
        Add all necessary rows to define an Exoplanet.

        :param parent:  A PyQt parent for the new GUI element.
        :type parent:  QWidget

        :param planet:  Optionally pass the GUI an already-constructed
                        exoplanet object to populate the GUI elements.
        :type planet:  Exoplanet
        """

        # Initialize as a QWidget object.
        super().__init__(parent)

        # If an Exoplanet object is not provided, use an empty Exoplanet.
        if not planet:
            planet = Exoplanet()

        # Define the GUI layout for this widget.
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Add an ExoParameterRow for each Exoplanet attribute.
        light = True
        for attr in planet.attributes:
            exo_param = getattr(planet, attr)
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
        :type planet:  Exoplanet
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
    """

    def __init__(self):

        # Initialize as a QWidget.
        super().__init__()

        # GUI elements for buttons to control resetting, loading, and reading
        # data to / from the GUI.
        clear = QPushButton("Clear the .pln Form")
        load = QPushButton("Load .pln File")
        save = QPushButton("Save As .pln File")

        # GUI elements to add column header labels.  Widths are fixed
        # arbitrarily to line up with element placement in the ExoParameterRow
        # objects in the QScrollArea.
        h0 = QLabel("PARAMETER:")
        h0.setFixedWidth(440)
        h1 = QLabel("DESCRIPTION:")
        h1.setFixedWidth(100)
        h2 = QLabel("VALUE:")
        h2.setFixedWidth(120)
        h3 = QLabel("UNITS:")
        h3.setFixedWidth(90)
        h4 = QLabel("UNCERT(+/-):")
        h4.setFixedWidth(130)
        h5 = QLabel("ASYM_UNC(+):")
        h5.setFixedWidth(130)
        h6 = QLabel("ASYM_UNC(-):")
        h6.setFixedWidth(120)
        h7 = QLabel("REFERENCE:")
        h8 = QLabel("URL:")

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
        self.grid.addWidget(load, 0, 0)
        self.grid.addWidget(save, 0, 1)
        self.grid.addWidget(clear, 0, 2)
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
        Display an Exoplanet object in the GUI.

        :param planet:  The exoplanet to display in the GUI.
        :type planet:  Exoplanet
        """

        # Delete the current scroll area by setting parent to None.
        self.scroll.setParent(None)

        # Construct a new ScrollWindow using the provided Exoplanet.
        new_window = ScrollWindow(parent=self, planet=planet)

        # Add the new ScrollWindow to the GUI.
        self.scroll = new_window
        self.grid.addWidget(self.scroll, 2, 0, 1, -1)
        self.setLayout(self.grid)

    def clear_form(self):
        """
        Reset the GUI to an empty state.
        """

        # Update the GUI with an empty Exoplanet object.
        planet = Exoplanet()
        self._update_form(planet)

    def load_pln(self):
        """
        Load information from an existing .pln file into the GUI.
        """

        # Use a popup dialog to get a .pln filename.
        loadit = QFileDialog.getOpenFileName(self, "Load a .pln file", ".")
        filename = loadit[0]

        # If no file is chosen, do nothing.  Otherwise, use the file to
        # construct an Exoplanet.
        if filename == "":
            return
        else:
            planet = Exoplanet(path=filename)

        # Add the new Exoplanet object to the GUI.
        self._update_form(planet)

    def write_pln(self):
        """
        Write the information currently displayed in the GUI to a .pln file.
        """

        # Initialize a new empty Exoplanet object.
        new_planet = Exoplanet()

        # Iterate through each ExoParameterRow in the ScrollWindow area.
        exo_panel = self.scroll.widget()
        rows = exo_panel.scroll_layout.count()
        for n in range(rows):
            exo_row = exo_panel.scroll_layout.itemAt(n).widget()

            # Use the ExoParameterRow method to read the information to a
            # dictionary.
            exo_dict = exo_row.return_parameter()

            # Use the ExoParameter method to update with the information in
            # the dictionary.
            parameter_name = exo_dict["parameter"].lower()
            exo_param = getattr(new_planet, parameter_name)
            exo_param.set_from_template(exo_dict)

            # Update the Exoplanet object with the updated ExoParameter.
            setattr(new_planet, parameter_name, exo_param)

        # Use Exoplanet methods to verify and save the object to a .pln file.
        new_planet.verify_pln()
        new_planet.save_to_pln(dir="../generated_pln", gui=True)


def __test__():
    test = Exoplanet()
    app = QApplication(sys.argv)
    # w = ScrollWindow(planet=test)
    w = MainGUI()
    sys.exit(app.exec_())
    sys.stdout = sys.__stdout__


if __name__ == "__main__":
    __test__()
