# /bin/python3

import sys
from shutil import copyfile

from invivo.util.radc_utils import *
from util.scan_key import Scan_key

OUTPUT_DIR = "/san1/mri_pull/"


def main():
    with open("/home/datamgt/aburgess/temp/toPull.dat") as lines:
        entries = lines.read().splitlines()

    for entry in entries:
        arr_entry = entry.split("|")
        scan_key = Scan_key(arr_entry[3])
        protocol = arr_entry[4]

        invivo_path = getInvivoRawPath(scan_key, protocol);
        nifti_path = os.path.join(invivo_path, scan_key.projid+"_"+scan_key.visit+"_nii")

        if( os.path.isdir( nifti_path )):
            os.mkdir(OUTPUT_DIR + scan_key.projid + "_" + scan_key.visit)

            copyfile(nifti_path, OUTPUT_DIR + scan_key.projid + "_" + scan_key.visit )


if __name__ == '__main__':
    sys.exit(main())
