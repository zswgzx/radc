import pwd
import grp
import os
import sys
import re
import shutil
from subprocess import *
from util.scan_key import Scan_key
from util.ScannerLocations import *
from util.ConvertDicomToNifti import convert_dicom_directory

INCOMING_DIRECTORY   = "/mri/invivo/raw/incoming" # Path where data from scanner should be placed
INCOMING_SCAN_PATHS = "./out/incoming_scans.dat" # To be loaded into the database
PROCESSING_ERRORS   = "./out/processing_errors.txt" # Where to log processing errors

def main():
    # first create flat file to load directories into database
    incoming_output = open( INCOMING_SCAN_PATHS, 'w')
    processing_errors = open( PROCESSING_ERRORS, 'a' )

    valid_entries = False # Flag used to determine if there are actually directories to move
    for entry in os.scandir( INCOMING_DIRECTORY ):
        if( entry.is_dir() ):
            # Check to see if this is a subject scan dir
            date_visit_projid_search = re.search("\d{6}_\d{2}_\d{8}", entry.name )
            if( date_visit_projid_search is not None):
                temp_incoming = entry.name.split("_")
                incoming_output.write( temp_incoming[2] +"|"+temp_incoming[0]+"|"+get_full_date(temp_incoming[0] )+"\n" )
                valid_entries = True
            else:
               print( "Invalid directory format " + entry.name + "\n")
               processing_errors.write( "Invalid directory format " + entry.name + "\n")

    incoming_output.close()

    # If there are valid entries, run sql to load flat file to temp table, and unload matching scans
    if( valid_entries ):
        matching_scans = check_output(["/u3/informix/bin/dbaccess", "radc", "./sql/invivo_incoming.sql"], encoding="UTF-8", stderr=DEVNULL).strip()

        # Read matching scan records. Each line is in the format:
        #
        for scan_match in matching_scans.splitlines():
            print( "scan_match")
            print( scan_match)
            match_arr = scan_match.split()

            temp_projid = match_arr[0]
            temp_scandate = match_arr[1]
            temp_location = match_arr[2]
            scanKey = Scan_key( match_arr[3])

            if(  temp_location == "BNK" ):
             scanLocation = Bannockburn()
            elif( temp_location == "MG" ):
                 scanLocation = MG()
            elif( temp_location == "UC" ):
                 scanLocation = UC()
            else:
                print( "Error: Unknown location " + temp_location + ". Skipping." )
                processing_errors.write( "Error: Unknown location " + temp_location + ". Skipping.\n")
                continue

           # Check for target output directory. If it already exists, log exception, and continue
            target_path = scanLocation.get_path( scanKey )
            if( os.path.exists( target_path ) ):
                print( "Error: Target directory already exists. Skipping: " + target_path )
                processing_errors.write( "Error: Target directory already exists. Skipping: " + target_path +"\n");
                continue

            scan_match_path = os.path.join( INCOMING_DIRECTORY, scanKey.scan_key )
            if( os.path.exists( scan_match_path) == False ):
                print( "Error: cannot find path matching : " + scan_match_path )
                processing_errors.write( "Error: cannot find path matching : " + scan_match_path +"\n")
                continue

            print( "Converting to nifti" )
            convert_dicom_directory( scan_match_path)
            print( "Moving "+scan_match_path + " to " + target_path )
            shutil.move( scan_match_path, os.path.dirname( target_path) )


# takes a date in the format YYMMDD and returns informix date  MM/DD/YYYY
def get_full_date( six_digit_date ):
    return six_digit_date[2:4]+"/"+six_digit_date[4:]+"/""20"+six_digit_date[0:2]

if __name__ == '__main__':
    sys.exit(main())
