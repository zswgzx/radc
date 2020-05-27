import os
import sys
import shutil
from glob import glob
import logging
import nibabel as nib
import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

import monai
from monai.transforms import \
    AddChanneld, Compose, LoadNiftid, ScaleIntensityd, RandCropByPosNegLabeld, RandZoomd, RandFlipd, ToTensord
from monai.data import list_data_collate, sliding_window_inference
from monai.metrics import compute_meandice
from monai.visualize import plot_2d_or_3d_image

def main():
    monai.config.print_config()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    datadir = '../data/'

    images = sorted(glob(os.path.join(datadir, 'train/images/*.nii.gz')))
    segs = sorted(glob(os.path.join(datadir, 'train/labels/*.nii.gz')))
    train_files = [{'img': img, 'seg': seg} for img, seg in zip(images, segs)]

    images = sorted(glob(os.path.join(datadir, 'val/images/*.nii.gz')))
    segs = sorted(glob(os.path.join(datadir, 'val/labels/*.nii.gz')))
    val_files = [{'img': img, 'seg': seg} for img, seg in zip(images, segs)]

    # define transforms for image and segmentation
    train_transforms = Compose([
        LoadNiftid(keys=['img', 'seg']),
        AddChanneld(keys=['img', 'seg']),
        ScaleIntensityd(keys=['img', 'seg']),
        RandCropByPosNegLabeld(keys=['img', 'seg'], label_key='seg', size=[32, 32, 32], pos=1, neg=1, num_samples=4),
        RandZoomd(keys=['img', 'seg'], keep_size=True),
        RandFlipd(keys=['img', 'seg'], spatial_axis=2),
        ToTensord(keys=['img', 'seg'])
    ])
    val_transforms = Compose([
        LoadNiftid(keys=['img', 'seg']),
        AddChanneld(keys=['img', 'seg']),
        ScaleIntensityd(keys=['img', 'seg']),
        ToTensord(keys=['img', 'seg'])
    ])

    # define dataset, data loader
    check_ds = monai.data.Dataset(data=train_files, transform=train_transforms)
    # use batch_size=2 to load images and use RandCropByPosNegLabeld to generate 2 x 4 images for network training
    check_loader = DataLoader(check_ds, batch_size=2, num_workers=4, collate_fn=list_data_collate,
                              pin_memory=torch.cuda.is_available())
    check_data = monai.utils.misc.first(check_loader)
    print(check_data['img'].shape, check_data['seg'].shape)

    # create a training data loader
    train_ds = monai.data.Dataset(data=train_files, transform=train_transforms)
    # use batch_size=2 to load images and use RandCropByPosNegLabeld to generate 2 x 4 images for network training
    train_loader = DataLoader(train_ds, batch_size=2, shuffle=True, num_workers=4,
                              collate_fn=list_data_collate, pin_memory=torch.cuda.is_available())
    # create a validation data loader
    val_ds = monai.data.Dataset(data=val_files, transform=val_transforms)
    val_loader = DataLoader(val_ds, batch_size=1, num_workers=4, collate_fn=list_data_collate,
                            pin_memory=torch.cuda.is_available())

    # create UNet, DiceLoss and Adam optimizer
    device = torch.device('cuda:0')
    model = monai.networks.nets.UNet(
        dimensions=3,
        in_channels=1,
        out_channels=1,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2),
        num_res_units=2,
    ).to(device)
    loss_function = monai.losses.DiceLoss(do_sigmoid=True)
    optimizer = torch.optim.Adam(model.parameters(), 1e-3)

    # start a typical PyTorch training
    val_interval = 2
    best_metric = -1
    best_metric_epoch = -1
    epoch_loss_values = list()
    metric_values = list()
    writer = SummaryWriter()
    iterations = 500
    for epoch in range(iterations):
        print('-' * 10)
        print('epoch {}/{}'.format(epoch + 1, iterations))
        model.train()
        epoch_loss = 0
        step = 0
        for batch_data in train_loader:
            step += 1
            inputs, labels = batch_data['img'].to(device), batch_data['seg'].to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = loss_function(outputs, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            epoch_len = len(train_ds) // train_loader.batch_size
            print('{}/{}, train_loss: {:.4f}'.format(step, epoch_len, loss.item()))
            writer.add_scalar('train_loss', loss.item(), epoch_len * epoch + step)
        epoch_loss /= step
        epoch_loss_values.append(epoch_loss)
        print('epoch {} average loss: {:.4f}'.format(epoch + 1, epoch_loss))

        if (epoch + 1) % val_interval == 0:
            model.eval()
            with torch.no_grad():
                metric_sum = 0.
                metric_count = 0
                val_images = None
                val_labels = None
                val_outputs = None
                for val_data in val_loader:
                    val_images, val_labels = val_data['img'].to(device), val_data['seg'].to(device)
                    roi_size = (32, 32, 32)
                    sw_batch_size = 4
                    val_outputs = sliding_window_inference(val_images, roi_size, sw_batch_size, model)
                    value = compute_meandice(y_pred=val_outputs, y=val_labels, include_background=True,
                                             to_onehot_y=False, add_sigmoid=True)
                    metric_count += len(value)
                    metric_sum += value.sum().item()
                metric = metric_sum / metric_count
                metric_values.append(metric)
                if metric > best_metric:
                    best_metric = metric
                    best_metric_epoch = epoch + 1
                    torch.save(model.state_dict(), 'best_metric_model.pth')
                    print('saved new best metric model')
                print('current epoch: {} current mean dice: {:.4f} best mean dice: {:.4f} at epoch {}'.format(
                    epoch + 1, metric, best_metric, best_metric_epoch))
                writer.add_scalar('val_mean_dice', metric, epoch + 1)
                # plot the last model output as GIF image in TensorBoard with the corresponding image and label
                plot_2d_or_3d_image(val_images, epoch + 1, writer, index=0, tag='image')
                plot_2d_or_3d_image(val_labels, epoch + 1, writer, index=0, tag='label')
                plot_2d_or_3d_image(val_outputs, epoch + 1, writer, index=0, tag='output')
    print('train completed, best_metric: {:.4f} at epoch: {}'.format(best_metric, best_metric_epoch))
    writer.close()

if __name__ == '__main__':
    main()
