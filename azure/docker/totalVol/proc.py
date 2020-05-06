#!/home/shengwei/anaconda3/bin/python

from os import listdir, cpu_count, system
from pathos.multiprocessing import ProcessPool as Pool
from tqdm import tqdm
from subprocess import run, PIPE, STDOUT
from sys import exit
import argparse


def get_scans(filename):
    """ get the scan keys from file """
    with open(filename, 'r') as f:
        scan_keys = f.read().splitlines()
    return scan_keys


def segmentation(scan_key, scanner):
    """ separate cat12 segmentation of csf/gm/wm/wmh (value 1 to 4 in tpm) in parallel """
    tpm_file = f'/media/shengwei/BackupData/totalVol/{scanner}/cat12r1434/seg/{scan_key}-tpm'
    command = f'fslmaths {tpm_file} -uthr 1 {scan_key}-csf -odt char;' \
              f'fslmaths {tpm_file} -uthr 2 -thr 2 -bin {scan_key}-gm -odt char;' \
              f'fslmaths {tpm_file} -thr 3 -bin {scan_key}-wm -odt char'
    result = run(command, stdout=PIPE, stderr=STDOUT, check=True, shell=True)
    if result.stdout.decode('utf-8') != '':
        with open(f'{scan_key}.log', 'wb') as logfile:
            logfile.write(result.stdout)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scanner', dest='scanner', action='store', nargs=1, default=None,
        help='Run total volume calculation for specific scanner (mg or uc)')
    args = parser.parse_args()
    scanner = args.scanner[0]

    scan_keys = get_scans('subjs-proc')
    if len(scan_keys) != 0:
        scan_keys.sort()
        scanners = len(scan_keys) * [scanner]

        with Pool(cpu_count() - 2) as pool:
            for _ in tqdm(pool.imap(segmentation, scan_keys, scanners), total=len(scan_keys)):
                pass

        logs = [log for log in listdir('.') if '.log' in log]
        if len(logs) != 0:
            for log in logs:
                print(f'Check {log}')
        
        system('./getVols ' + scanner+ ';mv *.nii.gz ~/work/wmh+totalvolumes/totalVol/' + scanner)
    else:
        print('No scan detected. Exiting.')
        exit(0)

