#/bin/python

# Used to check DTI processed data.
# Processed data is expected in two locations

import os
import sys
import itertools


def main():
    scanner1_adrd = 'path_to_scanner1_adrd'
    scanner1_other = 'path_to_scanner1_other'
    scanner2_adrd = 'path_to_scanner2_adrd'
    scanner2_other = 'path_to_scanner2_other'

    # gather scan keys in ADnRD folders
    adrd_scankeys = list()
    for root, directories, filenames in itertools.chain(os.walk(scanner1_adrd),
                                                    os.walk(scanner2_adrd) ):
        for filename in filenames:
            a_filename = filename.split("-")
            adrd_scankeys.append( a_filename[0])

    # gather {FA,TR} scankeys
    fatr_scankeys = list()
    for root, directories, filenames in itertools.chain(os.walk(scanner1_other),
                                                    os.walk(scanner2_other) ):
        for directory in directories:
            if directory.endswith( "DMC_R1_SAVE"):
                print(directory)

if __name__ == '__main__':
    sys.exit(main())

