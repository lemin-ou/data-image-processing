#!/usr/bin/env python3

from pathlib import Path
from sys import argv
import sys
import traceback
from subprocess import call
from processimage import main as imageprocessor
import csv
from random import randint
import glob
from shutil import copy, move, rmtree
from os import EX_SOFTWARE, getenv, path, listdir
from data_preperation import compress_directories, get_data, convert_to_csv, move_image_to_root, move_rejected_files, put_data
from logs import logger
from utils import *
TO_GENERATE = 3


def randomize_sample_images(to_generate):
    ''' feed the sample_image directory with random images
        from the batch images. '''

    root = get_root()
    empty_dir(get_sample_dir(root))
    for dir in glob.glob(path.join(root, '01', "0*")):
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
                path.join(dir, dir_files[start:end][randint(0, end - start - 1)]), get_sample_dir(root))


def process_batch_sample(dirs, pre_processor, post_processor):
    create_dir(get_root(), '.tmp')
    for dir in dirs:
        pre_processor(dir)
        for image in listdir(dir):
            if path.isfile(path.join(dir, image)):
                final, score, image_path = imageprocessor.apply_processors(
                    path.join(dir, image), get_root())
                if type(score) == int:
                    post_processor((final, score, image_path, dir))
        delete_temp(get_root())


def check_score(output):
    final, score, imagePath, parent = output
    pathRef = Path(imagePath)
    fileFullName = pathRef.name.split(".")
    extension = fileFullName.pop()

    threshold = getenv('IMAGE_%s_THRESHOLD' %
                       extension.upper()) or getenv("IMAGE_DEFAULT_THRESHOLD")
    logger.info("check_score: detecting threshold ... extension = %s, threshold = %s " % (
        extension, threshold))
    saveIn = path.join(pathRef.parent, "{}.{}".format(
        ".".join(fileFullName), extension))
    imageprocessor.save_image(
        (final, score, saveIn, parent), int(threshold))


def run_job():
    try:
        responseCode = call(getenv("JOB_SCRIPT_PATH"), shell=True)
        logger.info("Executed job return code : %s " % responseCode)
        if not type(responseCode) == int or responseCode != 0:
            raise Exception("Unknown error, please refer to your job")
    except Exception as e:
        logger.error("Error when executing job %s " % e)
        raise e


def move_rejected():
    root = get_root()
    move_rejected_files(root)


def upload_files():
    roots = ['output', 'rejected']
    put_data(roots)


def compress():
    root = get_root()
    compress_directories(root)


def move_to_output():
    root = get_root()
    move_image_to_root(path.join(root, 'output'), path.join(root, 'output'))


def append_score():
    isNotLocal = getenv("ENV") != 'localhost'
    try:
        config = load_config()
        root = config.get("imagespath") if isNotLocal else get_root()

        temp = create_dir(root, '.tmp')
        empty_dir(create_dir(root, 'output'))  # remove all content
        empty_dir(create_dir(root, 'rejected'))  # remove all content
        dataFile = config.get("csvpath")
        fileName = dataFile.split("/").pop()
        out_file = open(path.join(temp, fileName), 'w')
        with open(dataFile, 'r') as input:
            reader = csv.DictReader(input, delimiter='@')
            header = reader.fieldnames
            if len(header) > int(getenv("SOURCE_FILE_COLUMNS")):
                raise Exception("unexpected csv file structure")
            header.append('Score')

            writer = csv.DictWriter(out_file, fieldnames=header, delimiter='@')
            writer.writeheader()
            i = 0
            for row in reader:
                if i == 0:
                    logger.info('row sample -> %s ' % row)
                    i += 1
                impath = path.join(root, row["Photo"].strip("/"))
                (final, score, image_path) = imageprocessor.apply_processors(
                    impath, root)
                row["Score"] = score # TODO: commenting this mean no Score column will be added to the csv output file
                writer.writerow(row)
                check_score((final, score, image_path, root))
            out_file.close()
            move(path.join(temp, fileName),
                 path.join(root, fileName))
        delete_temp(root)
    except Exception as e:
        logger.error("error while apply score -> %s " % e)
        out_file.close()
        raise e
        # randomize_sample_images(to_generate)
# process_batch_sample([get_sample_dir()],
#                      lambda dir: (
#     empty_dir(create_dir(dir, 'output')),
#     empty_dir(create_dir(dir, 'rejected'))
# ), lambda output: check_score(output))


steps = {
    1: {"name": 'Download and Extract data from S3', "handler": get_data},

    2: {"name": 'Convert xlsx file to csv', "handler": convert_to_csv},
    3: {"name": 'Process Images in each sub-batch', "handler": append_score},
    4: {"name": 'Execute Data control Job', "handler": run_job},
    5: {"name": 'Move Job rejected Images', "handler": move_rejected},
    6: {"name": 'Move All output to root folder', "handler": move_to_output},
    7: {"name": 'Compress Rejected and Validated Images', "handler": compress},
    8: {"name": 'Upload Images to S3', "handler": upload_files},
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
