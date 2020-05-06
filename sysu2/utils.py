from __future__ import print_function
import numpy as np


def gaussian_norm_image(image):
    image[image != 0.] -= np.mean(image[image != 0.])
    image[image != 0.] /= np.std(image[image != 0.])
    return image


def preprocess_one_channel(image, rows, cols):
    image_slices = np.shape(image)[0]
    image_rows_raw = np.shape(image)[1]
    image_cols_raw = np.shape(image)[2]
    image_resized = np.ndarray((image_slices, rows, cols), dtype=np.float32)

    image = gaussian_norm_image(image)
    image_resized[...] = image[:, int((image_rows_raw - rows)/2):int((image_rows_raw + rows)/2),
                               int((image_cols_raw - cols)/2):int((image_cols_raw + cols)/2)]
    return image_resized


def preprocess_multi_channels(flair_image, t1_image, rows, cols):
    channel_num = 2
    flair_image_resized = preprocess_one_channel(flair_image, rows, cols)
    t1_image_resized = preprocess_one_channel(t1_image, rows, cols)
    images_multi_channels = np.ndarray((np.shape(flair_image)[0], rows, cols, channel_num), dtype=np.float32)

    images_multi_channels[...] = np.concatenate((flair_image_resized[..., np.newaxis],
                                                t1_image_resized[..., np.newaxis]), axis=3)
    return images_multi_channels


def postprocess(flair_raw, pred, rows, cols):
    image_rows_raw = np.shape(flair_raw)[1]
    image_cols_raw = np.shape(flair_raw)[2]
    pred_resized = np.zeros(flair_raw.shape, dtype=np.uint8)

    pred_resized[:, int((image_rows_raw - rows)/2):int((image_rows_raw + rows)/2),
                 int((image_cols_raw - cols)/2):int((cols + image_cols_raw)/2)] = pred[:, :, :, 0].astype(int)
    return pred_resized


def merge_train(flair, t1, truth, images, truths, i, slices):
    images[i*slices:(i+1)*slices, ..., 0] = flair
    images[i*slices:(i+1)*slices, ..., 1] = t1
    truths[i*slices:(i+1)*slices, ...] = truth
    return images, truths


def get_scans(filename):
    """ get scan keys from file """
    with open(filename, 'r') as f:
        scan_keys = f.read().splitlines()
    return scan_keys
