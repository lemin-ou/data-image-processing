#!/usr/bin/env python3

from pathlib import Path
from sys import argv
import sys
import traceback
import load_env
from processimage import main as imageprocessor
import csv
from random import randint
import glob
from shutil import copy, move, rmtree
from os import EX_SOFTWARE, getenv, path, listdir, mkdir
from data_preperation import get_data, convert_to_csv, load_config
from logs import logger
TO_GENERATE = 3


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
            logger.info('directory {} contains {} files'.format(
                dir, len(dir_files)))
            for _ in range(0, to_generate):
                start = randint(0, len(dir_files) - 1)
                end = randint(0, len(dir_files) - 1)
                while(start >= end):
                    start = randint(0, len(dir_files) - 1)
                    end = randint(0, len(dir_files) - 1)
                logger.info(
                    'random slicing start = {} , end = {}'.format(start, end))
                copy(
                    path.join(dir, dir_files[start:end][randint(0, end - start - 1)]), get_sample_dir(batch))


def get_batches(batches_path=__file__):
    file_dir = path.dirname(path.abspath(batches_path))
    batches_path = "{}/lot_*".format(path.join(file_dir, '..'))
    logger.info('batches path = %s' % batches_path)
    batches = glob.glob(batches_path)
    logger.info('detected batches = %s ' % batches)
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
                        post_processor((final, score, image_path, dir))
            delete_temp(batch)


def create_dir(parent, dir):
    """ create and return a directory if doesn't exist """
    directory = path.join(parent, dir)
    if not path.exists(directory):
        mkdir(directory)
    logger.info('create_dir: created directory %s ' % directory)
    return directory


def check_score(output):
    final, score, imagePath, parent = output
    pathRef = Path(imagePath)
    fileFullName = pathRef.name.split(".")
    extension = fileFullName.pop()

    threshold = getenv('IMAGE_%s_THRESHOLD' % extension.upper()) or 60
    logger.info("check_score: detecting threshold ... extension = %s, threshold = %s " % (
        extension, threshold))
    saveIn = path.join(pathRef.parent, "{}.{}".format(
        ".".join(fileFullName), extension))
    imageprocessor.save_image((final, score, saveIn), int(threshold))


def append_score():
    isNotLocal = getenv("ENV") != 'localhost'
    config = load_config()
    batches = [config.get("imagespath")] if isNotLocal else get_batches()
    for batch in batches:
        temp = create_dir(batch, '.tmp')
        dataFile = config.get(
            "csvpath") if isNotLocal else path.join(batch, "data.csv")
        fileName = dataFile.split("/").pop()
        try:
            out_file = open(path.join(temp, fileName), 'w')
            with open(dataFile, 'r') as input:
                reader = csv.DictReader(input, delimiter='@')
                header = reader.fieldnames
                header.append('Score')

                writer = csv.DictWriter(out_file, fieldnames=header)
                writer.writeheader()
                i = 0
                for row in reader:
                    if i == 0:
                        logger.info('row sample -> %s ' % row)
                        i += 1
                    impath = row["Photo"].strip("/")
                    (final, score, image_path) = imageprocessor.apply_processors(
                        path.join(batch, impath))
                    row["Score"] = score or 'Unknown'
                    writer.writerow(row)
                    check_score((final, score, image_path, batch))
                out_file.close()
                move(path.join(temp, fileName),
                     path.join(batch, fileName))
            delete_temp(batch)
        except Exception as e:
            logger.error("error while apply score -> %s " % e)
            out_file.close()
            raise e
        # randomize_sample_images(to_generate)
# process_batch_sample(lambda x: [get_sample_dir(x)],
#                      lambda dir: (
#     empty_dir(create_dir(dir, 'output')),
#     empty_dir(create_dir(dir, 'rejected'))
# ), lambda output: check_score(output))


steps = {
    1: {"name": 'Download and Extract data from S3', "handler": get_data},

    2: {"name": 'Convert xlsx file to csv', "handler": convert_to_csv},
    3: {"name": 'Process Images in each sub-batch', "handler": append_score},
    # 3: {"name": 'Convert xlsx file to csv', "handler": convert_to_csv},
}


try:
    step = int(argv[1])
    if step > len(steps.keys()) or step <= 0:
        raise Exception()
except Exception as e:
    logger.error("Can't identify step ")
    traceback.print_tb(e.__traceback__)
    sys.exit(-1)
try:

    if step == 1:
        logger.info("Begin executing orchestrator ....")

    print("\n" + "*" * 100 + "\n")
    logger.info("Begin Executing STEP {}: {} ....".format(
        step, steps[step]["name"]))
    print("\n")
    steps[step]["handler"]()
    print("\n")
    logger.info("STEP {}: Successfully handled.".format(step))
    print("\n" + "*" * 100 + "\n")
    print("\n")

    if len(steps.keys()) == step:
        logger.info("All Steps Has been executed, exit ....")

except Exception as e:
    logger.error("Error in orchestrator, can't handle STEP %s" % step)
    traceback.print_tb(e.__traceback__)
    sys.exit(EX_SOFTWARE)


# append_score()
