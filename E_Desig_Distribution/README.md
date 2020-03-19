# Environmental (E) Designations

*******************************

(E) Designations are the approximate location, represented by a point of the tax lot centroid, on property that may be affected by noise or air quality, or hazardous material contamination. This repo consists of two Python scripts used to build and distribute the (E) Designations data set, internally. 

### Prerequisites

An installation of Python 2/3 with the following packages is required to run the Generation script. A version of Python with the default ArcPy installation that comes with ArcGIS Desktop is required for the Distribution script in order to utilize Metadata functionality that is currently not available in the default ArcPy installation that comes with ArcGIS Pro (Python 3) or the default ArcPy installation that comes with ArcGIS 64-bit Background Geoprocessing. 

##### Distribute\_EDesig\_Apply\_Metadata.py

```
arcpy, xml, os, datetime, shutil, ConfigParser, traceback, sys
```

### Instructions for running

##### Distribute\_EDesig\_Apply\_Metadata.py

1.	Open the script in any integrated development environment (PyCharm is suggested)

2.	Ensure that your IDE is set to be utilizing the Python version that comes with the default installation of ArcGIS. This is required because only this Python version contains the metadata functions required.

3.	 Run the script. It will process the following steps:

  1.	In M:\GIS\BytesProduction\E_Des, if no corresponding directory exists, creates new directory to hold release files. Directory name follows YYYYMMDD naming standard.
  
  2.	Within newly created directory, copies original E_Desig text file, generates shp and meta directories, and populates these directories with requisite files from the temporary directory generated with the first script.
  
  3.	An E Designation feature class will also be copied from the temporary geodatabase to SDE PROD. If no E Designation feature class exists on SDE PROD currently, the naming convention for the feature class will match DCP_EARD_Edesignations. If a previous E Designation feature class exists on SDE PROD, the naming convention for the feature class will match DCP_EARD_Edesignations_{date_script_was_run}.
  
  4.	Layer metadata will be replaced for both M:\GIS\DATA\Zoning\Environmental designation.lyr.xml and M:\GIS\DATA\BYTES of the BIG APPLE\Zoning Related\Environmental designation.lyr.xml
