'''
    Functions on filesystem level.
'''

import logging
logger = logging.getLogger('opensubmit.executor')

import zipfile, tarfile, os, tempfile

def unpack_if_needed(destination_path: str, fpath: str) -> int:
    '''
        Unpacks or simply moves the given file into the destination path-
        fpath is a full-qualified path to some potential archive file.

        Returns the content of the directory.
    '''

    dircontent = os.listdir(destination_path)
    logger.debug("Content of %s before unarchiving: %s"%(destination_path,str(dircontent)))

    # Perform un-archiving, in case
    if zipfile.is_zipfile(fpath):
        logger.debug("Detected ZIP file at %s, unpacking it."%(fpath))
        with zipfile.ZipFile(fpath, "r") as zip:
            zip.extractall(destination_path)
    elif tarfile.is_tarfile(fpath):
        logger.debug("Detected TAR file at %s, unpacking it."%(fpath))
        with tarfile.open(fpath) as tar:
            tar.extractall(destination_path)
    else:
        if not fpath.startswith(destination_path):
            logger.debug("File at %s is a single non-archive file, copying it to %s"%(fpath, destination_path))
            shutil.copy(fpath, destination_path)

    dircontent = os.listdir(destination_path)
    logger.debug("Content of %s after unarchiving: %s"%(destination_path,str(dircontent)))
    return dircontent

def create_working_dir(config, prefix):
    '''
        Create a fresh temporary directory, based on the fiven prefix.
        Returns the new path.
    '''
    # Fetch base directory from executor configuration
    basepath = config.get("Execution","directory")

    if not prefix:
        prefix='opensubmit'

    finalpath = tempfile.mkdtemp(prefix=prefix+'_', dir=basepath)
    if not finalpath.endswith(os.sep):
        finalpath += os.sep
    logger.debug("Created fresh working directory at {0}.".format(finalpath))

    return finalpath

def has_file(dir, fname):
    return os.path.exists(dir+os.sep+fname)
