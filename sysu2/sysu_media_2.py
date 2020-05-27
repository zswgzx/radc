from __future__ import print_function
import os
import numpy as np
import tensorflow as tf
import SimpleITK as sitk
import scipy.spatial
from keras.models import Model
from keras.layers import Input, merge, Convolution2D, MaxPooling2D, UpSampling2D, Cropping2D, ZeroPadding2D
from keras.optimizers import Adam
from keras import backend as K


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

def get_unet(img_shape = None):

        dim_ordering = 'tf'
        
        inputs = Input(shape = img_shape)
        concat_axis = -1
            
        conv1 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering, name='conv1_1')(inputs)
        conv1 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv1)
        conv1 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv1)
        conv1 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv1)
        conv1 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv1)
        pool1 = MaxPooling2D(pool_size=(2, 2), dim_ordering=dim_ordering)(conv1)
        conv2 = Convolution2D(96, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(pool1)
        conv2 = Convolution2D(96, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv2)
        pool2 = MaxPooling2D(pool_size=(2, 2), dim_ordering=dim_ordering)(conv2)

        conv3 = Convolution2D(128, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(pool2)
        conv3 = Convolution2D(128, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv3)
        pool3 = MaxPooling2D(pool_size=(2, 2), dim_ordering=dim_ordering)(conv3)

        conv4 = Convolution2D(256, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(pool3)
        conv4 = Convolution2D(256, 4, 4, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv4)
        pool4 = MaxPooling2D(pool_size=(2, 2), dim_ordering=dim_ordering)(conv4)

        conv5 = Convolution2D(416, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(pool4)
        conv5 = Convolution2D(416, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv5)

        up_conv5 = UpSampling2D(size=(2, 2), dim_ordering=dim_ordering)(conv5)
        ch, cw = get_crop_shape(conv4, up_conv5)
        crop_conv4 = Cropping2D(cropping=(ch,cw), dim_ordering=dim_ordering)(conv4)
        up6 = merge([up_conv5, crop_conv4], mode='concat', concat_axis=concat_axis)
        conv6 = Convolution2D(256, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(up6)
        conv6 = Convolution2D(256, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv6)

        up_conv6 = UpSampling2D(size=(2, 2), dim_ordering=dim_ordering)(conv6)
        ch, cw = get_crop_shape(conv3, up_conv6)
        crop_conv3 = Cropping2D(cropping=(ch,cw), dim_ordering=dim_ordering)(conv3)
        up7 = merge([up_conv6, crop_conv3], mode='concat', concat_axis=concat_axis)
        conv7 = Convolution2D(128, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(up7)
        conv7 = Convolution2D(128, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv7)

        up_conv7 = UpSampling2D(size=(2, 2), dim_ordering=dim_ordering)(conv7)
        ch, cw = get_crop_shape(conv2, up_conv7)
        crop_conv2 = Cropping2D(cropping=(ch,cw), dim_ordering=dim_ordering)(conv2)
        up8 = merge([up_conv7, crop_conv2], mode='concat', concat_axis=concat_axis)
        conv8 = Convolution2D(96, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(up8)
        conv8 = Convolution2D(96, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv8)

        up_conv8 = UpSampling2D(size=(2, 2), dim_ordering=dim_ordering)(conv8)
        ch, cw = get_crop_shape(conv1, up_conv8)
        crop_conv1 = Cropping2D(cropping=(ch,cw), dim_ordering=dim_ordering)(conv1)
        up9 = merge([up_conv8, crop_conv1], mode='concat', concat_axis=concat_axis)
        conv9 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(up9)
        conv9 = Convolution2D(64, 3, 3, activation='relu', border_mode='same', dim_ordering=dim_ordering)(conv9)

        ch, cw = get_crop_shape(inputs, conv9)
        conv9 = ZeroPadding2D(padding=(ch, cw), dim_ordering=dim_ordering)(conv9)
        conv10 = Convolution2D(1, 1, 1, activation='sigmoid', dim_ordering=dim_ordering)(conv9)
        model = Model(input=inputs, output=conv10)
        model.compile(optimizer=Adam(lr=(1e-4)*2), loss=dice_coef_loss, metrics=[dice_coef_for_training])

        return model

#--------------------------------------------------------------------------------------
def preprocessing(FLAIR_image, T1_image, mask_image):
    
    channel_num = 2
    num_selected_slice = np.shape(FLAIR_image)[0]
    image_rows_Dataset = np.shape(FLAIR_image)[1]
    image_cols_Dataset = np.shape(FLAIR_image)[2]
    T1_image = np.float32(T1_image)
    
    imgs_two_channels = np.ndarray((num_selected_slice, rows_standard, cols_standard, channel_num), dtype=np.float32)
    FLAIR_image_suitable = np.ndarray((num_selected_slice, rows_standard, cols_standard), dtype=np.float32)
    T1_image_suitable = np.ndarray((num_selected_slice, rows_standard, cols_standard), dtype=np.float32)
  
    # FLAIR --------------------------------------------

    #------Gaussion Normalization
    FLAIR_image -=np.mean(FLAIR_image[mask_image == 1])      #Gaussion Normalization
    FLAIR_image /=np.std(FLAIR_image[mask_image == 1])
    FLAIR_image_suitable[...] = np.min(FLAIR_image)
  
    if image_rows_Dataset<rows_standard and image_cols_Dataset>=cols_standard:
        FLAIR_image_suitable[:, int(rows_standard/2-image_rows_Dataset/2):int(rows_standard/2+image_rows_Dataset/2), :] = FLAIR_image[:, :, int(image_cols_Dataset/2-cols_standard/2):int(image_cols_Dataset/2+cols_standard/2)]
    elif image_rows_Dataset>=rows_standard and image_cols_Dataset<cols_standard:
        FLAIR_image_suitable[:, : ,int(cols_standard/2-image_cols_Dataset/2):int(image_cols_Dataset/2+cols_standard/2)] = FLAIR_image[:, int(image_rows_Dataset/2-rows_standard/2):int(rows_standard/2+image_rows_Dataset/2), :]
    elif image_rows_Dataset<rows_standard and image_cols_Dataset<cols_standard:
        FLAIR_image_suitable[:, int(rows_standard/2-image_rows_Dataset/2):int(rows_standard/2+image_rows_Dataset/2) ,int(cols_standard/2-image_cols_Dataset/2):int(image_cols_Dataset/2+cols_standard/2)] = FLAIR_image[:, :, :]
    else: 
        FLAIR_image_suitable[...] = FLAIR_image[:, int(image_rows_Dataset/2-rows_standard/2):(image_rows_Dataset/2+rows_standard/2), int(image_cols_Dataset/2-cols_standard/2):int(image_cols_Dataset/2+cols_standard/2)]
  
    # T1 -----------------------------------------------
    #------Gaussion Normalization
    T1_image -=np.mean(T1_image[mask_image == 1])      #Gaussion Normalization
    T1_image /=np.std(T1_image[mask_image == 1])
    T1_image_suitable[...] = np.min(T1_image)
  
    if image_rows_Dataset<rows_standard and image_cols_Dataset>=cols_standard:
        T1_image_suitable[:, int(rows_standard/2-image_rows_Dataset/2):int(rows_standard/2+image_rows_Dataset/2), :] = T1_image[:, :, int(image_cols_Dataset/2-cols_standard/2):int(image_cols_Dataset/2+cols_standard/2)]
    elif image_rows_Dataset>=rows_standard and image_cols_Dataset<cols_standard:
        T1_image_suitable[:, : ,int(cols_standard/2-image_cols_Dataset/2):int(image_cols_Dataset/2+cols_standard/2)] = T1_image[:, int(image_rows_Dataset/2-rows_standard/2):int(rows_standard/2+image_rows_Dataset/2), :]
    elif image_rows_Dataset<rows_standard and image_cols_Dataset<cols_standard:
        T1_image_suitable[:, int(rows_standard/2-image_rows_Dataset/2):int(rows_standard/2+image_rows_Dataset/2) ,int(cols_standard/2-image_cols_Dataset/2):int(image_cols_Dataset/2+cols_standard/2)] = T1_image[:, :, :]
    else: 
        T1_image_suitable[...] = T1_image[:, (image_rows_Dataset/2-rows_standard/2):(image_rows_Dataset/2+rows_standard/2), (image_cols_Dataset/2-cols_standard/2):(image_cols_Dataset/2+cols_standard/2)]

    #---------------------------------------------------
    FLAIR_image_suitable  = FLAIR_image_suitable[..., np.newaxis]
    T1_image_suitable  = T1_image_suitable[..., np.newaxis]
    imgs_two_channels = np.concatenate((FLAIR_image_suitable, T1_image_suitable), axis = 3)
    
    return imgs_two_channels

#----------------------------------------------------
def postprocessing(FLAIR_array, pred):
    
    num_selected_slice = np.shape(FLAIR_array)[0]
    start_slice = int(float(num_selected_slice)/float(8))
    image_rows_Dataset = np.shape(FLAIR_array)[1]
    image_cols_Dataset = np.shape(FLAIR_array)[2]
    original_pred = np.ndarray(np.shape(FLAIR_array), dtype=np.float32)
    if image_rows_Dataset<rows_standard and image_cols_Dataset>=cols_standard:
        original_pred[:, :, (image_cols_Dataset-cols_standard)/2:(cols_standard+image_cols_Dataset)/2] = pred[:, int(rows_standard/2-image_rows_Dataset/2):int(image_rows_Dataset/2+rows_standard/2), :,0] 
    elif image_rows_Dataset>=rows_standard and image_cols_Dataset<cols_standard:
        original_pred[:, int(image_rows_Dataset/2-rows_standard/2):int(image_rows_Dataset/2+rows_standard/2), : ] = pred[:, :, (cols_standard-image_cols_Dataset)/2:(cols_standard+image_cols_Dataset)/2,0]
    elif image_rows_Dataset<rows_standard and image_cols_Dataset<cols_standard:
        original_pred[:, :, : ] = pred[:, int(rows_standard/2-image_rows_Dataset/2):int(image_rows_Dataset/2+rows_standard/2), (cols_standard-image_cols_Dataset)/2:(cols_standard+image_cols_Dataset)/2,0]
    else:
        original_pred[:, int(image_rows_Dataset/2-rows_standard/2):int(image_rows_Dataset/2+rows_standard/2), (image_cols_Dataset-cols_standard)/2:(cols_standard+image_cols_Dataset)/2] = pred[:,:,:,0]
    original_pred[0:start_slice, :, :] = 0
    original_pred[(num_selected_slice-start_slice-1):(num_selected_slice-1), :, :] = 0
    
    return original_pred

#Read data----------------------------------------------------------------------------
inputDir = '/input'
outputDir = '/output'

FLAIR_image = sitk.ReadImage(os.path.join(inputDir, 'pre', 'FLAIR.nii.gz'))
T1_image = sitk.ReadImage(os.path.join(inputDir, 'pre', 'T1.nii.gz'))
mask_image = sitk.ReadImage(os.path.join(inputDir, 'pre', 'bm.nii.gz')

FLAIR_array = np.float64(sitk.GetArrayFromImage(FLAIR_image))
T1_array = np.float64(sitk.GetArrayFromImage(T1_image))
mask_array = np.float64(sitk.GetArrayFromImage(mask_image))

#Process data-------------------------------------------------------------------------
rows_standard = 200
cols_standard = 200
para_FLAIR = np.ndarray((1,3), dtype=np.float32)
para_FLAIR_ = FLAIR_image.GetSpacing()
para_FLAIR[0,0] = round(para_FLAIR_[0],3)   # get parameter of the data
para_FLAIR[0,1] = round(para_FLAIR_[1],3)  
para_FLAIR[0,2] = round(para_FLAIR_[2],3) 

print(para_FLAIR)
#print(round(para_FLAIR[...], 3))
imgs_test = Others_preprocessing(FLAIR_array, T1_array, mask_array)
#Load model-------------------------------------------------------------------------------
img_shape=(rows_standard, cols_standard, 2)
model = get_unet(img_shape)
model.load_weights('/wmhseg_example/0.h5')
pred = model.predict(imgs_test, batch_size=5, verbose=1)
model.load_weights('/wmhseg_example/1.h5')
pred_1 = model.predict(imgs_test, batch_size=5, verbose=1)
model.load_weights('/wmhseg_example/2.h5')
pred_2 = model.predict(imgs_test, batch_size=5, verbose=1)
model.load_weights('/wmhseg_example/3.h5')
pred_3 = model.predict(imgs_test, batch_size=5, verbose=1)
pred[...] = (pred[...]+pred_1[...]+pred_2[...]+pred_3[...])/4
pred[pred[...,0] > 0.45] = 1      #thresholding 
pred[pred[...,0] <= 0.45] = 0
print(np.shape(pred))

#Postprocessing
original_pred = Others_postprocessing(FLAIR_array, pred)

filename_resultImage = os.path.join(outputDir,'result.nii.gz')
sitk.WriteImage(sitk.GetImageFromArray(original_pred), filename_resultImage)
