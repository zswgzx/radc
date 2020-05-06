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


def t2_fitting(scan_key, scanner):
    """ perform t2star fitting processing """

    command = 'mkdir {};cd {};' \
              'cp /home/shengwei/work/qsm/{}/{}/mag*.nii.gz .;' \
              ''.format(scan_key, scan_key, scanner, scan_key)

    if scanner == 'mg':
        command += 'fslorient -copyqform2sform mag;fslsplit mag echo;'
        for i in range(4):
            command += f'fslmaths echo{i:04} -add 0 echo{i:04} -odt float;'
    elif scanner == 'uc':
        command += 'fslsplit magni echo;'
    else:
        print('Type -h for usage, exiting...')
        exit(1)

    command += 'gunzip echo0*;' \
	       't2_map_mask_float 4 4.6 9.1 13.6 18.1;' \
               'fslmaths t2vol -mas ~/work/qsm/{}/{}/mask-hdbet-ero2 t2star;' \
               'fslmaths t2star -thr 0 -uthr 150 -bin tissue-mask -odt char;' \
               'fslmaths chi2 -mas tissue-mask chi2masked;' \
               'rm t2vol*nii chi2*nii mask*nii pdw*nii echo*nii mag*.nii.gz;' \
               'cd ..'.format(scanner, scan_key)

    result = run(command, stdout=PIPE, stderr=STDOUT, check=True, shell=True)
    if result.stdout.decode('utf-8') != '':
        with open(f'{scan_key}.log', 'wb') as logfile:
            logfile.write(result.stdout)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scanner', dest='scanner', action='store', nargs=1, default=None,
        help='Run qsm qc for specific scanner (mg or uc)')
    args = parser.parse_args()
    scanner = args.scanner[0]

    scan_keys = get_scans('/home/shengwei/work/qsm/{}/subjs'.format(scanner))
    scan_keys.sort()
    scanners = len(scan_keys) * [scanner]

    with Pool(cpu_count() - 2) as pool:
        for _ in tqdm(pool.imap(t2_fitting, scan_keys, scanners), total=len(scan_keys)):
            pass

    logs = [log for log in listdir('.') if '.log' in log]
    if len(logs) != 0:
        for log in logs:
            print(f'Check {log}')

    system('./t2star-fitting {}'.format(scanner))
