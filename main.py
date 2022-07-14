#!/usr/bin/env python3

import csv
from random import randint
import subprocess
import glob
from shutil import copy, move, rmtree
from os import path, listdir, mkdir
from math import floor
from dotenv import load_dotenv
load_dotenv()

from getdata import get_data
from processimage import main as imageprocessor

def empty_dir(dir):
    rmtree(dir)  # empty a directory
    mkdir(dir)  # create a directory


def delete_temp(batch):
    rmtree(path.join(batch, '.tmp'))


def randomize_sample_images(to_generate):
    ''' feed the sample_image directory with random images
        from the batch images. '''

    for batch in get_batches():
        empty_dir(get_sample_dir(batch))
        for dir in glob.glob(path.join(batch, '0*')):
            dir_files = listdir(dir)
            print('directory {} contains {} files'.format(dir, len(dir_files)))
            for _ in range(0, to_generate):
                start = randint(0, len(dir_files) - 1)
                end = randint(0, len(dir_files) - 1)
                while(start >= end):
                    start = randint(0, len(dir_files) - 1)
                    end = randint(0, len(dir_files) - 1)
                print('random slicing start = {} , end = {}'.format(start, end))
                copy(
                    path.join(dir, dir_files[start:end][randint(0, end - start - 1)]), get_sample_dir(batch))


to_generate = 3


def get_batches(batches_path=__file__):
    file_dir = path.dirname(path.abspath(batches_path))
    batches_path = "{}/lot_*".format(path.join(file_dir, '..'))
    print('batches path', batches_path)
    batches = glob.glob(batches_path)
    print('detected batches', batches)
    return batches


def get_sample_dir(batch):
    return path.join(batch,  "sample_image")


def get_batch_output_dir(batch):
    return path.join(batch,  "output")


def get_batch_rejected_dir(batch):
    return path.join(batch, "rejected")


def get_batches_directories():
    directories = []
    for batch in get_batches():
        directories.extend(glob.glob(path.join(batch,  '0*')))
    return directories


def process_batch_sample(get_dirs, pre_processor, post_processor):
    for batch in get_batches():
        create_dir(batch, '.tmp')
        for dir in get_dirs(batch):
            pre_processor(dir)
            for image in listdir(dir):
                if path.isfile(path.join(dir, image)):
                    final, score, image_path = imageprocessor.apply_processors(
                        path.join(dir, image))
                    if type(score) == int:
                        post_processor((final, score, image_path))
            delete_temp(batch)


def create_dir(parent, dir):
    """ create and return a directory if doesn't exist """
    directory = path.join(parent, dir)
    if not path.exists(directory):
        mkdir(directory)
    print('create_dir: created directory', directory)
    return directory


def append_score():
    for batch in get_batches():
        create_dir(batch, '.tmp')
        out_file = open(path.join(batch, ".tmp/data.csv"), 'w')
        with open(path.join(batch, "data.csv"), 'r') as input:
            reader = csv.DictReader(input, delimiter=';')
            header = reader.fieldnames
            header.append('Score')

            writer = csv.DictWriter(out_file, fieldnames=header)
            writer.writeheader()
            i = 0
            for row in reader:
                if i == 0:
                    print('append_score: row sample -> ', row)
                    i += 1
                impath = row["Photo"].split('/')
                impath.pop(1)
                (final, score, image_path) = imageprocessor.apply_processors(
                    batch + "/".join(impath))
                row["Score"] = score
                writer.writerow(row)
            out_file.close()
            move(path.join(batch, ".tmp/data.csv"),
                 path.join(batch, "out_data.csv"))
        delete_temp(batch)

        # randomize_sample_images(to_generate)
# process_batch_sample(lambda x: [get_sample_dir(x)],
#                      lambda dir: (
#     empty_dir(create_dir(dir, 'output')),
#     empty_dir(create_dir(dir, 'rejected'))
# ), lambda output: imageprocessor.save_image(output))


try:
    get_data()
except Exception as e:
    print("Error in script, terminate instance")
    subprocess.run("shutdown now")
finally:
    subprocess.run("shutdown now")

# append_score()
