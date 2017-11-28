'''
Functions dealing with the compilation of code.
'''

from .execution import shell_execution
from .filesystem import has_file
from .exceptions import ValidatorBrokenException

from exception import FileNotFoundError

import logging
logger = logging.getLogger('opensubmitexec')

GCC = ['gcc', '-o', '{output}', '{inputs}']
GPP = ['g++', '-o', '{output}', '{inputs}']


def call_make(directory):
    '''
    Call make to build the stuff.
    '''
    if not has_file(directory, 'Makefile'):
        raise FileNotFoundError("Could not find a Makefile.")
    logger.info("Running make in " + directory)
    shell_execution(['make'], directory)


def call_compiler(directory, compiler=GCC, output=None, inputs=None):
    '''
    Call the compiler to build the stuff.

    If the compile demands the output file name, it should be given in the
    output parameter.
    If the compiler demands the input file names, it should be given in the
    inputs parameter as list of strings.
    '''
    cmdline = []
    for element in compiler:
        if element == '{output}':
            if output:
                cmdline.append(output)
            else:
                logger.error('Missing output name for call_compiler')
                raise ValidatorBrokenException("You need to declare the output name for compilation.")
        elif element == '{inputs}':
            if inputs:
                for fname in inputs:
                    if compiler in [GCC, GPP] and fname.endswith('.h'):
                        logger.debug('Omitting {0} in the compiler call.'.format(fname))
                    else:
                        cmdline.append(fname)
            else:
                logger.error('Missing input file names for call_compiler')
                raise ValidatorBrokenException('You need to declare input files for compilation.')
        else:
            cmdline.append(element)

    logger.info("Running compilation in {0} with {1}".format(
        directory, cmdline))
    shell_execution(cmdline, directory)
