#/bin/python

import logging
import sys
from shutil import copyfile
from subprocess import call

from invivo.util.radc_utils import *
from util.scan_key import Scan_key

STAGING_DIR = 'staging'
OUTPUT_DIR = 'result'
FINAL_DIR = 'zips'


def main():
    logging.basicConfig(filename='convert_bfiles.log', filemode='w', level=logging.INFO)

    with open('NIGHTLY/MRI/uc_scankeys.dat') as keys:
        scankey_protocols = keys.read().splitlines()

    for scankey_protocol in scankey_protocols:
        arr_scankey_protocol = scankey_protocol.split('|')
        scankey = Scan_key(arr_scankey_protocol[0])
        protocol = arr_scankey_protocol[1]

        invivo_path = getInvivoRawPath(scankey, protocol)
        bfiles = False

        for _, _, files in os.walk(invivo_path):
            for file in files:
                if file.endswith('.bvec', re.IGNORECASE) or file.endswith('.bval', re.IGNORECASE):
                    bfiles = True
                    break

        if bfiles:
            logging.info( 'bfiles present, skipping')
            continue

        # Look for dicom to convert
        dicom_zips = find_dicom_zips(invivo_path)

        if (len(dicom_zips) == 0):
            logging.error('No DICOM zip found in ' + invivo_path)
            continue

        if (len(dicom_zips) > 1):
            logging.warning( 'Multiple dicom zips found in ' + invivo_path + ' using ' + dicom_zips[0].filename )

        dicom_zip = dicom_zips[0];

        clear_staging_folders()

        try:
            dicom_zip.extractall(STAGING_DIR)
        except zipfile.BadZipfile:
            logging.error('Bad zip file ' + invivo_path + '.' )
            continue

        dicom_zip.close();

        convertDicom(STAGING_DIR, OUTPUT_DIR)
        bfiles_created = False

        #look for resulting bfiles, and copy
        for _, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                if file.endswith('.bvec', re.IGNORECASE):
                    bfiles_created = True
                    absname = os.path.abspath(os.path.join(root, file))
                    copyfile(absname, invivo_path + '/' + scankey.projid + '_' + scankey.visit + '.bvec')

                if file.endswith('.bval', re.IGNORECASE):
                    absname = os.path.abspath(os.path.join(root, file))
                    copyfile(absname, invivo_path + '/' + scankey.projid + '_' + scankey.visit + '.bval')

        if bfiles_created:
            logging.warning('Bfiles created for ' + scankey.projid + ' ' + scankey.visit)


def convertDicom(dicom_dir, out_dir):
    os.chdir(dicom_dir)
    call(['dcm2niix', '-o', out_dir, '-f', '%d', '-i', 'y', '-v', 'n', '-z', 'y', dicom_dir])


def clear_staging_folders():
    print('Clearing staging folders')
    if os.path.isdir(STAGING_DIR):
        os.system('rm -fr "%s"' % STAGING_DIR)
        os.mkdir(STAGING_DIR)

    if os.path.isdir(OUTPUT_DIR):
        os.system('rm -fr "%s"' % OUTPUT_DIR)
        os.mkdir(OUTPUT_DIR)
    print('Finished clearing')


if __name__ == '__main__':
    sys.exit(main())

