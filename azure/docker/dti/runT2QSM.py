#!/home/shengwei/anaconda3/bin/python

from zipfile import ZipFile
from nipype.interfaces.dcm2nii import Dcm2niix
from os import cpu_count, chdir, system
from shutil import rmtree
import argparse
from pathos.multiprocessing import ProcessPool as Pool
from tqdm import tqdm


def get_scans(filename):
    """ get the scan keys from file """
    with open(filename, 'r') as f:
        scan_keys = f.read().splitlines()
    return scan_keys


def convert_dcm(scan_key):
    """ convert dicom with dcm2niix """
    chdir(scan_key)
    ZipFile('dicomdata.zip').extractall()

    converter = Dcm2niix()
    converter.inputs.source_dir = './dicomdata/DICOM/'
    converter.inputs.output_dir = '.'
    converter.inputs.ignore_deriv = True
    converter.inputs.single_file = True
    converter.inputs.out_filename = "%d"
    converter.run()

    rmtree('dicomdata')
    system('rm *.json *.zip [DEFMS]* T2*a.nii.gz Q*[1-5].nii.gz')
    return converter.cmdline


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--IDlist', dest='id_list', action='store', nargs=1, default=None,
        help='Run dcm2niix on scans with merged T2mapping & QSM image')
    args = parser.parse_args()
    id_list=args.id_list[0]

    scan_keys = get_scans(id_list)

    with Pool(cpu_count()-2) as pool:
        for _ in tqdm(pool.imap(convert_dcm, scan_keys), total = len(scan_keys)):
            pass

