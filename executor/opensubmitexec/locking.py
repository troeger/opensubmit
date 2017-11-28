'''
    Locking helper functions.
'''

from twisted.python.lockfile import FilesystemLock
import os

import logging
logger = logging.getLogger('opensubmitexec')


def break_lock(config):
    fname = config.get("Execution", "pidfile")
    try:
        os.remove(fname)
        logger.info("Lock file at {0} removed.".format(fname))
    except FileNotFoundError:
        logger.info("No lock file found at {0}.".format(fname))


class ScriptLock():
    config = None
    flock = None

    def __init__(self, config):
        '''
        Parse machine-local configuration file.
        '''
        self.config = config

    def __enter__(self):
        '''
        Be a context manager.
        '''
        fname = self.config.get("Execution", "pidfile")
        self.flock = FilesystemLock(fname)
        logger.debug("Obtaining script lock")
        self.flock.lock()

    def __exit__(self, exc_type, exc_value, traceback):
        '''
        Be a context manager.
        '''
        logger.debug("Releasing script lock")
        self.flock.unlock()
