mkdir /bidsformat/sub-1
mkdir /bidsformat/sub-1/anat
mv /data/input*.nii /bidsformat/sub-1/anat/sub-1_T1w.nii
mv /data/input*.json /bidsformat/sub-1/anat/sub-1_T1w.json

/usr/local/miniconda/bin/mriqc /bidsformat /out participant --participant_label 1 -m T1w --nprocs 2 --ants-nthreads 2 --no-sub --ica --fft-spikes-detector

mv /tmp/work/workflow_enumerator/anatMRIQCT1w /out
mv /out/sub-1/anat/* /out
rm -r /out/sub-1 /out/anatMRIQCT1w/SpatialNormalization 

find /out -type f -name '_*' -delete
find /out -name '*.html' -delete
find /out -name '*.rst' -delete
find /out -name '*.pklz' -delete
find /out -type d -empty -delete

tar cfz /out/anatMRIQCT1w.tgz /out/anatMRIQCT1w
rm -rf /out/anatMRIQCT1w
