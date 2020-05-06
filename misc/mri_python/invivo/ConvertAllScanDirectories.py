# /bin/python3

# This program is intended to convert all dicom zips missing nifti
import logging
import os
import sys
from shutil import copyfile
from subprocess import call

import re
from nipype.interfaces.fsl import Merge

from util.ConvertDicomToNifti import convert_dicom_directory

MRI_BASE = '/mri/invivo/raw/mg/160627'


# Looks for all scan paths ([date]_[visit]_[projid]) in the (MRI_BASE) directory and attempts to convert them to nifti
# Intended as a massive converter
def main():
    logging.basicConfig(filename='convert.log', filemode='w', level=logging.INFO)

    # Find all scan directories
    # They must be directly under a startdate folder
    scan_dirs = []
    for root, dirs, files in os.walk(MRI_BASE):
        for tempDir in dirs:
            # Check if we're in a startdate directory:
            tempBase = os.path.basename( root );
            startDateSearch = re.fullmatch("\d{6}", tempBase )
            if startDateSearch:
                # Check if the directory is in the expected format
                scanFolderSearch = re.search("\d{6}_\d{2}_\d{8}", tempDir )
                if scanFolderSearch:
                    scan_dirs.append( os.path.join(root, tempDir));

            else:
                # Not searching a start date folder
                # Prevent searching too deep in the directory tree
                continue

    # print( "Found " + len(scan_dirs) + " scan dirs to convert")

    for scan_dir in scan_dirs:
        convert_dicom_directory( scan_dir )


if __name__ == '__main__':
    sys.exit(main())
