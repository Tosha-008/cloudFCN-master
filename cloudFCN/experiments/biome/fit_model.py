from tensorflow.keras.models import Model, load_model
from tensorflow.keras.callbacks import ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.optimizers import Adagrad, SGD, Adadelta

import json
import sys
import os

# sys.path.append('/Users/tosha_008/PycharmProjects/cloudFCN-master')
project_path = "/content/cloudFCN-master"
sys.path.append(project_path)

# OUR STUFF
from cloudFCN.data import loader, transformations as trf
from cloudFCN.data.Datasets import LandsatDataset, train_valid_test
from cloudFCN import models, callbacks
from cloudFCN.experiments import custom_callbacks
from MFCNN import model_mfcnn_def

def fit_model(config):
    """
    Return trained keras model. Main training function for cloud detection. Parameters
    contained in config file.
    """
    io_opts = config['io_options']
    model_load_path = io_opts['model_load_path']
    model_save_path = io_opts['model_save_path']
    model_checkpoint_dir = io_opts['model_checkpoint_dir']
    model_name = io_opts['model_name']

    if model_checkpoint_dir is not None:
        chkpnt_path = os.path.join(
            model_checkpoint_dir, 'weights.{epoch:02d}-{val_loss:.2f}.hdf5')

    num_classes = config['model_options']['num_classes']
    bands = config['model_options']['bands']
    if bands is not None:
        num_channels = len(bands)
    else:
        num_channels = 12

    # train_path = io_opts['train_path']  # can be single or multiple directories
    # valid_paths = io_opts['valid_paths']
    # summary_valid_path = io_opts['summary_valid_path']
    data_path = io_opts['data_path']

    train_path, valid_paths, test_paths = train_valid_test(data_path)
    summary_valid_path = valid_paths

    summary_valid_percent = io_opts['summary_valid_percent']

    fit_opts = config['fit_options']
    batch_size = fit_opts['batch_size']
    patch_size = fit_opts['patch_size']
    epochs = fit_opts['epochs']
    steps_per_epoch = fit_opts['steps_per_epoch']

    train_set = LandsatDataset(train_path)
    train_loader = loader.dataloader(
        train_set, batch_size, patch_size,
        transformations=[trf.train_base(patch_size),
                         trf.band_select(bands),
                         trf.class_merge(3, 4),
                         trf.class_merge(1, 2),
                         trf.sometimes(0.1, trf.bandwise_salt_and_pepper(
                             0.001, 0.001, pepp_value=-3, salt_value=3)),
                         trf.sometimes(0.2, trf.salt_and_pepper(
                             0.003, 0.003, pepp_value=-3, salt_value=3)),
                         trf.sometimes(0.2, trf.salt_and_pepper(
                             0.003, 0.003, pepp_value=-4, salt_value=4)),
                         trf.sometimes(0.2, trf.salt_and_pepper(
                             0.003, 0.003, pepp_value=-5, salt_value=5)),
                         trf.sometimes(0.5, trf.intensity_scale(0.9, 1.1)),
                         trf.sometimes(0.5, trf.intensity_shift(-0.05, 0.05)),
                         trf.sometimes(0.5, trf.chromatic_scale(0.90, 1.1)),
                         trf.sometimes(0.5, trf.chromatic_shift(-0.05, 0.05)),
                         trf.sometimes(0.8, trf.white_noise(0.2)),
                         trf.sometimes(0.2, trf.quantize(2**5)),
                         trf.sometimes(0.1, trf.white_noise(0.8))
                         ],
        shuffle=True,
        num_classes=num_classes,
        num_channels=num_channels)
    foga_valid_sets = [LandsatDataset(valid_path)
                       for valid_path in valid_paths]
    foga_valid_loaders = [
        loader.dataloader(
            valid_set, batch_size, patch_size,
            transformations=[trf.train_base(patch_size,fixed=True),
                             trf.band_select(bands),
                             trf.class_merge(3, 4),
                             trf.class_merge(1, 2)
                             ],
            shuffle=False,
            num_classes=num_classes,
            num_channels=num_channels) for valid_set in foga_valid_sets]
    summary_valid_set = LandsatDataset(summary_valid_path)
    summary_valid_set.randomly_reduce(summary_valid_percent)
    summary_batch_size = 12
    summary_steps = len(summary_valid_set)//summary_batch_size
    summary_valid_loader = loader.dataloader(
        summary_valid_set, summary_batch_size, patch_size,
        transformations=[trf.train_base(patch_size,fixed=True),
                         trf.band_select(bands),
                         trf.class_merge(3, 4),
                         trf.class_merge(1, 2)
                         ],
        shuffle=False,
        num_classes=num_classes,
        num_channels=num_channels)

    if model_load_path:
        model = load_model(model_load_path)
    elif model_name == "cloudfcn":
        model = models.build_model5(
            batch_norm=True, num_channels=num_channels, num_classes=num_classes)
        optimizer = Adadelta()

        model.compile(loss='categorical_crossentropy', metrics=['categorical_accuracy'],
                      optimizer=optimizer)
        model.summary()
    elif model_name == "mfcnn":
        model = model_mfcnn_def.build_model_mfcnn(
            num_channels=num_channels, num_classes=num_classes)
        optimizer = Adadelta()

        model.compile(loss='categorical_crossentropy', metrics=['categorical_accuracy'],
                      optimizer=optimizer)
        model.summary()

    train_gen = train_loader()
    summary_valid_gen = summary_valid_loader()
    foga_valid_gens = [foga_valid_loader()
                       for foga_valid_loader in foga_valid_loaders]
    callback_list = [custom_callbacks.foga_table5_Callback_no_thin(
                         foga_valid_sets, foga_valid_gens, frequency=1)

                     ]
    if model_checkpoint_dir is not None:
        callback_list.append(ModelCheckpoint(chkpnt_path, monitor='val_loss', verbose=0,
                                         save_best_only=False, save_weights_only=False, mode='auto', period=1))
    history = model.fit(
        train_gen,
        validation_data=summary_valid_gen,
        validation_steps=summary_steps,
        steps_per_epoch=steps_per_epoch,
        epochs=epochs,
        verbose=1,
        callbacks=callback_list
    )
    with open('training_history.json', 'w') as f:
        json.dump(history.history, f)

    model.save(model_save_path)
    return model


if __name__ == "__main__":
    config_path = sys.argv[1]  # TAKE COMMAND LINE ARGUMENT
    with open(config_path, 'r') as f:
        config = json.load(f)
    model = fit_model(config)
