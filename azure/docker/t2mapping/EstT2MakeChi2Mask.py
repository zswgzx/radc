#!/home/shengwei/anaconda3/bin/python

from os import listdir, cpu_count, system, mkdir
from pathos.multiprocessing import ProcessPool as Pool
from tqdm import tqdm
from subprocess import run, PIPE, STDOUT


def t2_mapping(filename):
    """ perform t2 mapping processing """

    scan_key = filename.split('-')[0]
    mkdir(scan_key)
    command = 'mv {}-* {};' \
              'cd {};' \
              'fslsplit {}-5T2s echo -t;' \
              ''.format(scan_key, scan_key, scan_key, scan_key)
    for i in range(1,5):
        command += f'fslmaths echo{i:04} -add 0 echo{(i-1):04} -odt float;'
    command += 'gunzip echo0*;' \
               't2_map_mask_float 4 40 60 80 100;' \
               'gzip chi2.nii mask.nii t2vol.nii pdw.nii;' \
               'bet echo0000 brain -S;' \
               'fslmaths brain_mask -fillh26 brain_mask -odt char;' \
               'fslmaths t2vol -mas brain_mask -abs t2vol1;' \
               'fslmaths t2vol1 -thr 250 -bin mask250;' \
               'fslmaths brain_mask -sub mask250 -ero chi2mask -odt char;' \
               'rm echo0* brain.nii.gz brain_skull.nii.gz mask250.nii.gz t2vol1.nii.gz;' \
               'mv chi2.nii.gz ../../QA/chi2/{}-chi2.nii.gz;' \
               'mv mask.nii.gz ../../t2s/masks/{}-headmask.nii.gz;' \
               'mv t2vol.nii.gz ../../t2s/raw/{}-rawT2.nii.gz;' \
               'mv brain_mask.nii.gz ../../t2s/masks/{}-brainmask.nii.gz;' \
               'mv chi2mask.nii.gz ../../QA/chi2/{}-chi2mask.nii.gz;' \
               'mv pdw.nii.gz ../../pdw/raw/{}-rawPDw.nii.gz;' \
               'fslmaths ../../pdw/raw/{}-rawPDw -mas ../../t2s/masks/{}-headmask ../../pdw/{}-pdw;' \
               'fslmaths ../../t2s/raw/{}-rawT2 -mas ../../t2s/masks/{}-headmask -thr 0 ../../t2s/{}-t2;' \
               'mv *-5T2s.nii.gz ..;' \
               'cd ..;' \
               'rmdir {}' \
               ''.format(scan_key, scan_key, scan_key, scan_key, scan_key,
                         scan_key, scan_key, scan_key, scan_key, scan_key,
                         scan_key, scan_key, scan_key)

    result = run(command, stdout=PIPE, stderr=STDOUT, check=True, shell=True)
    if result.stdout.decode('utf-8') != '':
        with open(f'{scan_key}.log', 'wb') as logfile:
            logfile.write(result.stdout)
    return


if __name__ == '__main__':

    filenames = [nii for nii in listdir('.') if '.nii.gz' in nii]
    filenames.sort()

    with Pool(cpu_count() - 2) as pool:
        for _ in tqdm(pool.imap(t2_mapping, filenames), total=len(filenames)):
            pass
