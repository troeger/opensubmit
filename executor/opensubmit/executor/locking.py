'''
    Locking helper functions.
'''

import logging, os
logger = logging.getLogger('opensubmit.executor')

from twisted.python.lockfile import FilesystemLock

def break_lock(config):
    fname=config.get("Execution", "pidfile")
    os.remove(fname)

class ScriptLock():
    config = None
    flock = None

    def __init__(self, config):
        '''
        Parse machine-local configuration file.
        '''
        self.config=config

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
