from __future__ import print_function
import os
import numpy as np
import SimpleITK as sitk
from model import predict
from utils import get_scans, preprocess_multi_channels, postprocess

inputDir = '/input/pre'
outputDir = '/output'
weightDir = '/wmhseg_example'
scans = get_scans(os.path.join(inputDir, 'subjs'))

rows = 200
cols = 200
wmh_threshold = .5

for scan_key in scans:
    # Read data
    FLAIR_image = sitk.ReadImage(os.path.join(inputDir, '{}-flair-denoised.nii.gz'.format(scan_key)))
    T1_image = sitk.ReadImage(os.path.join(inputDir, '{}-T1.nii.gz'.format(scan_key)))

    FLAIR_array = np.float32(sitk.GetArrayFromImage(FLAIR_image))
    T1_array = np.float32(sitk.GetArrayFromImage(T1_image))

    # Process data
    imgs_test = preprocess_multi_channels(FLAIR_array, T1_array, rows, cols)

    # Load model
    pred = predict(imgs_test, rows, cols, weightDir)
    pred[pred[..., 0] > wmh_threshold] = 1
    pred[pred[..., 0] <= wmh_threshold] = 0

    # Postprocessing
    original_pred = postprocess(FLAIR_array, pred, rows, cols)
    filename_resultImage = os.path.join(outputDir, '{}-sysu2.nii.gz'.format(scan_key))
    sitk.WriteImage(sitk.GetImageFromArray(original_pred), filename_resultImage)

    pred[...] = 0.
    FLAIR_array[...] = 0.
    T1_array[...] = 0.
