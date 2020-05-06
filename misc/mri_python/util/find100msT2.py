import getopt
import glob
import json
import sys

from shutil import copyfile

def main(argv):
   inputdir = ''
   outputdir = ''
   try:
      opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
   except getopt.GetoptError:
      print('find1msT2.py -i <inputdir> -o <outputdir>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('find1msT2.py -i <inputdir> -o <outputdir>')
         sys.exit()
      elif opt in ("-i", "--idir"):
         inputdir = arg
      elif opt in ("-o", "--odir"):
         outputdir = arg

   if inputdir == '':
       print( "please provide an input directory (-i)" );
       sys.exit(-1)
   if outputdir == '':
       print( "please provide an output directory (-o)" );
       sys.exit(-1)

   jsonList = glob.glob(inputdir+'/*.json')
   for jsonListing in jsonList:
       with open(jsonListing) as json_file:
           json_data = json.load( json_file )
           if "EchoTime" not in json_data:
               print( "echoTime not foud, skipping" )
               continue

           echoTime = json_data["EchoTime"];

           if "ProtocolName" not in json_data:
               print( "protocol name not found, skipping" )
               continue
           protocolName = json_data["ProtocolName"];
           if "T2_map" in protocolName and echoTime == 0.1:
               print( "Found " + jsonListing )
               niiFileName = jsonListing.replace( ".json", ".nii.gz" ) #todo: write a method to get matching nii
               print( "Copying: "+niiFileName + " to " + outputdir)
               copyfile( niiFileName, outputdir+"/T2_map_100ms.nii.gz" )
               sys.exit(0)
   print( "100ms T2 map missing for " + inputdir )
   sys.exit(-1)
if __name__ == "__main__":
   main(sys.argv[1:])
