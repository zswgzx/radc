#/bin/python

# Intended to pull 3T processed DTI data to a staging folder for distribution
# /mri/invivo/processed/dti/[scanner]/[start-date]/[subj]_proc/[subj]_DMC_R1_SAVE/*{FA,TR}.nii.gz


import sys
from shutil import copyfile

from invivo.util.radc_utils import *
from util.scan_key import Scan_key


def main():

    STAGING_DIRECTORY="/san1/mri_pull/"

    with open("/home/datamgt/aburgess/work/zhu_mri/scankeys.dat") as lines:
        entries = lines.read().splitlines()

    map_scankeys = list()
    for entry in entries:
        map_scankeys.append(entry)

    copied_raw = list()
    for root, directories, filenames in itertools.chain(os.walk("/mri/invivo/processed/dti/mg"),
                                                        os.walk("/mri/invivo/processed/dti/uc")):
        for filename in filenames:
            filename_upper = filename.upper()
            if filename_upper.endswith("FA.NII.GZ") or filename_upper.endswith("TR.NII.GZ"):
                # split root (base directory) by slash
                # expected format:
                #  /mri/invivo/processed/dti/uc/120221/140307_04_68289181_proc/140307_04_68289181_DMC_R1_SAVE/
                # 0/1  /2     /3        /4  /5 /6     /7                      /8

                a_root = root.split("/");
                location = a_root[5]
                startdate = a_root[6]

                # determine scankey
                scan_key_str = a_root[8].split("_DMC_")[0]
                scan_key = Scan_key(scan_key_str)

                if scan_key_str not in map_scankeys:
                    continue

                # print root+"/"+filename

                result_filename = ""
                if filename_upper.endswith("FA.NII.GZ"):
                    result_filename = scan_key.projid+"_"+scan_key.visit+"_DMC_R1_FA.nii.gz"
                else:
                    result_filename = scan_key.projid + "_" + scan_key.visit + "_DMC_R1_TR.nii.gz"

                destination = STAGING_DIRECTORY+location+"/"+startdate+"/"+scan_key.projid+"_"+scan_key.visit

                if not os.path.exists(destination):
                    os.makedirs(destination)

                copyfile(root+"/"+filename, destination+"/"+result_filename)

                #find raw invivo path
                invivo_path = getInvivoRawPath( scan_key, location.upper() )
                nii_zips = find_nii_zips(invivo_path)
                if (len(nii_zips) < 1):
                    print "WARNIGN: Nii.zip not found in " + invivo_path
                    continue

                if scan_key_str in copied_raw:
                    continue

                print "Copying raw " + scan_key.projid + " " + scan_key.visit
                for zip in nii_zips:
                    nii_zip_name = os.path.basename(zip.filename)
                    copyfile(zip.filename, destination+"/"+scan_key.projid+"_"+scan_key.visit+"_nii.zip" )
                    print "Successfully pulled " + scan_key.projid + " " + scan_key.visit

                #copy bfiles
                for invroot, dirs, invivofiles in os.walk(invivo_path):
                    for name in invivofiles:
                        if name.endswith(".bvec", re.IGNORECASE) or name.endswith(".bval", re.IGNORECASE):
                            copyfile(os.path.join(invroot, name),
                                     destination + "/" + name)

                copied_raw.append(scan_key_str)



if __name__ == '__main__':
    sys.exit(main())