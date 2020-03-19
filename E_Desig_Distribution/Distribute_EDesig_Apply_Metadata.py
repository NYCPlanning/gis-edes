'''
This script must be run using the Python version associated with standard ArcGIS (Python 2.7, 32-bit)
This script utilizes the DCP_EARD_Edesignations_20190228 archived Feature Class in SDE_ARCHIVE for generating
desired metadata format. If this file is renamed or moved, a new template Feature Class must be utilized on line
97 of this script.
'''

import xml.etree.ElementTree as ET, arcpy, os, datetime, shutil, ConfigParser, zipfile, sys, traceback, calendar

try:
    # Set script start-time for logging run-time purposes
    print("Beginning script execution")
    StartTime = datetime.datetime.now().replace(microsecond=0)

    # Set path to configuration ini file for paths

    config = ConfigParser.ConfigParser()
    config.read(r'edesig_config_template.ini')

    # Log outputs in text file

    log_path = config.get('DISTRIBUTION_PATHS', 'Log_Path')
    log = open(os.path.join(log_path, 'log_distribute_edesignations.txt'), "a")

    # Set current date variables.

    print("Start")
    current_date = datetime.datetime.today().strftime("%Y%m%d")

    directory_current_date = datetime.datetime.today().strftime("%Y%m%d")

    publication_date = str(datetime.datetime.today().year) + \
                       str(datetime.datetime.today().month) + \
                       str(calendar.monthrange(datetime.datetime.today().year, datetime.datetime.today().month)[1])

    xslt = arcpy.GetInstallInfo('desktop')['InstallDir'] + "Metadata/Stylesheets/ArcGIS.xsl"

    # Create directory for corresponding release date in Bytes Production directory
    output_path = config.get('DISTRIBUTION_PATHS', 'Output_Path')

    # Set current year directory variable.

    latest_year_array = []
    for directory in os.listdir(output_path):
        dir_year = datetime.datetime.strptime(directory, '%Y').year
        latest_year_array.append(dir_year)

    latest_year_dir = str(max(latest_year_array))

    if os.path.isdir(os.path.join(output_path, latest_year_dir, directory_current_date)):
        print("Date directory already exists. Skipping")
    else:
        print("Creating date directory in M: drive")
        os.makedirs(os.path.join(output_path, latest_year_dir, directory_current_date))

    # Create shapefile directory in Bytes Production directory

    if os.path.isdir(os.path.join(output_path, latest_year_dir, directory_current_date, "shp")):
        print("Shapefile directory already exists. Skipping")
    else:
        print("Creating shapefile directory in M: drive")
        os.makedirs(os.path.join(output_path, latest_year_dir, directory_current_date, "shp"))

    # Create metadata directory in Bytes Production directory

    if os.path.isdir(os.path.join(output_path, latest_year_dir, directory_current_date, "meta")):
        print("Metadata directory already exists. Skipping")
    else:
        print("Creating shapefile directory in M: drive")
        os.makedirs(os.path.join(output_path, latest_year_dir, directory_current_date, "meta"))

    # Export original EDesignation text file to Bytes Production directory

    edesig_path = config.get('DISTRIBUTION_PATHS', 'EDesig_Path')

    edesig_file_names = []
    edesig_file_dates = []

    for filename in os.listdir(edesig_path):
        if filename.endswith('.txt'):
            filename_date = datetime.datetime.strptime(filename.split("_")[2][:-4], "%Y%m%d")
            edesig_file_dates.append(filename_date)
            edesig_file_names.append(filename.split(".")[0])

    # Assign most recent E-Designation file to variable

    latest_edesig_txt = max(edesig_file_dates)

    for filename in os.listdir(edesig_path):
        if filename.endswith('.txt'):
            filename_date = datetime.datetime.strptime(filename.split("_")[2][:-4], "%Y%m%d")
            if filename_date == latest_edesig_txt:

                # Export original EDesignation text file to BytesProduction folder.
                print("Exporting original E-Designation text file to BytesProduction folder")
                shutil.copyfile(os.path.join(edesig_path, filename), os.path.join(output_path, latest_year_dir, directory_current_date, filename))
                print('Export complete')

    # Set path for translation xml file and xslt file. This is required for exporting xml files from a shapefile or FC.

    print("Setting arcdir")
    Arcdir = arcpy.GetInstallInfo("desktop")["InstallDir"]
    translator = Arcdir + "Metadata/Translator/ARCGIS2FGDC.xml"
    xslt = Arcdir + "Metadata/Stylesheets/ArcGIS.xsl"
    xslt_remove_geoprocessing = Arcdir + "Metadata/Stylesheets/gpTools/remove geoprocessing history.xslt"
    xslt_remove_local_storage = Arcdir + "Metadata/Stylesheets/gpTools/remove local storage info.xslt"

    # Set path variables.

    print("Setting initial paths")

    edes_old_sde_path = config.get('DISTRIBUTION_PATHS', 'EDesig_Old_SDE_Path')
    output_gen_path = os.path.join(config.get('DISTRIBUTION_PATHS', 'Output_Path'), latest_year_dir, directory_current_date)
    output_meta_path = os.path.join(config.get('DISTRIBUTION_PATHS', 'Output_Path'), latest_year_dir, directory_current_date, 'meta')
    output_shp_path = os.path.join(config.get('DISTRIBUTION_PATHS', 'Output_Path'), latest_year_dir, directory_current_date, 'shp')
    interim_meta_path = os.path.join(config.get('DISTRIBUTION_PATHS', 'Temp_Path'), 'meta')
    interim_shp_path = os.path.join(config.get('DISTRIBUTION_PATHS', 'Temp_Path'), 'shp')
    output_lyr_path_zoning = config.get('DISTRIBUTION_PATHS', 'Output_Zoning_Layer_Path')
    output_lyr_path_bytes_zoning = config.get('DISTRIBUTION_PATHS', 'Output_Bytes_Zoning_Layer_Path')
    output_lyr_path_boundaries_zoning = config.get('DISTRIBUTION_PATHS', 'Output_Boundaries_Zoning_Layer_Path')
    gdb_path = os.path.join(config.get('DISTRIBUTION_PATHS', 'Temp_Path'), 'EDES_GDB.gdb')
    sde_path = config.get('DISTRIBUTION_PATHS', 'SDE_Path')

    # Check if previous metadata files have already been created.

    print("Checking if metadata outputs already exist from previous iteration.")
    if arcpy.Exists(os.path.join(interim_meta_path, 'nyedes_meta.xml')):
        print("Previous metadata output found. Deleting now.")
        arcpy.Delete_management(os.path.join(interim_meta_path, 'nyedes_meta.xml'))
    if arcpy.Exists(os.path.join(interim_meta_path, 'nyedes_meta_updated.xml')):
        print("Previous metadata output found. Deleting now.")
        arcpy.Delete_management(os.path.join(interim_meta_path, 'nyedes_meta_updated.xml'))
    if arcpy.Exists(os.path.join(interim_meta_path, 'nyedes_meta_updated_geoprocess.xml')):
        print("Previous metadata output found. Deleting now.")
        arcpy.Delete_management(os.path.join(interim_meta_path, 'nyedes_meta_updated_geoprocess.xml'))
    if arcpy.Exists(os.path.join(interim_meta_path, 'nyedes_meta_updated_geoprocess_localstorage.xml')):
        print("Previous metadata output found. Deleting now.")
        arcpy.Delete_management(os.path.join(interim_meta_path, 'nyedes_meta_updated_geoprocess_localstorage.xml'))

    # Export metadata from original EDes file as standalone xml file.

    print("Exporting xml metadata to intermediary folder")
    arcpy.ExportMetadata_conversion(edes_old_sde_path, translator, os.path.join(interim_meta_path, "nyedes_meta.xml"))
    print("Export complete")
    print("Printing XML Text")
    tree = ET.parse(os.path.join(interim_meta_path, "nyedes_meta.xml"))
    root = tree.getroot()

    # Update standalone xml file with current date for publication date.

    for x in root.iter('pubdate'):
        print("Date {0} will be updated to {1}".format(x.text, current_date))
        x.text = publication_date
    tree.write(os.path.join(interim_meta_path, "nyedes_meta_updated.xml"))

    # Remove geoprocessing history and local storage information from standalone xml file.

    arcpy.XSLTransform_conversion(os.path.join(interim_meta_path, "nyedes_meta_updated.xml"),
                                  xslt_remove_geoprocessing,
                                  os.path.join(interim_meta_path, "nyedes_meta_updated_geoprocess.xml"))

    arcpy.XSLTransform_conversion(os.path.join(interim_meta_path, "nyedes_meta_updated_geoprocess.xml"),
                                  xslt_remove_local_storage,
                                  os.path.join(interim_meta_path, "nyedes_meta_updated_geoprocess_localstorage.xml"))


    # Apply new metadata xml to temporary Feature Class (e.g. EDES_GDB.gdb/nyedes_{current_date}

    arcpy.MetadataImporter_conversion(os.path.join(interim_meta_path, "nyedes_meta_updated_geoprocess_localstorage.xml"),
                                      os.path.join(gdb_path, 'nyedes_{}'.format(current_date)))
    arcpy.UpgradeMetadata_conversion(os.path.join(gdb_path, 'nyedes_{}'.format(current_date)), 'FGDC_TO_ARCGIS')

    # Apply new metadata xml to temporary shapefile (e.g. C:/tempEDesig/shp/nyedes_{current_date}

    arcpy.MetadataImporter_conversion(os.path.join(interim_meta_path, "nyedes_meta_updated_geoprocess_localstorage.xml"),
                                      os.path.join(interim_shp_path, 'nyedes_{}.shp'.format(current_date)))
    arcpy.UpgradeMetadata_conversion(os.path.join(gdb_path, 'nyedes_{}'.format(current_date)), 'FGDC_TO_ARCGIS')

    # Copy new standalone xml file to Bytes folder.

    if os.path.exists(os.path.join(interim_meta_path, 'nyedes_meta_Final.xml')):
        print("Standalone xml already exists in Bytes folder")
    else:
        print("Copying new standalone xml to Bytes folder")
        shutil.copyfile(os.path.join(interim_meta_path, "nyedes_meta_updated_geoprocess_localstorage.xml"),
                        os.path.join(output_meta_path, "nyedes_meta_Final.xml"))
        print("Copy complete.")

    # Produce HTML document from XML stand-alone output

    if os.path.exists(os.path.join(gdb_path, "nyedes_{}".format(current_date))):
        print("Creating new standalone html in Bytes folder")
        arcpy.XSLTransform_conversion(os.path.join(gdb_path, "nyedes_{}".format(current_date)),
                                      xslt,
                                      os.path.join(output_meta_path, 'nyedes_{}.html'.format(directory_current_date)),
                                      '#')

    # Export final product Shapefile to Bytes Production directory

    print("Exporting shapefile to Bytes directory")
    if os.path.exists(os.path.join(output_shp_path, "nyedes_{}.shp".format(current_date))):
        print("Shapefile files already exist. Skipping")
    else:
        arcpy.FeatureClassToShapefile_conversion(os.path.join(gdb_path, "nyedes_{}".format(current_date)),
                                                 output_shp_path)

    # Export final product Feature Class to SDE PROD

    if arcpy.Exists(os.path.join(sde_path, "DCP_EARD_Edesignations")):
        print("EARD_EDesignations already exists in SDE. Renaming new export with appended date on end. "
              "Remember to archive/delete the old version.")
        arcpy.FeatureClassToFeatureClass_conversion(os.path.join(gdb_path, "nyedes_{}".format(current_date)), sde_path,
                                                    "DCP_EARD_Edesignations_{}".format(current_date))
        arcpy.XSLTransform_conversion(os.path.join(sde_path, "DCP_EARD_Edesignations_{}".format(current_date)),
                                      xslt_remove_geoprocessing, os.path.join(interim_meta_path, 'DCP_EARD_Edes.xml'))
        arcpy.MetadataImporter_conversion(os.path.join(interim_meta_path, 'DCP_EARD_Edes.xml'),
                                          os.path.join(sde_path, 'DCP_EARD_Edesignations_{}'.format(current_date)))
        arcpy.Delete_management(os.path.join(interim_meta_path, 'DCP_EARD_Edes.xml'))
    else:
        arcpy.FeatureClassToFeatureClass_conversion(os.path.join(gdb_path, "nyedes_{}".format(current_date)), sde_path,
                                                    "DCP_EARD_Edesignations")
        arcpy.XSLTransform_conversion(os.path.join(sde_path, "DCP_EARD_Edesignations"),
                                      xslt_remove_geoprocessing, os.path.join(interim_meta_path, 'DCP_EARD_Edes.xml'))
        arcpy.MetadataImporter_conversion(os.path.join(interim_meta_path, 'DCP_EARD_Edes.xml'),
                                          os.path.join(sde_path, 'DCP_EARD_Edesignations'))
        arcpy.Delete_management(os.path.join(interim_meta_path, 'DCP_EARD_Edes.xml'))

    # Export layer metadata to M drive Zoning directory


    def update_lyr_meta(in_path):
        print("Exporting metadata for {}".format(in_path))
        arcpy.Delete_management(os.path.join(in_path, 'Environmental designation.lyr.xml'))
        arcpy.ExportMetadata_conversion(os.path.join(gdb_path, 'nyedes_{}'.format(current_date)), translator,
                                        os.path.join(in_path, 'Environmental designation.lyr.xml'))
        arcpy.UpgradeMetadata_conversion(os.path.join(in_path, 'Environmental designation.lyr.xml'),
                                         'FGDC_TO_ARCGIS')
        print("New layer metadata exported for {}".format(in_path))

    update_lyr_meta(output_lyr_path_zoning)
    update_lyr_meta(output_lyr_path_boundaries_zoning)
    update_lyr_meta(output_lyr_path_bytes_zoning)

    EndTime = datetime.datetime.now().replace(microsecond=0)
    print("Script runtime: {}".format(EndTime - StartTime))
    log.write(str(StartTime) + "\t" + str(EndTime) + "\t" + str(EndTime - StartTime) + "\n")

except:
    print("error")
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages() + "\n"

    print(pymsg)
    print(msgs)

    log.write("" + pymsg + "\n")
    log.write("" + msgs + "")
    log.write("\n")
    log.close()
