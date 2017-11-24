'''
    Functions on filesystem level.
'''

import zipfile
import tarfile
import os
import tempfile
import shutil

from .result import FailResult, PassResult

import logging
logger = logging.getLogger('opensubmitexec')


def unpack_if_needed(destination_path, fpath):
    '''
    fpath is the fully qualified path to a single file that
    might be a ZIP / TGZ archive.
    The function moves the file, or the content if it is an
    archive, to the directory given by destination_path.

    Returns a boolean indicator that is true if:
    - fpath is an archive.
    - The archive contains only one single directory with
      arbitrary content. This is helpful in catching the
      typical "right-click to compress" cases for single
      ZIP files.
    '''
    result = False

    dircontent = os.listdir(destination_path)
    logger.debug("Content of %s before unarchiving: %s" %
                 (destination_path, str(dircontent)))

    # Perform un-archiving, in case
    if zipfile.is_zipfile(fpath):
        logger.debug("Detected ZIP file at %s, unpacking it." % (fpath))
        with zipfile.ZipFile(fpath, "r") as zip:
            infolist = zip.infolist()
            directories = [entry.filename for entry in infolist if entry.filename.endswith('/')]
            files = [entry.filename for entry in infolist if not entry.filename.endswith('/')]
            logger.debug(directories)
            logger.debug(files)
            if len(directories) == 1:
                d = directories[0]
                in_this_dir = [entry for entry in files if entry.startswith(d)]
                if len(files) == len(in_this_dir):
                    logger.debug("ZIP archive contains only one subdirectory")
                    result = True
            zip.extractall(destination_path)
    elif tarfile.is_tarfile(fpath):
        logger.debug("Detected TAR file at %s, unpacking it." % (fpath))
        with tarfile.open(fpath) as tar:
            infolist = tar.getmembers()
            # A TGZ file of one subdirectory with arbitrary files
            # has one infolist entry per directory and file
            directories = [entry.name for entry in infolist if entry.isdir()]
            files = [entry.name for entry in infolist if entry.isfile()]
            logger.debug(directories)
            logger.debug(files)
            if len(directories) == 1:
                d = directories[0]
                in_this_dir = [entry for entry in files if entry.startswith(d)]
                if len(files) == len(in_this_dir):
                    logger.debug("TGZ archive contains only one subdirectory")
                    result = True
            tar.extractall(destination_path)
    else:
        if not fpath.startswith(destination_path):
            logger.debug(
                "File at %s is a single non-archive file, copying it to %s" % (fpath, destination_path))
            shutil.copy(fpath, destination_path)

    dircontent = os.listdir(destination_path)
    logger.debug("Content of %s after unarchiving: %s" %
                 (destination_path, str(dircontent)))
    return result


def create_working_dir(config, prefix):
    '''
        Create a fresh temporary directory, based on the fiven prefix.
        Returns the new path.
    '''
    # Fetch base directory from executor configuration
    basepath = config.get("Execution", "directory")

    if not prefix:
        prefix = 'opensubmit'

    finalpath = tempfile.mkdtemp(prefix=prefix + '_', dir=basepath)
    if not finalpath.endswith(os.sep):
        finalpath += os.sep
    logger.debug("Created fresh working directory at {0}.".format(finalpath))

    return finalpath


def prepare_working_directory(job, submission_fname, validator_fname):
    '''
    Based on two downloaded files in the working directory,
    the student submission and the validation package,
    the working directory is prepared.

    We unpack student submission first, so that teacher files overwrite
    them in case.

    When the student submission is a single directory, we change the
    working directory and go directly into it, before fetching the
    validator stuff.

    Returns a Result object. 
    '''
    single_dir = unpack_if_needed(job.working_dir, submission_fname)
    dircontent = os.listdir(job.working_dir)

    # Check what we got from the student
    if len(dircontent) is 0:
        logger.error("Submission archive file has no content.")
        return FailResult("Your compressed upload is empty - no files in there.")
    elif single_dir:
        logger.warning(
            "The submission archive contains only one directory. I assume I should go in there ...")
        job.working_dir = job.working_dir + dircontent[0] + os.sep

    # Unpack validator package
    single_dir = unpack_if_needed(job.working_dir, validator_fname)
    if single_dir:
        logger.error("The validator archive contains only one directory.")
        return FailResult("Invalid validator archive, don't use subdirectories.")

    if not os.path.exists(job.validator_script_name):
        # The download is already the script
        logger.debug("Using the download directly als validator script.")
        shutil.move(validator_fname, job.validator_script_name)

    return PassResult()


def has_file(dir, fname):
    return os.path.exists(dir + os.sep + fname)
