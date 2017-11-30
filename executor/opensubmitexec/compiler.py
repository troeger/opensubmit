'''
Functions dealing with the compilation of code.
'''

from .exceptions import ValidatorBrokenException

import logging
logger = logging.getLogger('opensubmitexec')

GCC = ['gcc', '-o', '{output}', '{inputs}']
GPP = ['g++', '-pthread', '-o', '{output}', '{inputs}']


def compiler_cmdline(compiler=GCC, output=None, inputs=None):
    cmdline = []
    for element in compiler:
        if element == '{output}':
            if output:
                cmdline.append(output)
            else:
                logger.error('Compiler output name is needed, but not given.')
                raise ValidatorBrokenException("You need to declare the output name for this compiler.")
        elif element == '{inputs}':
            if inputs:
                for fname in inputs:
                    if compiler in [GCC, GPP] and fname.endswith('.h'):
                        logger.debug('Omitting {0} in the compiler call.'.format(fname))
                    else:
                        cmdline.append(fname)
            else:
                logger.error('Input file names for compiler are not given.')
                raise ValidatorBrokenException('You need to declare input files for this compiler.')
        else:
            cmdline.append(element)
    return cmdline[0], cmdline[1:]
