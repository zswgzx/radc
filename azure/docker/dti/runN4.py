#!/home/shengwei/anaconda3/bin/python

from os import path, system, cpu_count
from sys import exit
import argparse
from pathos.multiprocessing import ProcessPool as Pool
from tqdm import tqdm

def get_scans(filename):
    """ get the scan keys from file """
    with open(filename, 'r') as f:
        scan_keys = f.read().splitlines()
    return scan_keys


def bias_correct(filename, scanner, scan_key):
    """ check file existence, and output the N4 correction command to run if exists """
    if path.isfile(filename):
        if scanner == 'mg':
            filename_no_extension = path.splitext(filename)[0]
            modality = filename_no_extension.split('/')[-1].split('-')[0].lower()
            if modality == 'mprage':
                modality = 't1'
        elif scanner == 'uc':
            filename_no_extension = path.splitext(path.splitext(filename)[0])[0]
            modality = filename_no_extension.split('/')[-1]
            if len(modality) == 18:
                modality = 'flair'
            if modality == 't1-reorient':
                modality = 't1'
        command = 'N4BiasFieldCorrection ' \
                  '-d 3 ' \
                  '-s 2 ' \
                  '-c [50x50x50x50,1e-9] ' \
                  '-b [200] ' \
                  '-i {} ' \
                  '-o /media/shengwei/BackupData/totalVol/{}/' \
                  '{}-n4corrected/{}-n4.nii.gz'.format(filename, scanner, modality, scan_key)
        return command
    else:
        return None
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scanner', dest='scanner', action='store', nargs=1, default=None,
        help='Run N4 correction on flair and t1 images from specific scanner (mg or uc)')
    args = parser.parse_args()
    scanner=args.scanner[0]

    scan_keys = get_scans('subjects')
    if scanner == 'mg':
        commands = [bias_correct(scan_key + '/FLAIR-corrected.nii.gz',
            scanner, scan_key) for scan_key in scan_keys]
        commands.extend([bias_correct(scan_key + '/MPRAGE-corrected-reorn.nii.gz', 
            scanner, scan_key) for scan_key in scan_keys])
    elif scanner == 'uc':
        commands = [bias_correct('/home/shengwei/work/vbm/uc/flair/raw/' + scan_key + '.nii.gz',
            scanner, scan_key) for scan_key in scan_keys]
        commands.extend([bias_correct('/media/shengwei/BackupData/fmri/uc/150908/' \
            + scan_key + '/t1-reorient.nii.gz', scanner, scan_key) for scan_key in scan_keys])
    else:
        print('Type -h for usage, exiting...')
        exit(1)

    with Pool(cpu_count()-2) as pool:
        for _ in tqdm(pool.imap(system, commands), total = len(commands)):
            pass

