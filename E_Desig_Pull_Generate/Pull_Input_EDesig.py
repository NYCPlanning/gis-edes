import win32com.client, datetime, os, subprocess, shutil, configparser, sys, traceback

'''
Must use 32-bit version of arcpy that comes with the default installation of ArcGIS Desktop.
Python installation must also include the win32com.client package 
'''

try:
    # Assign start time variable for logging purposes
    StartTime = datetime.datetime.now().replace(microsecond=0)

    # Assign and read initialization file for required path information
    config = configparser.ConfigParser()
    config.read(r"edesig_config_template.ini")

    # Assign log object for outputting run-time details
    log_path = config.get('INPUT_PULL_PATHS', 'Log_Path')
    log = open(os.path.join(log_path, 'log_input_pull_edesignations.txt'), "a")

    # Assign remaining paths from read ini file
    temp_path = config.get("INPUT_PULL_PATHS", "Temp_Path")
    python3_path = config.get("INPUT_PULL_PATHS", "Python3_Path")
    gen_script_path = config.get("INPUT_PULL_PATHS", "Generation_Script_Path")

    # Assign email you wish to have notified upon script completion
    email_recipient = config.get("INPUT_PULL_PATHS", "Email_Recipient")

    # Assign today date variable for comparison in E-Designation archive
    today = datetime.datetime.now()

    # Assign E-Designation archive path
    edes_archive_path = config.get("INPUT_PULL_PATHS", "EDes_Path")

    # Assign outlook object
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    # Assign outlook inbox object
    inbox = outlook.GetDefaultFolder(6)

    # Assign object to hold all inbox emails
    messages = inbox.Items

    # Create dictionary for holding E-Designation text file creation date (key) and associated attachment (value)
    e_des_dict = {}

    # Loop through all inbox messages.
    for message in messages:
        try:
            # Assign email properties
            body_content = message.body
            subject_content = message.Subject
            sender_email = message.SenderEmailAddress
            message_author = message.Sender
            message_date_str = str(message.SentOn)
            message_date = datetime.datetime.strptime(message_date_str, "%m/%d/%y %H:%M:%S")

            # Check that "Latest E-Designation data file as of" exists within email subject line
            if "Latest" in subject_content and "SUSAN WONG" in sender_email:
                date_index = subject_content.find("as of") + 6
                e_des_date = subject_content[date_index:].strip()
                e_des_dt = datetime.datetime.strptime(e_des_date, "%m/%d/%Y")
                print("E-Designation email found - {}".format(subject_content))
                print("Adding email date: {} to E-Des dictionary".format(e_des_date))
                attachments = message.Attachments

                # Check that the particular email has an attachment otherwise continue the loop
                if len(attachments) > 0:
                    attachment = attachments.Item(1)
                    e_des_dict[e_des_dt] = attachment
                else:
                    continue
        # Handle errors in which particular email properties are Unknown
        except AttributeError as error:
            print("This particular email returned an Unknown sender. Skipping")
            continue
        # Handle errors in which particular email properties contain invalid/unreadable characters
        except UnicodeEncodeError as error:
            print("This particular email returned a sender value with an invalid character. Skipping")
            continue

    # Get the most recent E-Designation email and convert it to both datetime and formatted string objects
    latest_edes = max(e_des_dict.keys())
    latest_edes_str = latest_edes.strftime("%Y%m%d")
    print("Latest E-Designation text file found - {}".format(latest_edes_str))

    # Build email to send to GIS Team if a new E-Designation file was detected

    outlook = win32com.client.Dispatch("Outlook.Application")
    email_msg = outlook.CreateItem(0x0)
    email_msg.To = email_recipient
    email_msg.Subject = "E-Designation GIS Team Confirmation - {}".format(e_des_date)
    email_msg.Body = "Greetings, \n\n" \
               "This email is to notify GIS Team that an E-Designation text file was sent on {}. \n\n" \
               "Please check the E-Designation archive directory to ensure that the file was correctly added. \n\n" \
               "Also check the E-Designation script logs to confirm the generation script ran successfully. \n\n" \
               "If the E-Designation file was archived correctly and the script log/temp directory indicates " \
               "successful generation all that is left to do is run the E-Designation Distribution script to migrate " \
               "the updated data set to the SDE and layer files. \n\n" \
               "Thank you very much!".format(e_des_date)

    # Check the E-Designation archive for the existence of the most recent E-Designation email attachment
    if os.path.exists(os.path.join(edes_archive_path, "{}_{}.txt".format(str(e_des_dict[latest_edes])[:5], latest_edes_str))):
        # If the most recent E-Designation email attachment already exists in archive, log result and end script
        print("The latest E-Des text file has already been added to the appropriate path")
        print("Aborting script. "
              "If you are sure that the E-Des text file currently in archive is out-of-date. "
              "Please compare email attachment and latest E-Des archive file")
        log_new_date = ''
    else:
        # If the most recent E-Designation email attachment does not exist, save to archive, delete previous output directory, and kick off EDes Generation script
        e_des_dict[latest_edes].SaveAsFile(os.path.join(edes_archive_path, "{}_{}.txt".format(str(e_des_dict[latest_edes])[:5], latest_edes_str)))
        if os.path.exists(temp_path):
            print("Previous temp dir detected. Removing prev directory with old outputs")
            shutil.rmtree(temp_path)
            print("Beginning to run E-Designation generation script. Outputs will print below:")
            subprocess.call([python3_path, gen_script_path])
            print("Generation script complete. Sending notification email to GIS Team DL")
            email_msg.Send()
            log_new_date = e_des_date
        else:
            print("Beginning to run E-Designation generation script. Outputs will print below:")
            subprocess.call([python3_path, gen_script_path])
            print("Generation script complete. Sending notification email to GIS Team DL")
            email_msg.Send()
            log_new_date = e_des_date

    # Log total script run-time
    EndTime = datetime.datetime.now().replace(microsecond=0)
    print("Script runtime: {}".format(EndTime - StartTime))
    log.write(str(StartTime) + "\t" + str(EndTime) + "\t" + str(EndTime - StartTime) + "\t" + log_new_date + "\n")
    log.close()

except:
    print("error")
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # Log any Python errors that were encountered during script run-time
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])

    print(pymsg)

    log.write("" + pymsg + "\n")
    log.write("\n")
    log.close()