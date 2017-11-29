'''
Small helper functions.
'''

import logging
logger = logging.getLogger('opensubmitexec')


def assert_raises(callable, *args, **kwargs):
    try:
        return callable(*args, **kwargs)
    except Exception:
        pass
    else:
        logger.error("Unexpected non-occurence of exception while running "+str(callable))
        raise SystemExit()

def assert_dont_raises(callable, *args, **kwargs):
    try:
        return callable(*args, **kwargs)
    except Exception as e:
        logger.error("Unexpected occurence of exception while running {1}: {0} ".format(e, str(callable)))
        raise SystemExit()
    else:
        pass
