'''
Functions dealing with the compilation of code.
'''

from .execution import shell_execution
from .result import ValidatorBrokenResult
from .filesystem import has_file

import logging
logger = logging.getLogger('opensubmit.executor')

GCC = ['gcc','-o','{output}','{inputs}']
GPP = ['g++','-o','{output}','{inputs}']

def call_configure(directory):
    ''' 
    Call configure to generate a Makefile.
    '''
    if has_file(directory, 'configure'):
        logger.info("Running ./configure in "+directory)
        return shell_execution(['configure'], directory)
    else:
        return FailResult("Could not find a configure script for execution.")

def call_make(directory):
    ''' 
    Call make to build the stuff.
    '''
    if has_file(directory, 'Makefile'):
        logger.info("Running make in "+directory)
        return shell_execution(['make'], directory)
    else:
        return FailResult("Could not find a Makefile.")

def call_compiler(directory, compiler=GCC, output=None, inputs=None):
    ''' 
    Call the compiler to build the stuff.

    If the compile demands the output file name, it should be given in the
    output parameter.
    If the compiler demands the input file names, it should be given in the
    inputs parameter as list of strings.
    '''
    cmdline=[]
    for element in compiler:
        if element == '{output}':
            if output:
                cmdline.append(output)
            else:
                logger.error('Missing output name for call_compiler')
                return ValidatorBrokenResult('You need to declare the output name for compilation.')
        elif element == '{inputs}':
            if inputs:
                cmdline.append(' '.join(inputs))
            else:
                logger.error('Missing input file names for call_compiler')
                return ValidatorBrokenResult('You need to declare input files for compilation.')
        else:
            cmdline.append(element)

    logger.info("Running compilation in {0} with {1}".format(directory, cmdline))
    return shell_execution(cmdline, directory)

