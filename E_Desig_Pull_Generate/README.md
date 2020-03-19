# Environmental (E) Designations

*******************************

(E) Designations are the approximate location, represented by a point of the tax lot centroid, on property that may be affected by noise or air quality, or hazardous material contamination. This repo consists of two Python scripts used to build and distribute the (E) Designations data set, internally. 

### Prerequisites

An installation of Python 2/3 with the following packages is required to run the Generation script. A version of Python with the default ArcPy installation that comes with ArcGIS Desktop is required for the Distribution script in order to utilize Metadata functionality that is currently not available in the default ArcPy installation that comes with ArcGIS Pro (Python 3) or the default ArcPy installation that comes with ArcGIS 64-bit Background Geoprocessing. 

##### Pull\_Input\_EDesig.py

```
win32com.client, datetime, os, subprocess, shutil, configparser, sys, traceback
```

##### Generate\_EDesig.py

```
arcpy, os, datetime, pandas, shutil, sys, traceback, configparser
```

### Instructions for running

##### Pull\_Input\_EDesig.py

1. This script is meant to be scheduled through the use of either batch files or with the aide of software such as Windows Task Scheduler.

2. Ensure that when you schedule the task you assign the appropriate python executable to run this script (must be a Python executable with the aforementioned packages installed)

3. Ensure that the configuration ini file is up-to-date with path and other variables. If any paths or other variables have changed since the time of this writing, those changes must be reflected in the ini file.

4. Each time the scheduled script is run it will loop through the user's Outlook inbox for emails with a specific subject line related to E-Designations.

5. If particular emails are found, their associated release date and attachment are assigned to an in-memory dictionary. The latest release date is pulled from the dictionary and checked against E-Designation files already available in our E-Designation archive. If no match is found, they email's attachment is automatically downloaded to the archive directory and the Generate\_EDesig.py script is kicked-off using this new export.

6. When the Generate\_EDesig.py script is complete, an email is sent to the GIS Team email notifying the team that a new E-Designation export is available and prompting the user to run the Distribute\_EDesig\_Apply\_Metadata.py.

##### Generate\_EDesig.py

1. Open the script in any integrated development environment (PyCharm is suggested)

2.	Ensure that your IDE is set to be utilizing a version of Python 3 as its interpreter for this specific script or a version of Python 2 which has had pandas installed via pip.

3.	Ensure that the configuration ini file is up-to-date with path variables. If any paths have changed since the time of this writing, those changes must be reflected in the ini file.

4.	Run the script. It will create a new temporary directory. Within this temporary directory a copy of the latest E-Designation text file, a file geodatabase, and shp/meta folders are generated.

5.	After processing is finished, the temporary file geodatabase will have the new e designation feature class using the following naming convention **nyedes\_{date\_script\_was_run}**. The shp temporary directory will also hold a copy of the new e designation data set in shapefile format with the same naming convention.