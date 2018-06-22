### Directory Contents
- Exoplanet.py
A class to contain parameters and related information for a single exoplanet.  Includes functions to read and write .pln files from Exoplanet objects.  More work may include parameter calculations, limit checking, and additional file formats.  Also includes an ExoParameter class to define parameters, but needs more work.
- exoplanet_tables.db  
A SQLite database file containing the results of the steps and code contained in the Python Notebook.
- exoplanets_org_work.ipynb  
A Python Notebook with steps taken and code written to identify a list of confirmed exoplanets listed in both exoplanet.eu and the NASA Exoplanet Archive.
- new_exoplanets_to_add.csv  
A CSV file containing just the final resulting table from the Python Notebook.  This table is also contained in the SQLite database file.
- pln_template.yaml  
A YAML template file to help the Exoplanet class recreate a pln file with the original sections and parameters.