import sys
from subprocess import *

from util.scan_key import Scan_key
from util.radc_utils import *
from util.ScanTypes import *


INDEX_STATUS_UPDATES = "./out/index_status_updates.sql"
NIFTI_SERIES_INSERTS = "./out/nifti_series_inserts.sql"


def main():
    print("Processing all un-indexed scans")
  
    index_updates = open( INDEX_STATUS_UPDATES, 'w' )
    nifti_series  = open( NIFTI_SERIES_INSERTS, 'w' )

    unindexed_scans = check_output(["/u3/informix/bin/dbaccess", "radc", "./sql/select_unindexed.sql"], encoding="UTF-8", stderr=DEVNULL).strip()
    # Unload format:
    # id   projid   visit scandate     protocl  scankey
    # 2507 53600397 07    08/01/2018   UC       180801_07_53600397

    for unindexed_scan_line in unindexed_scans.splitlines():
        unindexed_scan = unindexed_scan_line.split()
        mri_id = unindexed_scan[0]
        scan_key = Scan_key(unindexed_scan[5] )
        protocol = unindexed_scan[4]


        invivo_path = getInvivoRawPath(scan_key, protocol)
        nifti_path = os.path.join(invivo_path, scan_key.projid+"_"+scan_key.visit+"_nii")

        if( not os.path.exists( nifti_path) ):
            print( "Nifti directory not found in " + nifti_path )
            continue

        index_updates.write("update mris set index_status_raw='INDEXED', index_status_raw_date=today, nifti_file_path='"+nifti_path+"' where id='"+mri_id+"';\n")

        nifti_entries = [];

        for entry in os.scandir( nifti_path ):
            if( entry.is_dir() ):
                # This is a directory, skipping
                continue
            elif( "nii" in entry.name ):
                nifti_entries.append( entry )

        
        for nifti in nifti_entries:
            scan_type = find_matching_scantype_for_nifti( nifti.name )
            nifti_series.write("insert into mri_invivo_nifti (mri_id, scan_type, file_path) values ("+mri_id+", '"+scan_type.get_enum_value()+"', '"+nifti.path+"');\n")
            
            
            

    index_updates.close()
    nifti_series.close()




#  for entry in entries:
#        arr_entry = entry.split("|")
#        scan_key = Scan_key(arr_entry[0])
#        protocol = arr_entry[1]

#        invivo_path = getInvivoRawPath(scan_key, protocol);
#        nifti_path = os.path.join(invivo_path, scan_key.projid+"_"+scan_key.visit+"_nii")

#        os.mkdir(OUTPUT_DIR + scan_key.projid + "_" + scan_key.visit)

#        print( "Searching for " + nifti_path )
#        if( os.path.isdir( nifti_path )):
#            copytree(nifti_path, OUTPUT_DIR + scan_key.projid + "_" + scan_key.visit+"/" )





if __name__ == '__main__':
    sys.exit(main())

