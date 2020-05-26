import itertools
import os
import re
import tarfile
import zipfile

from datetime import datetime, strftime
from zipfile import ZipFile

# This is the primary holder for common methods used accross all the RADC MRI Python applications

MRI_RAW_BASE_DIR = '/mri/invivo/raw/'


def find_dicom(base_path):
    for entry in os.scandir(base_path):
        if not entry.name.startswith('.') and entry.is_file():
            if entry.name.endswith('.zip', re.IGNORECASE) or entry.name.endswith('.tar.gz', re.IGNORECASE):
                if re.search('nii|nifti|nifti|par|P\d{5,6}.zip|phantom|acr', entry.name, re.IGNORECASE) is None:
                    if zipfile.is_zipfile(entry.path):
                        if check_dicom_zip(ZipFile(entry.path)):
                           return entry
                    elif tarfile.is_tarfile(entry.path):
                        if check_dicom_tar(tarfile.open(entry.path, 'r|gz')):
                            return entry
                    else:
                        print('Invalid dicom')

# This method traverses a directory searching for dicom zips
# Returns an array of dicom zips
def find_dicom_zips(base_path):
    dicom_zips = []
    for root, dirs, files in os.walk(base_path):
        for name in files:
            if name.endswith('.zip', re.IGNORECASE):
                if re.search('nii|nifti|nifti|par|P\d{5,6}.zip|phantom|acr', name, re.IGNORECASE) is None:
                    temp_zip = ZipFile(os.path.join(root, name))
                    if check_dicom_zip(temp_zip):
                        dicom_zips.append(temp_zip)
    return dicom_zips


def find_nii_zips(base_path):
    nii_zips = []
    for root, dirs, files in os.walk(base_path):
        for name in files:
            if  name.endswith('nii.zip', re.IGNORECASE)  or name.lower() == 'niftii.zip':
                temp_zip = ZipFile(os.path.join(root, name))
                nii_zips.append(temp_zip)
    return nii_zips


# This method checks a zip file for any entry that matches "dicom"
# Returns true if the zip contains dicom, false otherwise
def check_dicom_zip(zip_file):
    for entry in zip_file.namelist():
        if re.search('dicom', entry, re.IGNORECASE) is not None:
            return True
    return False

# todo: speed up by iterating over files manually and returning when dicom is found (vs using getnames())
def check_dicom_tar(tar_file):
    for entry in tar_file.getnames():
        if re.search('dicom', entry, re.IGNORECASE) is not None:
            return True
        else:
            return False


# This method zips the contents of "nii_folder" and places it in "final_directory/projid_visit_nii.zip" 
def zip_nii(nii_folder, projid, visit, dest_dir):
    result_zip = zipfile.ZipFile(dest_dir + '/' + projid + '_' + visit + '_nii.zip', 'w')
    for root, dirs, files in os.walk(nii_folder):
        for file in files:
            result_zip.write(os.path.join(root, file), projid + '_' + visit + '/' + file)


# Searches MRI_RAW_BASE_DIR for a directory named as the supplied scan_key
def find_path_from_scankey(scan_key):
    for root, dirs, files in itertools.chain(os.walk(MRI_RAW_BASE_DIR + 'bannockburn'),
                                             os.walk(MRI_RAW_BASE_DIR + 'mg'), 
                                             os.walk(MRI_RAW_BASE_DIR + 'uc')):
        for dir in dirs:
            if scan_key in dir:
                return os.path.join(root, dir)


# Assembles the expected invivo raw path for given scan_key and protocol
def get_raw_path(scan_key, protocol):
    if protocol == 'BNK':
        return MRI_RAW_BASE_DIR + 'bannockburn/090211/' + scan_key.scan_key
    elif protocol == 'MG':
        start_date = [datetime(2012, 5, 1)]
        start_date.append = datetime(2015, 7, 15)
        start_date.append = datetime(2016, 6, 21)
        start_date.append = datetime(2016, 6, 27)

        for i in range(1, len(start_date)):
            if scan_key.date < start_date[i]:
                return MRI_RAW_BASE_DIR + protocol.lower() + '/' + \
                    start_date[i-1].strftime("%y%m%d") + '/' + scan_key.scan_key
            else:
                return MRI_RAW_BASE_DIR + protocol.lower() + '/' + \
                    start_date[i].strftime("%y%m%d") + '/' + scan_key.scan_key
    elif protocol == 'UC':
        start_date = [datetime(2012, 2, 21)]
        start_date.append = datetime(2014, 9, 22)
        start_date.append = datetime(2015, 7, 6)
        start_date.append = datetime(2015, 11, 20)
        start_date.append = datetime(2016, 1, 25)
        start_date.append = datetime(2018, 6, 4)

        for i in range(1, len(start_date)):
            if scan_key.date < start_date[i]:
                return MRI_RAW_BASE_DIR + protocol.lower() + '/' + \
                    start_date[i-1].strftime("%y%m%d") + '/' + scan_key.scan_key
            else:
                return MRI_RAW_BASE_DIR + protocol.lower() + '/' + \
                    start_date[i].strftime("%y%m%d") + '/' + scan_key.scan_key
    else:
        sys.exit('Unrecognized MRI protocol')

def make_tarfile(dest_path, src_dir):
    print('Tarring directory' + src_dir)
    if os.path.exists(dest_path):
        sys.exit('Error: Tar file already exists. Skipping: ' + dest_path);
    else:
        os.system('tar -c -I pigz --remove-files -C ' + os.path.dirname(src_dir) \
                  + ' -f ' + dest_path + os.path.basename(src_dir))
