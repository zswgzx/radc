#/bin/python

# Used to check DTI processed data.
# Processed data is expected in two locations

from os import walk
from sys import exit
from itertools import chain


def main():
    scanner1_adrd = 'path_to_scanner1_adrd'
    scanner1_other = 'path_to_scanner1_other'
    scanner2_adrd = 'path_to_scanner2_adrd'
    scanner2_other = 'path_to_scanner2_other'

    # gather scan keys in ADnRD folders
    adrd_scankeys = set()
    for _, _, filenames in chain(walk(scanner1_adrd), walk(scanner2_adrd)):
        for filename in filenames:
            adrd_scankeys.add(filename.split('-')[0])
    print('ad rd scan keys:', sorted(adrd_scankeys))

    # gather {FA,TR} scankeys
    fatr_scankeys = list()
    for _, directories, _ in chain(walk(scanner1_other), walk(scanner2_other) ):
        for directory in directories:
            if directory.endswith('DMC_R1_SAVE'):
                fatr_scankeys.append(directory)
    print('fa tr scan keys:', sorted(fatr_scankeys))

if __name__ == '__main__':
    exit(main())

