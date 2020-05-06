from __future__ import print_function
import os
import numpy as np
import SimpleITK as sitk
from model import train
from utils import get_scans, preprocess_one_channel, merge_train

inputDir = '/home/szhang/wmhchallenge'
outputDir = '/home/szhang/wmhchallenge/sysu2'
scans = get_scans(os.path.join(inputDir, 'subjs'))
rows = 200
cols = 200
slices = 35
channels = 2
os.environ['KERAS_BACKEND'] = 'tensorflow'
os.environ["CUDA_VISIBLE_DEVICES"] = '0'

images = np.ndarray((slices*len(scans), rows, cols, channels), dtype=np.float32)
truths = np.ndarray((slices*len(scans), rows, cols), dtype=np.float32)

for i, scan_key in enumerate(scans):
    # Read data
    flair_image = sitk.ReadImage(os.path.join(inputDir, '{}-flair-denoised.nii.gz'.format(scan_key)))
    t1_image = sitk.ReadImage(os.path.join(inputDir, '{}-T1.nii.gz'.format(scan_key)))
    truth_image = sitk.ReadImage(os.path.join(inputDir, '{}.nii.gz'.format(scan_key)))

    flair_array = np.float32(sitk.GetArrayFromImage(flair_image))
    t1_array = np.float32(sitk.GetArrayFromImage(t1_image))
    truth_array = np.float32(sitk.GetArrayFromImage(truth_image))

    # Process data
    flair_array = preprocess_one_channel(flair_array, rows, cols)
    t1_array = preprocess_one_channel(t1_array, rows, cols)
    truth_array = preprocess_one_channel(truth_array, rows, cols)

    # Merge data
    images, truths = merge_train(flair_array, t1_array, truth_array, images, truths, i, slices)

    # Postprocessing
    flair_array[...] = 0.
    t1_array[...] = 0.
    truth_array[...] = 0.

# train model
truths = truths[..., np.newaxis]
train(images, truths, outputDir, patient=4, verbose=True)
