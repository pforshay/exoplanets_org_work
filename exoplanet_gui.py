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


class ExoParameterRow(QWidget):

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
        super().__init__(parent)
        self.setAutoFillBackground(True)

        digits_width = 125
        text_width = 175
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

        if isinstance(parameter, ExoParameter):
            self.field.setText(parameter.parameter)
            self.label.setText(parameter.label)
            self.value.setText(str(parameter.value))
            self.units.setText(parameter.units)
            self.uncertainty.setText(str(parameter.uncertainty))
            self.uncertainty_upper.setText(str(parameter.uncertainty_upper))
            ref = self.reference.findText(parameter.reference)
            if ref == -1:
                self.reference.insertItem(1, parameter.reference)
                self.reference.setCurrentIndex(1)
            else:
                self.reference.setCurrentIndex(ref)
            url = self.url.findText(parameter.url)
            if url == -1:
                self.url.insertItem(1, parameter.url)
                self.url.setCurrentIndex(1)
            else:
                self.url.setCurrentIndex(url)

        if self.uncertainty.text() == "None":
            self.uncertainty.setText("N/A")
            self.uncertainty.setAlignment(Qt.AlignHCenter)
            self.uncertainty.setEnabled(False)
            self.uncertainty_upper.setText("N/A")
            self.uncertainty_upper.setAlignment(Qt.AlignHCenter)
            self.uncertainty_upper.setEnabled(False)
            self.uncertainty_lower.setText("N/A")
            self.uncertainty_lower.setAlignment(Qt.AlignHCenter)
            self.uncertainty_lower.setEnabled(False)

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

        # self.setStyleSheet("background-color: red")
        self.setLayout(hbox)

    def return_parameter(self):
        d = {}
        d["parameter"] = self.field.text()

        val = self.value.text()
        try:
            d["value"] = Decimal(val)
        except InvalidOperation:
            d["value"] = val

        unc = self.uncertainty.text()
        try:
            d["uncertainty"] = Decimal(unc)
        except InvalidOperation:
            d["uncertainty"] = None

        unc_hi = self.uncertainty_upper.text()
        try:
            d["uncertainty_upper"] = Decimal(unc_hi)
        except InvalidOperation:
            d["uncertainty_upper"] = None

        unc_lo = self.uncertainty_lower.text()
        try:
            unc_lo = Decimal(unc_lo)
            unc = (d["uncertainty_upper"] + unc_lo) / 2
            d["uncertainty"] = unc
        except InvalidOperation:
            pass

        d["reference"] = self.reference.currentText()
        d["url"] = self.url.currentText()

        return d


class ExoPlanetPanel(QWidget):

    def __init__(self, parent=None, planet=None):
        super().__init__(parent)
        if not planet:
            planet = Exoplanet()

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        light = True
        for attr in planet.attributes:
            exo_param = getattr(planet, attr)
            new_row = ExoParameterRow(parent=parent, parameter=exo_param)
            if light:
                light = not light
            else:
                p = new_row.palette()
                p.setColor(new_row.backgroundRole(), Qt.lightGray)
                new_row.setPalette(p)
                light = not light
            # new_row = QLabel(exo_param.parameter)
            self.scroll_layout.addWidget(new_row)

        self.setLayout(self.scroll_layout)


class ScrollWindow(QScrollArea):

    def __init__(self, parent=None, planet=None):
        super().__init__(parent)

        self.setWidget(ExoPlanetPanel(parent=parent, planet=planet))
        self.setWidgetResizable(True)
        self.setFixedHeight(800)


class MainGUI(QWidget):

    def __init__(self):
        super().__init__()

        clear = QPushButton("Clear the .pln Form")
        load = QPushButton("Load .pln File")
        save = QPushButton("Save As .pln File")

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

        self.scroll = ScrollWindow(parent=self)

        self.grid = QGridLayout()
        self.grid.addWidget(load, 0, 0)
        self.grid.addWidget(save, 0, 1)
        self.grid.addWidget(clear, 0, 2)
        self.grid.addLayout(header, 1, 0, 1, -1)
        self.grid.addWidget(self.scroll, 2, 0, 1, -1)

        clear.clicked.connect(self.clear_form)
        load.clicked.connect(self.load_pln)
        save.clicked.connect(self.write_pln)

        self.setLayout(self.grid)
        self.resize(1600, 900)
        self.show()

    def clear_form(self):
        planet = Exoplanet()
        self.update_form(planet)

    def load_pln(self):
        loadit = QFileDialog.getOpenFileName(self, "Load a .pln file", ".")
        filename = loadit[0]

        if filename == "":
            return
        else:
            planet = Exoplanet(path=filename)

        self.update_form(planet)

    def update_form(self, planet):
        self.scroll.setParent(None)
        new_window = ScrollWindow(parent=self, planet=planet)
        self.scroll = new_window
        self.grid.addWidget(self.scroll, 2, 0, 1, -1)
        self.setLayout(self.grid)

    def write_pln(self):
        new_planet = Exoplanet()
        exo_panel = self.scroll.widget()
        rows = exo_panel.scroll_layout.count()
        for n in range(rows):
            exo_row = exo_panel.scroll_layout.itemAt(n).widget()
            exo_dict = exo_row.return_parameter()
            parameter_name = exo_dict["parameter"].lower()
            exo_param = getattr(new_planet, parameter_name)
            exo_param.set_from_template(exo_dict)
            # print(exo_param)
            setattr(new_planet, parameter_name, exo_param)
        new_planet.verify_pln()
        new_planet.save_to_pln(dir="/generated_pln", gui=True)


def __test__():
    test = Exoplanet()
    app = QApplication(sys.argv)
    # w = ScrollWindow(planet=test)
    w = MainGUI()
    sys.exit(app.exec_())
    sys.stdout = sys.__stdout__


if __name__ == "__main__":
    __test__()
