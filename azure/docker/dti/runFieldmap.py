#!/home/shengwei/anaconda3/bin/python

from os import listdir, path, cpu_count
from pathos.multiprocessing import ProcessPool as Pool
from tqdm import tqdm
from subprocess import run, PIPE, STDOUT
from sys import exit
import datetime

def get_fieldmap(scan_key):
    """ run Dcm2NiiX-fieldmap script in parallel """
    result = run(f'./Dcm2NiiX-fieldmap {scan_key}',
                 stdout=PIPE,
                 stderr=STDOUT,
                 check=True,
                 shell=True)
    if result.stdout.decode('utf-8') != '':
        with open(f'{scan_key}.log', 'wb') as logfile:
            logfile.write(result.stdout)
    return


if __name__ == '__main__':
    scan_keys = [folder for folder in listdir('.') 
        if path.isdir(folder) and 
            (str(datetime.datetime.today().year)[-2:] in folder or 
             str(datetime.datetime.today().year-1)[-2:] in folder)]
    if len(scan_keys) != 0:
        scan_keys.sort()

        with Pool(cpu_count() - 2) as pool:
            for _ in tqdm(pool.imap(get_fieldmap, scan_keys), total=len(scan_keys)):
                pass

        logs = [log for log in listdir('.') if '.log' in log]
        if len(logs) != 0 :
            for log in logs:
                print(f'Check {log}')
    else:
        print('No scan detected. Exiting.')
        exit(0)
