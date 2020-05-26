#!/bin/python3

import grp
import logging
import os
import pwd
import re
import shutil
import sys
import tarfile
import zipfile

_STAGING_DIR = '/san1/mri_convert/staging'
_CONVERT_BASE_DIR = '/san1/test/'


# This class obtains meta data (i.e. date, visit, projid, protocol) of scan from its path
class MriWrapper(object):
    def __init__(self, path):
        self.path = path
        scankey_search = re.search('\d{6}_\d{2}_\d{8}', path)

        if scankey_search is None:
            sys.exit('Could not find scan key from ' + path)
        else:
            scan_key = scankey_search.group(0).split('_')
            self.date = scan_key[0]
            self.visit = scan_key[1]
            self.projid = scan_key[2]

        if re.search('bannockburn', path):
            self.protocol = ('bannockburn',)
        elif re.search('mg', path):
            self.protocol = ('mg',)
        elif re.search('uc', path):
            self.protocol = ('uc',)
        else:
            sys.exit('No such active or valid protocol exists')


#----------
def find_dicom(base_path):
    for entry in os.scandir(base_path):
        if not entry.name.startswith('.') and entry.is_file():
            if entry.name.endswith('.zip', re.IGNORECASE) or entry.name.endswith('.tar.gz', re.IGNORECASE):
                if re.search('nii|nifti|nifti|par|P\d{5,6}.zip', entry.name, re.IGNORECASE) is None:
                    if zipfile.is_zipfile(entry.path):
                        if check_dicom_zip(ZipFile(entry.path)):
                            return entry
                    elif tarfile.is_tarfile(entry.path):
                        if check_dicom_tar(tarfile.open(entry.path, 'r|gz')):
                            return entry
                    else:
                        sys.exit('DICOM not found or invalid in ' + base_path)


# This checks a zip file for any entry that matches "dicom"
# Returns true if the zip contains dicom, false otherwise
def check_dicom_zip(zip_file):
    for entry in zip_file.namelist():
        if re.search('dicom', entry, re.IGNORECASE):
            return True
    return False

# TODO: speed up by iterating over files manually and returning when dicom is found (vs using getnames())
def check_dicom_tar(tar_file):
    for entry in tar_file.getnames():
        if re.search('dicom', entry, re.IGNORECASE) is not None:
            return True
    return False

#----------
def __test_convert():
    for entry in os.scandir(_CONVERT_BASE_DIR):
        convert_dicom_to_nifti(entry, _CONVERT_BASE_DIR, True)


def convert_dicom_to_nifti(dicom_entry, output_dir, unzip=None):
    if unzip:
        if dicom_entry.is_dir():
            raise IsADirectoryError('DICOM entry ' + dicom_entry + ' is a folder. ' + \
                'Please pass in a compressed file.');

        # unzip dicom to staging directory
        if dicom_entry.name.endswith(".zip", re.IGNORECASE):
            print("Unzipping " + dicom_entry.name)
            try:
                zipfile.ZipFile(dicom_entry.path).extractall(_STAGING_DIR)
            except zipfile.BadZipfile:
                sys.exit('Bad zipfile! Skipping')
        elif dicom_entry.name.endswith(".tar.gz", re.IGNORECASE):
            print("Untarring " + dicom_entry.name)
            tarfile.open(dicom_entry.path, "r:gz").extractall(_STAGING_DIR)
        else:
            sys.exit('DICOM entry not recognized. Skipping ' + dicom_entry.name)

    __convert_dicom_dir(_STAGING_DIR, output_dir)


def convert_dicom_dir(dicom_dir):
    print('Checking DICOM in ' + dicom_dir)
    logging.basicConfig(filename='convert.log', filemode='w', level=logging.INFO)

    dicom = find_dicom(dicom_dir)
    if not dicom:
        logging.error('No DICOM in ' + dicom_dir)
    else:
        logging.log(logging.INFO, 'Converting ' + dicom.path)
        wrapper = MriWrapper(dicom.path)

        output_dir = os.path.join(os.path.dirname(dicom.path), wrapper.projid + '_' + wrapper.visit + '_nii')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        else:
            print('Scan directory already exists. Skipping ' + output_dir)

        __clear_staging_folders()

        convert_dicom_to_nifti(dicom, output_dir, True)

        userId = pwd.getpwnam('mriadmin').pw_uid
        groupId = grp.getgrnam('mri').gr_gid
        for root, dirs, files in os.walk(output_dir):
            for subdir in dirs:
                os.chown(os.path.join(root, subdir), userId, groupId)
            for file in files:
                os.chown(os.path.join(root, file), userId, groupId)


# Private conversion method
def __convert_dicom_dir(src_dir, dst_dir):
    print('Starting conversion')
    try:
        os.system('dcm2niix -i y -f %d -v n -z y -o ' + dst_dir + ' ' + src_dir)
    except Exception:
        sys.exit('Error converting, cleaning up ' + src_dir)


def __clear_staging_folders():
    print( 'Clearing staging folders')
    if os.path.isdir(_STAGING_DIR):
        shutil.rmtree(_STAGING_DIR)
        os.mkdir(_STAGING_DIR)


if __name__ == '__main__':
    __test_convert()
    sys.exit()
