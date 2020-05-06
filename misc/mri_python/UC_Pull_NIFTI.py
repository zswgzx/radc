#/bin/python

import sys
from shutil import copyfile

from invivo.util.radc_utils import *
from util.scan_key import Scan_key

OUTPUT_DIR = "/san1/mri_pull/uc/"

def main():
	with open("/home/datamgt/aburgess/temp/uc.dat") as lines:
		entries = lines.read().splitlines()
	
	for entry in entries:
		arr_entry = entry.split("|") 
		scan_key = Scan_key( arr_entry[3] )
		protocol = arr_entry[4]

		invivo_path = getInvivoRawPath( scan_key, protocol );
		
		nii_zips = find_nii_zips( invivo_path )
		
		if( len(nii_zips) < 1 ):
			print "WARNIGN: Nii.zip not found in " + invivo_path
			continue

		os.mkdir( OUTPUT_DIR+scan_key.projid+"_"+scan_key.visit )

		bfilesPresent = False		
		for root, dirs, files in os.walk(invivo_path):
		        for name in files:
		            if name.endswith(".bvec", re.IGNORECASE) or name.endswith(".bval", re.IGNORECASE):
		                copyfile( os.path.join(root, name), OUTPUT_DIR+scan_key.projid+"_"+scan_key.visit+"/"+name )
                  		bfilesPresent = True

		if bfilesPresent != True:
			print "WARNING: No BFiles found in " + invivo_path


		for zip in nii_zips:
			nii_zip_name = os.path.basename(zip.filename)
			copyfile( zip.filename, OUTPUT_DIR+scan_key.projid+"_"+scan_key.visit+"/"+nii_zip_name )		
			print "Successfully pulled "+ scan_key.projid + " " + scan_key.visit

if __name__ == '__main__':
    sys.exit(main())
