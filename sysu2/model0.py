from __future__ import print_function
import os
import numpy as np
import tensorflow as tf
from keras.models import Model
from keras.layers import Input, merge, Conv2D, MaxPooling2D, UpSampling2D, Cropping2D, ZeroPadding2D, BatchNormalization, Activation
from keras.layers.merge import concatenate
from keras.optimizers import Adam
from keras import backend as K
from keras.preprocessing.image import apply_transform, transform_matrix_offset_center
K.set_image_data_format('channels_last')

# -define u-net architecture--------------------
smooth = 1.


def dice_coef_for_training(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def dice_coef_loss(y_true, y_pred):
    return -dice_coef_for_training(y_true, y_pred)


def get_crop_shape(target, refer):
    # width, the 3rd dimension
    cw = (target.get_shape()[2] - refer.get_shape()[2]).value
    assert (cw >= 0)
    if cw % 2 != 0:
        cw1, cw2 = int(cw/2), int(cw/2) + 1
    else:
        cw1, cw2 = int(cw/2), int(cw/2)
    # height, the 2nd dimension
    ch = (target.get_shape()[1] - refer.get_shape()[1]).value
    assert (ch >= 0)
    if ch % 2 != 0:
        ch1, ch2 = int(ch/2), int(ch/2) + 1
    else:
        ch1, ch2 = int(ch/2), int(ch/2)

    return (ch1, ch2), (cw1, cw2)


def conv_bn_relu(nd, k=3, inputs=None):
    conv = Conv2D(nd, k, padding='same')(inputs)  # kernel_initializer='he_normal'
    # bn = BatchNormalization()(conv)
    relu = Activation('relu')(conv)
    return relu


def get_unet(img_shape=None, first5=True):
    inputs = Input(shape=img_shape)
    concat_axis = -1

    if first5:
        filters = 5
    else:
        filters = 3

    conv1 = Conv2D(64, filters, activation='relu', padding='same', name='conv1_1')(inputs)
    conv1 = Conv2D(64, filters, activation='relu', padding='same')(conv1)
    conv1 = Conv2D(64, filters, activation='relu', padding='same')(conv1)
    conv1 = Conv2D(64, filters, activation='relu', padding='same')(conv1)
    conv1 = Conv2D(64, filters, activation='relu', padding='same')(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = Conv2D(96, 3, activation='relu', padding='same')(pool1)
    conv2 = Conv2D(96, 3, activation='relu', padding='same')(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = Conv2D(128, 3, activation='relu', padding='same')(pool2)
    conv3 = Conv2D(128, 3, activation='relu', padding='same')(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = Conv2D(256, 3, activation='relu', padding='same')(pool3)
    conv4 = Conv2D(256, 4, activation='relu', padding='same')(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = Conv2D(416, 3, activation='relu', padding='same')(pool4)
    conv5 = Conv2D(416, 3, activation='relu', padding='same')(conv5)

    up_conv5 = UpSampling2D(size=(2, 2))(conv5)
    ch, cw = get_crop_shape(conv4, up_conv5)
    crop_conv4 = Cropping2D(cropping=(ch, cw))(conv4)
    up6 = concatenate([up_conv5, crop_conv4], axis=concat_axis)
    conv6 = Conv2D(256, 3, activation='relu', padding='same')(up6)
    conv6 = Conv2D(256, 3, activation='relu', padding='same')(conv6)

    up_conv6 = UpSampling2D(size=(2, 2))(conv6)
    ch, cw = get_crop_shape(conv3, up_conv6)
    crop_conv3 = Cropping2D(cropping=(ch, cw))(conv3)
    up7 = concatenate([up_conv6, crop_conv3], axis=concat_axis)
    conv7 = Conv2D(128, 3, activation='relu', padding='same')(up7)
    conv7 = Conv2D(128, 3, activation='relu', padding='same')(conv7)

    up_conv7 = UpSampling2D(size=(2, 2))(conv7)
    ch, cw = get_crop_shape(conv2, up_conv7)
    crop_conv2 = Cropping2D(cropping=(ch, cw))(conv2)
    up8 = concatenate([up_conv7, crop_conv2], axis=concat_axis)
    conv8 = Conv2D(96, 3, activation='relu', padding='same')(up8)
    conv8 = Conv2D(96, 3, activation='relu', padding='same')(conv8)

    up_conv8 = UpSampling2D(size=(2, 2))(conv8)
    ch, cw = get_crop_shape(conv1, up_conv8)
    crop_conv1 = Cropping2D(cropping=(ch, cw))(conv1)
    up9 = concatenate([up_conv8, crop_conv1], axis=concat_axis)
    conv9 = Conv2D(64, 3, activation='relu', padding='same')(up9)
    conv9 = Conv2D(64, 3, activation='relu', padding='same')(conv9)

    ch, cw = get_crop_shape(inputs, conv9)
    conv9 = ZeroPadding2D(padding=(ch, cw))(conv9)
    conv10 = Conv2D(1, 1, activation='sigmoid', padding='same')(conv9)
    model = Model(inputs=inputs, outputs=conv10)
    model.compile(optimizer=Adam(lr=2e-4), loss=dice_coef_loss, metrics=[dice_coef_for_training])

    return model


def augment(x_0, x_1, y):
    theta = (np.random.uniform(-15, 15) * np.pi) / 180.
    rotation_matrix = np.array([[np.cos(theta), -np.sin(theta), 0],
                                [np.sin(theta), np.cos(theta), 0],
                                [0, 0, 1]])

    shear = np.random.uniform(-.1, .1)
    shear_matrix = np.array([[1, -np.sin(shear), 0],
                             [0, np.cos(shear), 0],
                             [0, 0, 1]])

    zx, zy = np.random.uniform(.9, 1.1, 2)
    zoom_matrix = np.array([[zx, 0, 0],
                            [0, zy, 0],
                            [0, 0, 1]])

    augmentation_matrix = np.dot(np.dot(rotation_matrix, shear_matrix), zoom_matrix)
    transform_matrix = transform_matrix_offset_center(augmentation_matrix, x_0.shape[0], x_0.shape[1])
    x_0 = apply_transform(x_0[..., np.newaxis], transform_matrix, channel_axis=2)
    x_1 = apply_transform(x_1[..., np.newaxis], transform_matrix, channel_axis=2)
    y = apply_transform(y[..., np.newaxis], transform_matrix, channel_axis=2)

    return x_0[..., 0], x_1[..., 0], y[..., 0]


def predict(imgs_2channels, rows, cols, weight_dir):
    img_shape = (rows, cols, 2)
    model = get_unet(img_shape, False)
    for i in range(4):
        model.load_weights(os.path.join(weight_dir, '{}.h5'.format(i)))
        pred = model.predict(imgs_2channels, batch_size=5, verbose=1)
        if i == 0: 
            pred0 = pred
        else:
            pred0 += pred

    pred0 /= 4
    return pred0


def train(images, masks, base_path, patient=0, verbose=False):
    # train single model on the training set
    samples_num = images.shape[0]
    row = images.shape[1]
    col = images.shape[2]
    channels = images.shape[3]
    epoch = 50
    batch_size = 30
    img_shape = (row, col, channels)

    model = get_unet(img_shape, True)
    current_epoch = 1
    while current_epoch <= epoch:
        print('Epoch {}/{}'.format(str(current_epoch), str(epoch)))
        images_aug = np.zeros(images.shape, dtype=np.float32)
        masks_aug = np.zeros(masks.shape, dtype=np.float32)

        for i in range(samples_num):
            images_aug[i, ..., 0], images_aug[i, ..., 1], masks_aug[i, ..., 0] = \
                augment(images[i, ..., 0], images[i, ..., 1], masks[i, ..., 0])
        image = np.concatenate((images, images_aug), axis=0)
        mask = np.concatenate((masks, masks_aug), axis=0)

        history = model.fit(image, mask, batch_size=batch_size, epochs=1, verbose=verbose, shuffle=True)
        current_epoch += 1

        if history.history['loss'][-1] > 0.99:
            model = get_unet(img_shape, True)
            current_epoch = 1

    model_path = base_path + '/full_2channels_aug_5/'

    if not os.path.exists(model_path):
        os.mkdir(model_path)

    model_path += str(patient) + '.h5'
    model.save_weights(model_path)
    print('Model saved to {}'.format(model_path))
