'''
This script must be run using the Python version associated with ArcGIS Pro (Python 3.6, 64-bit)

It is also important to note that unless files are deleted from the temporary C: directory (tempEDesig), they will be
re-used in the generation of E-Designations. In order to avoid using old datasets one should ALWAYS delete the temporary
directory on C: unless you are troubleshooting the script or are confident that the most recent exports already exist in
temp dir.

Script run-time is approximately 1 hour with no temporary files in GDB and approximately 20 minutes when
the most recent temporary files are already copied to the GDB. If the script is run from the user's C: drive the
associated run-times are 20 minutes with no temporary files and approximately 5 minutes with most recent temp files
already in the GDB.
'''


import arcpy, os, datetime, pandas as pd, sys, traceback, configparser

try:
    StartTime = datetime.datetime.now().replace(microsecond = 0)

    # Path Declarations

    config = configparser.ConfigParser()
    config.read(r'edesig_config_template.ini')
    temp_path = config.get('GENERATION_PATHS', 'Temp_Path')

    # Create temporary directory - C:\tempEDesig

    print("Checking Temp directory")
    if not os.path.isdir(temp_path):
        os.mkdir(temp_path)
    else:
        print("Temp directory already exists")

    # Log outputs in text file

    log_path = config.get('GENERATION_PATHS', 'Log_Path')
    log = open(os.path.join(log_path, "log_generate_edesignations.txt"), "a")

    # Check that temporary gdb exists

    print("Checking Temp FGDB")
    if arcpy.Exists(os.path.join(temp_path, "EDES_GDB.gdb")):
        print("Temp FGDB already exists")
    else:
        arcpy.CreateFileGDB_management(temp_path, 'EDES_GDB', "CURRENT")

    # Create Geodatabase path variable

    gdb_path = os.path.join(temp_path, 'EDES_GDB.gdb')

    # Create directories for outputs

    current_date = datetime.datetime.today().strftime("%Y%m%d")

    # Create temporary shapefile directory in C:\tempEDesig\

    if os.path.isdir(os.path.join(temp_path, "shp")):
        print("Shapefile directory already exists. Skipping")
    else:
        print("Creating shapefile directory in temporary directory")
        os.makedirs(os.path.join(temp_path, "shp"))

    # Create temporary metadata directory in C:\tempEDesig\

    if os.path.isdir(os.path.join(temp_path, "meta")):
        print("Metadata directory already exists. Skipping")
    else:
        print("Creating metadata directory in temporary directory")
        os.makedirs(os.path.join(temp_path, "meta"))

    # Create list of all existing E-Designation files

    print("Parsing EDes files for most recent")
    edesig_file_names = []
    edesig_file_dates = []

    # Declare path to directory holding E-Designation text files

    edesig_path = config.get('GENERATION_PATHS', 'EDesig_Path')

    # Assign lists for all E-Designation text file exports

    for filename in os.listdir(edesig_path):
        if filename.endswith('.txt'):
            filename_date = datetime.datetime.strptime(filename.split("_")[2][:-4], "%Y%m%d")
            edesig_file_dates.append(filename_date)
            edesig_file_names.append(filename.split(".")[0])

    # Assign most recent E-Designation file to variable

    latest_edesig_txt = max(edesig_file_dates)
    latest_edesig_name = max(edesig_file_names)
    print(latest_edesig_name)
    print("Latest EDes file available is {}".format(str(latest_edesig_txt)))

    # Generate BBLs from values expressed in most recent E-Designation file.

    print("Generating BBL values from constituent fields")

    for filename in os.listdir(edesig_path):
        if filename.endswith('.txt'):
            filename_date = datetime.datetime.strptime(filename.split("_")[2][:-4], "%Y%m%d")
            if filename_date == latest_edesig_txt:

                # Convert most recent E-Desgination TXT file into Pandas DataFrame.

                latest_edesig_csv = pd.read_csv(os.path.join(edesig_path, filename),
                                                sep=",",
                                                names = ["ENUMBER", "E_DATE", "BOROCODE", "TAXBLOCK","TAXLOT", "HAZMAT",
                                                         "AIR", "NOISE","HAZMAT_D", "AIR_DATE", "NOISE_D", "CEQR_NUM",
                                                         "ULURP_NUM", "BBL"])

                str_filename_date = filename_date.strftime("%Y%m%d")

                # Modify DataFrame to generate BBL values from available fields.

                latest_edesig_csv['BBL'] = latest_edesig_csv.apply(lambda row: row.BOROCODE*1000000000 + row.TAXBLOCK*10000 + row.TAXLOT, axis=1)
                print("Converting file type from txt to csv")

                # Convert most recent E-Designation Pandas DataFrame into CSV file.

                latest_edesig_csv.to_csv(os.path.join(temp_path, filename.replace("txt", "csv")))

    # Convert csv to DBASE table and import into temporary FGDB.

    print("Connecting to Temp File Geodatabase")
    arcpy.env.workspace = temp_path

    for csv in arcpy.ListTables():
        print('Tables currently available in temporary Geodatabase: '.format(csv))
        arcpy.env.workspace = gdb_path
        if arcpy.Exists(csv.replace('.csv', '')) is False:
            print("Converting file type from csv to dbf")
            arcpy.TableToDBASE_conversion(os.path.join(temp_path, csv), gdb_path)
            print("Deleting unnecessary field")
            arcpy.DeleteField_management(os.path.join(gdb_path, csv.replace('.csv', '.dbf')), 'Field1')
        else:
            print("Required base DBF exists. Skipping import")

    # List feature classes currently in temporary GDB

    arcpy.env.workspace = gdb_path

    fc_list = arcpy.ListFeatureClasses()
    print("The following feature classes are currently available within the GDB: {}".format(fc_list))

    # Import MapPLUTO spatial files to temporary GDB

    mappluto_path = config.get('GENERATION_PATHS', 'PROD_Path')

    if "MapPLUTO_UNCLIPPED" in fc_list and "TAXLOT_POLYGON" in fc_list:
        print("Required base FCs exist. Skipping import")
    if "MapPLUTO_UNCLIPPED" not in fc_list:
        print("MapPLUTO spatial file required. Importing MapPLUTO")
        fms = arcpy.FieldMappings()

        fm = arcpy.FieldMap()
        fm.addInputField(os.path.join(mappluto_path, 'GISPROD.SDE.MapPLUTO_UNCLIPPED'), "BBL")
        fms.addFieldMap(fm)

        arcpy.FeatureClassToFeatureClass_conversion(os.path.join(mappluto_path, 'GISPROD.SDE.MapPLUTO_UNCLIPPED'),
                                                    gdb_path, "MapPLUTO_UNCLIPPED", "", fms)

    # Import Tax Lot Polygon spatial files to temporary GDB

    taxlot_path = config.get('GENERATION_PATHS', 'Cadastral_Path')

    if "TAXLOT_POLYGON" not in fc_list:
        print("TaxLot Polygon spatial file required. Importing TaxLot Polygon")
        fms = arcpy.FieldMappings()

        fm = arcpy.FieldMap()
        fm.addInputField(os.path.join(taxlot_path, "GISPROD.SDE.Tax_Lot_Polygon"),
                         "BBL")
        fms.addFieldMap(fm)
        arcpy.FeatureClassToFeatureClass_conversion(os.path.join(taxlot_path, 'GISPROD.SDE.Tax_Lot_Polygon'),
                                                    gdb_path, "TAXLOT_POLYGON", "", fms)

    # Add Double Field to TaxLot Polygon for future join

    print("Checking Tax Lot Polygon FC for Double BBL field")
    field_list = [field.name for field in arcpy.ListFields(os.path.join(gdb_path, "TAXLOT_POLYGON"))]

    if "DBBL" in field_list:
        print("DBBL is already present in the Tax Lot Feature Class")
    else:
        print("DBBL is not present in Tax Lot FC. Creating now")
        arcpy.AddField_management(os.path.join(gdb_path, "TAXLOT_POLYGON"), "DBBL", "DOUBLE")
        print("Populating DBBL field.")
        arcpy.CalculateField_management(os.path.join(gdb_path, "TAXLOT_POLYGON"), 'DBBL', '!BBL!')

    # Create in-memory feature layers and table views for join.

    arcpy.env.workspace = gdb_path
    gdb_files = arcpy.ListTables()

    arcpy.env.workspace = "in_memory"

    for f in gdb_files:
        print("EDes table available: {}".format(f))

        # Check that table view for join doesn't already exist within workspace

        if 'GIS' in f and arcpy.Exists('EDES_TableView') is False:
            print("Creating Table View for EDes file")
            arcpy.MakeTableView_management(os.path.join(gdb_path, f), "EDES_TableView")
            print(arcpy.Exists("EDES_TableView"))
        else:
            print("EDes_TableView already exists. Deleting and re-creating.")
            arcpy.Delete_management("EDES_TableView")
            arcpy.MakeTableView_management(os.path.join(gdb_path, f), "EDES_TableView")

    # Create temporary feature layers for MapPLUTO and TaxLot Polygon spatial files

    print("Creating Feature Layers for MapPLUTO and TaxLot")
    arcpy.MakeFeatureLayer_management(os.path.join(gdb_path, "MapPLUTO_UNCLIPPED"), "MapPLUTO_FeatLayer")
    arcpy.MakeFeatureLayer_management(os.path.join(gdb_path, "TAXLOT_POLYGON"), "TaxLot_FeatLayer")

    print(arcpy.Exists("MapPLUTO_FeatLayer"))
    print(arcpy.Exists("TaxLot_FeatLayer"))

    # Join EDes to MapPLUTO and retain matching records.

    print("Joining MapPLUTO and EDes for matching records")
    arcpy.env.workspace = gdb_path
    fc_list = arcpy.ListFeatureClasses()
    arcpy.AddJoin_management("MapPLUTO_FeatLayer", "BBL", "EDES_TableView", "BBL", "KEEP_ALL")

    print("Getting first join field")
    for field in arcpy.ListFields("MapPLUTO_FeatLayer"):
        if 'BBL' in field.name.upper() and 'E_GIS' in field.name.upper():
            bbl_join_field = field.name
            print("join field set: {}".format(bbl_join_field))

    print("Creating MapPLUTO Match Feature Class")
    if 'MapPLUTO_MatchBBL' in fc_list:
        print("MapPLUTO Match FC already exists. Skipping.")
    else:
        print("Copying MapPLUTO Match Feature Class to Geodatabase")
        arcpy.CopyFeatures_management("MapPLUTO_FeatLayer", "MapPLUTO_MatchBBL")
        print("Copy of MapPLUTO Match Feature Class Complete")

    print("Creating MapPLUTO Match Selection Feature Class")
    sql_1 = "{0} IS NOT NULL".format(arcpy.AddFieldDelimiters(latest_edesig_name, bbl_join_field.replace(".", "_")))
    print(sql_1)

    if 'MapPLUTO_MatchBBL_Selection' in fc_list:
        print("MapPLUTO Match Selection FC already exists. Skipping")
    else:
        print("Selecting unique MapPLUTO matches")
        arcpy.Select_analysis("MapPLUTO_MatchBBL", "MapPLUTO_MatchBBL_Selection", where_clause=sql_1)
        print("MapPLUTO Match Selection Created")

    # Delete in-memory table and layer in preparation for re-join

    print("Deleting old in_memory table and layer")
    arcpy.Delete_management("MapPLUTO_FeatLayer")
    arcpy.Delete_management("EDES_TableView")

    # Re-creating in-memory table and layer

    print("Re-creating in_memory table and layer")
    for f in gdb_files:
        print("EDes table available: {}".format(f))
        if 'GIS' in f and arcpy.Exists('EDES_TableView') is False:
            print("Creating Table View for {}".format(f))
            arcpy.MakeQueryTable_management(os.path.join(gdb_path, f), "EDES_TableView", 'ADD_VIRTUAL_KEY_FIELD')
            print(arcpy.Exists("EDES_TableView"))
        else:
            print("EDes_TableView already exists. Deleting and re-creating.")
            arcpy.Delete_management("EDES_TableView")
            arcpy.MakeQueryTable_management(os.path.join(gdb_path, f), "EDES_TableView", 'ADD_VIRTUAL_KEY_FIELD')

    arcpy.MakeFeatureLayer_management(os.path.join(gdb_path, "MapPLUTO_UNCLIPPED"), "MapPLUTO_FeatLayer")
    print(arcpy.Exists("MapPLUTO_FeatLayer"))

    # Join EDes to MapPLUTO and retain non-matching records.

    print("Joining EDES and MapPLUTO for non-matching records")
    arcpy.env.workspace = gdb_path
    arcpy.AddJoin_management("EDES_TableView", "BBL", "MapPLUTO_FeatLayer", "BBL", "KEEP_ALL")

    # Check that join worked correctly. Not typically used, but left for special cases

    fields = arcpy.ListFields("EDES_TableView")
    fields = [field.name for field in fields]
    print(fields)

    with arcpy.da.SearchCursor("EDES_TableView", fields) as cursor:
            for row in cursor:
                print("{0}, {1}".format(row[14], row[16]))

    arcpy.env.workspace = gdb_path
    tbl_list = arcpy.ListTables()

    if 'EDES_NoMatchBBL' in tbl_list:
        print("Edes No Match Table already exists. Skipping")
    else:
        print("Creating Edes No Match Table")
        arcpy.TableToTable_conversion("EDES_TableView", gdb_path, 'EDES_NoMatchBBL')
        print("Edes No Match table created")

    # sql_2 = '{} IS NULL'.format(arcpy.AddFieldDelimiters("EDES_NoMatchBBL", "BBL_1"))
    sql_2 = '{} IS NULL'.format(arcpy.AddFieldDelimiters("EDES_NoMatchBBL", "BBL"))

    if 'EDES_NoMatchBBL_Selection' in tbl_list:
        print("Edes non-matching table already exists. Skipping")
    else:
        print("Creating Edes No Match Selection table")
        arcpy.TableSelect_analysis("EDES_NoMatchBBL", "EDES_NoMatchBBL_Selection", sql_2)
        print("EDes No Match Selection Created")

    print("Creating Table View for EDes non-BBL Match records")
    arcpy.MakeTableView_management(os.path.join(gdb_path, "EDES_NoMatchBBL_Selection.dbf"), "EDES_NoMatchBBL_TableView")

    # Join EDes to TaxLot and retain matching records.

    print("Joining TaxLot and EDes for matching records")
    arcpy.AddJoin_management("TAXLOT_FeatLayer", "DBBL", "EDES_NoMatchBBL_TableView", "BBL", "KEEP_COMMON")

    arcpy.env.workspace = gdb_path
    fc_list = arcpy.ListFeatureClasses()

    print("Creating TaxLot Match Feature Class")
    if 'TaxLot_MatchBBL' in fc_list:
        print("TaxLot Match FC already exists. Skipping")
    else:
        arcpy.FeatureClassToFeatureClass_conversion("TAXLOT_FeatLayer", gdb_path, "TaxLot_MatchBBL")

    # Match field names across joined mappluto FC and taxlot FC.

    retain_fields_pluto = ['E_GIS_{}_ENUMBER'.format(str_filename_date), 'E_GIS_{}_CEQR_NUM'.format(str_filename_date),
                           'E_GIS_{}_ULURP_NUM'.format(str_filename_date), 'E_GIS_{}_BOROCODE'.format(str_filename_date),
                           'E_GIS_{}_TAXBLOCK'.format(str_filename_date), 'E_GIS_{}_TAXLOT'.format(str_filename_date),
                           'E_GIS_{}_BBL'.format(str_filename_date)]

    retain_fields_taxlot = ['OBJECTID_12', 'ENUMBER', 'CEQR_NUM', 'ULURP_NUM', 'BOROCODE', 'TAXBLOCK', 'TAXLOT', 'BBL']

    req_fields = ['OBJECTID', 'Shape', 'Shape_Area', 'Shape_Length']

    available_fields_pluto = arcpy.ListFields(os.path.join(gdb_path, "MapPLUTO_MatchBBL_Selection"))

    if len(available_fields_pluto) == 11:
        print("Fields have already gone through process for MapPLUTO")
    else:
        for field in available_fields_pluto:
            if field.name not in retain_fields_pluto and field.name not in req_fields:
                print("Deleting the following field from MapPLUTO: {}".format(field.name))
                arcpy.DeleteField_management(os.path.join(gdb_path, "MapPLUTO_MatchBBL_Selection"), field.name)
            if field.name in retain_fields_pluto and field.name not in req_fields:
                print("Altering the following field in MapPLUTO: {}".format(field.name))
                arcpy.AlterField_management("MapPLUTO_MatchBBL_Selection", field.name, field.name.replace(latest_edesig_name
                                                                                                          + "_", ""))

    available_fields_taxlot = arcpy.ListFields(os.path.join(gdb_path, 'TaxLot_MatchBBL'))

    if len(available_fields_taxlot) == 12:
        print("Fields have already gone through processing for TaxLot")
    else:
        for field in available_fields_taxlot:
            if field.name not in retain_fields_taxlot and field.name not in req_fields:
                print("Deleting the following field in TaxLot: {}".format(field.name))
                arcpy.DeleteField_management(os.path.join(gdb_path, "TaxLot_MatchBBL"), field.name)

    # Merge MapPLUTO and TaxLot feature layers to get comprehensive list of E-Designation records

    merge_list = [os.path.join(gdb_path, "MapPLUTO_MatchBBL_Selection"), os.path.join(gdb_path, "TaxLot_MatchBBL")]
    print("Merging TaxLot and MapPLUTO Match FCs.")

    if arcpy.Exists(os.path.join(gdb_path, "EDesignations_FinalPoly")):
        print("EDesignation_FinalPoly already exists. Skipping")
    else:
        arcpy.Merge_management(merge_list, os.path.join(gdb_path, "EDesignations_FinalPoly"))

    # Convert polygons to centroid points

    print("Converting Feature polygons to centroid points.")

    if arcpy.Exists(os.path.join(gdb_path, 'EDesignations_FinalPoint')):
        print("EDesignation_FinalPoint already exists. Skipping")
    else:
        arcpy.FeatureToPoint_management("EDesignations_FinalPoly", "EDesignations_FinalPoint")

    # Re-ordering fields with field map to match previous releases

    print("Re-ordering fields with field mapping")

    fms = arcpy.FieldMappings()

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), "ENUMBER")
    fms.addFieldMap(fm)

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), 'CEQR_NUM')
    fms.addFieldMap(fm)

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), 'ULURP_NUM')
    fms.addFieldMap(fm)

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), 'BOROCODE')
    fms.addFieldMap(fm)

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), 'TAXBLOCK')
    fms.addFieldMap(fm)

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), 'TAXLOT')
    fms.addFieldMap(fm)

    fm = arcpy.FieldMap()
    fm.addInputField(os.path.join(gdb_path, "EDesignations_FinalPoint"), 'BBL')
    fms.addFieldMap(fm)

    print("Re-ordering fields complete.")
    print("Exporting final result to point feature class")

    # Begin exporting final product to temporary geodatabase location

    if arcpy.Exists(os.path.join(gdb_path, 'nyedes_{}'.format(current_date))):
        print("EARD_EDesignations already exists. Skipping")
    else:
        arcpy.FeatureClassToFeatureClass_conversion(os.path.join(gdb_path, "EDesignations_FinalPoint"),
                                                    gdb_path, "nyedes_{}".format(current_date), "", fms)

    # Begin exporting final product to temporary shapefile folder

    if arcpy.Exists(os.path.join(temp_path, "shp", "nyedes_{}".format(current_date))):
        print("EDes shapefile already exists. Skipping")
    else:
        print("Exporting EARD_EDesignations shapefile to shapefile folder")
        arcpy.FeatureClassToShapefile_conversion(os.path.join(gdb_path, "nyedes_{}".format(current_date)),
                                                 os.path.join(temp_path, "shp"))

    EndTime = datetime.datetime.now().replace(microsecond=0)
    print("Script runtime: {}".format(EndTime - StartTime))
    log.write(str(StartTime) + "\t" + str(EndTime) + "\t" + str(EndTime - StartTime) + "\n")
    log.close()

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
