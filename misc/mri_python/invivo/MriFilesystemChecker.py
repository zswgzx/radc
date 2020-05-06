#/bin/python
# Python program that reads MRI_SCANKEY|PROTOCOL unloaded from RADC:MRIS, and checks the filesystem based on the expected path.
# If  MRI(s) are missing they will be written to a file
 
import os
import sys

from util.radc_utils import getInvivoRawPath
from util.scan_key import Scan_key


def main():
    # Open file containg scan keys | protocol 
    with open("/home/datamgt/NIGHTLY/MRI/scankeys.dat") as keys:
        scan_keys_protocol = keys.read().splitlines()

    for scan_key_protocol in scan_keys_protocol:
        arr_scan_key_protocol = scan_key_protocol.split("|")
    scan_key = Scan_key(arr_scan_key_protocol[0])
    protocol = arr_scan_key_protocol[1]

    if not os.path.isdir(getInvivoRawPath(scan_key, protocol)):
        print("Can't find path for "+str(scan_key)+" "+protocol+". Expected path "+getInvivoRawPath(scan_key, protocol))

if __name__ == '__main__':
    sys.exit(main())

