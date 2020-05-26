import os
import re
import itertools
import zipfile
import datetime
from zipfile import ZipFile
import tarfile

# This is the primary holder for common methods used accross all the RADC MRI Python applications

INVIVO_BASE = '/mri/invivo/raw/'


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
                temp_zip = ZipFile(os.path.join(root,name))
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
def check_dicom_tar( tar_file ):
    for entry in tar_file.getnames():
        if re.search('dicom', entry, re.IGNORECASE) is not None:
            return True
    return False


# This method zips the contents of "nii_folder" and places it in "final_directory/projid_visit_nii.zip" 
def zip_nii( nii_folder, projid, visit, final_directory ):
    result_zip = zipfile.ZipFile(final_directory+'/'+projid+'_'+visit+'_nii.zip', 'w')
    for root, dirs, files in os.walk(nii_folder):
        for file in files:
            result_zip.write(os.path.join(root, file), projid+'_'+visit+'/'+file)


# Searches /mri/invivo/raw/* for a directory named as the supplied scan_key
def find_path_from_scanKey(scan_key):
    for root, directories, filenames in itertools.chain(os.walk('/mri/invivo/raw/bannockburn'),
                                                        os.walk('/mri/invivo/raw/mg'), os.walk('/mri/invivo/raw/uc'),
                                                        os.walk('/mri/invivo/raw/mcw')):
        for directory in directories:
            if scan_key in directory:
                return os.path.join(root, directory)


# Assembles the expected invivo raw path for a given scan_key and protocol
def getInvivoRawPath( scan_key, protocol ):
    if protocol == 'BNK':
        cutoff1 = datetime.datetime(2009, 2, 11 )
        if scan_key.date < cutoff1:
            return INVIVO_BASE+'bannockburn/061130/'+scan_key.scan_key
        return INVIVO_BASE+'bannockburn/090211/'+scan_key.scan_key

    if protocol == 'MG':
        cutoff1 = datetime.datetime(2015, 7, 15)
        cutoff2 = datetime.datetime(2016, 6, 21)
        cutoff3 = datetime.datetime(2016, 6, 27)

        if scan_key.date < cutoff1:
            return INVIVO_BASE+'mg/120501/'+scan_key.scan_key
        if scan_key.date < cutoff2:
            return INVIVO_BASE + 'mg/150715/' + scan_key.scan_key
        if scan_key.date < cutoff3:
            return INVIVO_BASE+'mg/160621/' + scan_key.scan_key
        return INVIVO_BASE + 'mg/160627/' + scan_key.scan_key

    if protocol == 'UC':
        cutoff1 = datetime.datetime(2014, 9, 22)
        cutoff2 = datetime.datetime(2015, 7, 6)
        cutoff3 = datetime.datetime(2015, 11, 20)
        cutoff4 = datetime.datetime(2016, 1, 25)
        cutoff5 = datetime.datetime(2018, 6, 4)

        if scan_key.date < cutoff1:
            return INVIVO_BASE + 'uc/120221/' + scan_key.scan_key
        if scan_key.date < cutoff2:
            return INVIVO_BASE + 'uc/140922/' + scan_key.scan_key
        if scan_key.date < cutoff3:
            return INVIVO_BASE + 'uc/150706/' + scan_key.scan_key
        if scan_key.date < cutoff4:
            return INVIVO_BASE + 'uc/151120/' + scan_key.scan_key
        if scan_key.date < cutoff5:
            return INVIVO_BASE + 'uc/160125/' + scan_key.scan_key
        return INVIVO_BASE + 'uc/180604/' + scan_key.scan_key

    return 'Error: recognized protocol'

def make_tarfile(output_file_path, source_dir):
    print( 'Tarring directory ' + source_dir );
    if( os.path.exists( output_file_path ) ):
        print( 'Error: Tar file already exists. Skipping: ' + output_file_path );
        return;
    else:
        call(['tar', '-c', '--use-compress-program=pigz', '--remove-files', '--directory', os.path.dirname(source_dir),  '-f', output_file_path, os.path.basename(source_dir)])


