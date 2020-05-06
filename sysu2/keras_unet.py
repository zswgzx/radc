import numpy as np
import os
import sys
import SimpleITK as sitk
from utils import get_scans, preprocess_one_channel, merge_train
from sklearn.model_selection import train_test_split
from keras_unet.utils import get_augmented
from keras_unet.models import custom_unet
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam
from keras_unet.metrics import iou, iou_thresholded
from keras_unet.losses import jaccard_distance

inputDir = '/home/szhang/wmhchallenge'
outputDir = '/home/szhang/wmhchallenge/sysu2'
scans = get_scans(os.path.join(inputDir, 'subjs'))
rows = 256
cols = 256
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

x_train, x_val, y_train, y_val = train_test_split(images, truths, test_size=0.5, random_state=0)
train_gen = get_augmented(
    x_train, y_train, batch_size=2,
    data_gen_args = dict(
        rotation_range=15.,
        width_shift_range=0.05,
        height_shift_range=0.05,
        shear_range=10,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='constant'
    ))

model = custom_unet(
    x_train[0].shape,
    use_batch_norm=False,
    num_classes=1,
    filters=64,
    dropout=0.2,
    output_activation='sigmoid'
)

model_filename = 'wmh-mg.h5'
callback_checkpoint = ModelCheckpoint(
    model_filename,
    verbose=1,
    monitor='val_loss',
    save_best_only=True,
)

model.compile(
    optimizer=Adam(lr=2e-4),
    loss='jaccard_distance',
    metrics=[dice_coef]
)

history = model.fit_generator(
    train_gen,
    steps_per_epoch=100,
    epochs=50,
    
    validation_data=(x_val, y_val),
    callbacks=[callback_checkpoint]
)

