'''
    Functions on filesystem level.
'''

import zipfile
import tarfile
import os
import tempfile
import shutil

from .exceptions import JobException

import logging
logger = logging.getLogger('opensubmitexec')


def unpack_if_needed(destination_path, fpath):
    '''
    fpath is the fully qualified path to a single file that
    might be a ZIP / TGZ archive.
    The function moves the file, or the content if it is an
    archive, to the directory given by destination_path.

    Returns a directory name if:
    - fpath is an archive.
    - The archive contains only one this single directory with
      arbitrary content.

    This is helpful in catching the typical "right-click to compress"
    cases for single ZIP files in Explorer / Finder.
    '''
    result = None

    dircontent = os.listdir(destination_path)
    logger.debug("Content of %s before unarchiving: %s" %
                 (destination_path, str(dircontent)))

    # Perform un-archiving, in case
    if zipfile.is_zipfile(fpath):
        logger.debug("Detected ZIP file at %s, unpacking it." % (fpath))
        with zipfile.ZipFile(fpath, "r") as zip:
            infolist = zip.infolist()
            directories = [entry.filename for entry in infolist if entry.filename.endswith('/')]
            logger.debug("List of directory entries: "+str(directories))

            # Consider this case: ['subdir1/', 'subdir1/subdir2/']
            if len(directories) > 1:
                redundant = []
                for current in directories:
                    starts_with_this = [el for el in directories if el.startswith(current)]
                    if len(starts_with_this) == len(directories):
                        # current is a partial directory name that is contained
                        # in all others
                        redundant.append(current)
                logger.debug("Redundant directory entries: "+str(redundant))
                directories = [entry for entry in directories if entry not in redundant]
                logger.debug("Updated list of directory entries: "+str(directories))

            files = [entry.filename for entry in infolist if not entry.filename.endswith('/')]
            logger.debug("List of files: "+str(files))
            if len(directories) == 1:
                d = directories[0]
                in_this_dir = [entry for entry in files if entry.startswith(d)]
                if len(files) == len(in_this_dir):
                    logger.debug("ZIP archive contains only one subdirectory")
                    result = d
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
                    result = d
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

    If unrecoverable errors happen, such as an empty student archive,
    a JobException is raised.
    '''
    single_dir = unpack_if_needed(job.working_dir, submission_fname)
    dircontent = os.listdir(job.working_dir)

    # Check what we got from the student
    if len(dircontent) is 0:
        info_student = "Your compressed upload is empty - no files in there."
        info_tutor = "Submission archive file has no content."
        logger.error(info_tutor)
        raise JobException(info_student=info_student, info_tutor=info_tutor)
    elif single_dir:
        logger.warning(
            "The submission archive contains only one directory. I assume I should go in there ...")
        job.working_dir = job.working_dir + single_dir + os.sep

    # Unpack validator package
    single_dir = unpack_if_needed(job.working_dir, validator_fname)
    if single_dir:
        info_student = "Internal error with the validator. Please contact your course responsible."
        info_tutor = "Error: Directories are not allowed in the validator archive."
        logger.error(info_tutor)
        raise JobException(info_student=info_student, info_tutor=info_tutor)

    if not os.path.exists(job.validator_script_name):
        # The download is already the script
        logger.debug("Using the download directly als validator script.")
        shutil.move(validator_fname, job.validator_script_name)


def has_file(dir, fname):
    return os.path.exists(dir + os.sep + fname)
