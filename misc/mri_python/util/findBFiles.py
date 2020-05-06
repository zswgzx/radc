import glob
import os
import sys

from shutil import copyfile

# Quick and dirty script to find and copy bfiles
def main(argv):
   filepath = '../target/scans.dat'
   output_dir = '/home/alec/temp/mg/'
   with open(filepath) as fp:
      for cnt, line in enumerate(fp):
          line_a = line.split('/');
          projid_visit_a = line_a[2].split("_")
          projid = projid_visit_a[0]
          visit  = projid_visit_a[1]
          bfiles = glob.glob('/mri/invivo/raw/mg/**/'+projid+"_"+visit+"_nii/*.bv*", recursive=True)
          if( bfiles == [] ):
             print( "no bfiles found for projid:{} visit:{}".format( projid, visit) )
          else:
             temp_output_path = output_dir+projid+"_"+visit+"/"
             os.mkdir(temp_output_path)
             for bfile in bfiles:
                print( os.path.basename(bfile) )
                copyfile(bfile, temp_output_path + os.path.basename(bfile))


   sys.exit(0)
if __name__ == "__main__":
   main(sys.argv[1:])
