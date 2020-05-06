#/bin/python

# This program is intended to convert all dicom zips under a parent folder into nifti
import os
import sysz
import shutil
from shutil import copyfile

from mri_wrapper import mri_wrapper
#from dcm2nii import convertDicom2Nifti
from subprocess import call
from radc_utils import *
import zipfile
from zipfile import ZipFile

STAGING_DIR = "/san1/mri_convert/staging"
OUTPUT_DIR = "/san1/mri_convert/result"
FINAL_DIR = "/san1/mri_convert/zips"


def main():
    # Open file and read into memory - not as efficient, but resolves new line issue
    with open("/home/datamgt/user/temp/MPRAGE_3T_paths.dat") as f:
        content = f.read().splitlines()
    for line in content:
        wrapper = mri_wrapper( line )
        clear_staging_folders()
        dicom_zips = find_dicom_zips(line)
        final_result_dir =  FINAL_DIR+"/"+wrapper.protocol+"/"+wrapper.projid+"_"+wrapper.visit;
	print "Checking " + line
	if os.path.exists( final_result_dir):
		print "Already added"
		continue
        for zip in dicom_zips:
            mri_session = mri_wrapper(zip.filename)
	    if not os.path.exists( OUTPUT_DIR+"/"+mri_session.projid+"_"+mri_session.visit ):
	        os.mkdir(OUTPUT_DIR+"/"+mri_session.projid+"_"+mri_session.visit)
            print "Unzipping " + zip.filename
            zip.extractall(STAGING_DIR)
            zip.close()
            print "Converting " + zip.filename
            # converted_files = convertDicom2Nifti(STAGING_DIR, OUTPUT_DIR+"/"+mri_session.projid+"_"+mri_session.visit)
            convertDicom( STAGING_DIR, OUTPUT_DIR+"/"+mri_session.projid+"_"+mri_session.visit )

	
	if os.path.exists( final_result_dir):
		os.rename( final_result_dir, final_result_dir+"(2)" )

        os.mkdir( final_result_dir )
        for root, dirnames, filenames in os.walk(OUTPUT_DIR):
            for filename in filenames:
                if "mpr" in filename.lower():
                    copyfile( root+"/"+filename, final_result_dir+"/"+filename )


def convertDicom( dicom_dir, out_dir ):
    os.chdir(dicom_dir)
    call(["/home/datamgt/MRI/programs/mricron/dcm2nii", "-o", out_dir, "-x", "n", "-r", "n", "-e", "n", "-d", "n", "-g",  "n", dicom_dir] )


def clear_staging_folders():
    print "Clearing staging folders"
    if os.path.isdir(STAGING_DIR):
        os.system('rm -fr "%s"' % STAGING_DIR)
        os.mkdir(STAGING_DIR)

    if os.path.isdir(OUTPUT_DIR):
        os.system('rm -fr "%s"' % OUTPUT_DIR)
        os.mkdir(OUTPUT_DIR)
    print "Finished clearing"


if __name__ == '__main__':
    sys.exit(main())
