#!/bin/python3

import pwd, grp, os, sys, shutil, zipfile, tarfile, re
import logging

from nipype.interfaces.dcm2nii import Dcm2niix

from nipype.interfaces.fsl import Merge

from util.mri_wrapper import Mri_wrapper
from util.radc_utils import find_dicom

_STAGING_INPUT = "/san1/mri_convert/staging"
logging.basicConfig(filename='convert.log', filemode='w', level=logging.INFO)

def __test_convert():
    for entry in os.scandir("/san1/test/"):
        convert_dicom_to_nifti( entry, "/san1/test/")


def convert_dicom_directory(dicom_directory):
    print("Checking for dicom in " + dicom_directory)
    dicom = find_dicom(dicom_directory)
    if not dicom:
        logging.error("No dicom found in " + dicom_directory)
    else:
        logging.log(logging.INFO, "Converting " + dicom.path)
        wrapper = Mri_wrapper(dicom.path)

        output_directory = os.path.join(os.path.dirname(dicom.path), wrapper.projid + "_" + wrapper.visit + "_nii")
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)
        else:
            print("Warning scan directory already exists. Skipping. " + output_directory)
            return

        # Clear staging directories
        __clear_staging_folders()

        convert_dicom_to_nifti(dicom, output_directory, True)

        # There's a bug with dcm2niix where the Morton Grove gre_field_mapping looses a volume with "merge" flag on
        # We need to run dcm2niix on that series without merge, and merge it manually later
        if wrapper.protocol == "mg":
            print("Delete phase map and reconvert series w/o merge")

            if os.path.isfile(os.path.join(output_directory, "gre_field_mapping_e1.nii.gz")):
                os.remove(os.path.join(output_directory, "gre_field_mapping_e1.nii.gz"))
                os.remove(os.path.join(output_directory, "gre_field_mapping_e1.json"))
            elif os.path.isfile(os.path.join(output_directory, "gre_field_mapping_e2.nii.gz")):
                os.remove(os.path.join(output_directory, "gre_field_mapping_e2.nii.gz"))
                os.remove(os.path.join(output_directory, "gre_field_mapping_e2.json"))
            else:
                print("Warning: could not find gre_field_mapping_e1(2).nii.gz for scan. " + output_directory)
                return

            # Phase map is series 10 at Morton Grove
            convert_dicom_to_nifti(dicom, output_directory, False,  False, ["10"])
            phase1 = os.path.join(output_directory, "gre_field_mapping_e1.nii.gz")
            phase2 = os.path.join(output_directory, "gre_field_mapping_e2.nii.gz")
            if (os.path.exists(phase1)) and (os.path.exists(phase2)):
                merger = Merge()
                merger.inputs.in_files = [phase1, phase2]
                merger.inputs.dimension = 'a'
                merger.inputs.output_type = 'NIFTI_GZ'
                merger.inputs.merged_file = os.path.join(output_directory, "gre_field_mapping_merged.nii.gz")
                print(merger.cmdline)
                try:
                    merger.run()
                    os.remove(phase1)
                    os.remove(phase2)
                except Exception as e:
                    print("Whoops!")
                    print(e)
            else:
                print("Error generating 2Vol Phase Maps. Skipping " + output_directory)

        userId = pwd.getpwnam("mriadmin").pw_uid
        groupId = grp.getgrnam("mri").gr_gid
        for root, dirs, files in os.walk(output_directory):
            for subdir in dirs:
                os.chown(os.path.join(root, subdir), userId, groupId)
            for file in files:
                os.chown(os.path.join(root, file), userId, groupId )

def convert_dicom_to_nifti(dicomFileEntry, outputDirectory, unzip=None, mergeFiles=None , seriesList=None):

    if unzip:
        if dicomFileEntry.is_dir():
            raise IsADirectoryError("Dicom path " + dicomFileEntry + " is a directory. Please pass in a compressed file.");

        # unzip dicom to staging directory
        if dicomFileEntry.name.endswith(".zip", re.IGNORECASE):
            print("Unzipping " + dicomFileEntry.name)
            try:
                zipfile.ZipFile(dicomFileEntry.path).extractall(_STAGING_INPUT)
            except zipfile.BadZipfile:
                print("Whoa bad zipfile! Skipping")
                return

        elif dicomFileEntry.name.endswith(".tar.gz", re.IGNORECASE):
            print("Untarring " + dicomFileEntry.name)
            tarfile.open(dicomFileEntry.path, "r:gz").extractall(_STAGING_INPUT)

    __convert_dicom_directory(_STAGING_INPUT, outputDirectory, mergeFiles, seriesList)


# Private conversion method
def __convert_dicom_directory( sourceDir, outputDir, mergeFiles, seriesList ):

    #Default merge files If mergeFiles param is None (empty)
    if mergeFiles == None:
        mergeFiles = True;

    print( "Starting conversion")
    converter = Dcm2niix()
    converter.inputs.source_dir = sourceDir
    converter.inputs.output_dir = outputDir
    converter.inputs.ignore_deriv = True
    converter.inputs.merge_imgs = mergeFiles
    converter.inputs.single_file = True
    converter.inputs.out_filename = "%d"

    if seriesList is not None:
        converter.inputs.series_numbers = seriesList

    print(converter.cmdline)
    try:
        converter.run()
    except Exception as e:
        print("Error converting nifti, cleaning up: " + sourceDir)
        print(e)
        return False

def __clear_staging_folders():
    print( "Clearing staging folders")
    if os.path.isdir(_STAGING_INPUT):
        shutil.rmtree(_STAGING_INPUT)
        os.mkdir(_STAGING_INPUT)



if __name__ == '__main__':
    __test_convert()
    sys.exit()


