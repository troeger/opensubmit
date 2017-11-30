class JobException(Exception):
    '''
    An exception that occured while using
    the Job API.
    '''
    def __init__(self, info_student=None, info_tutor=None):
        self.info_student = info_student
        self.info_tutor = info_tutor
    pass


class RunningProgramException(Exception):
    def __init__(self, instance, output=None):
        '''
        A problem that occured while running a student program.
        The instance parameter stores the
        RunningProgram instance raising this
        issue.
        The output paramete stores all the output data
        being produces so far.
        '''
        self.instance = instance
        self.output = output


class WrongExitStatusException(RunningProgramException):
    def __init__(self, instance, expected, got=None, output=None):
        self.instance = instance
        self.expected = expected
        self.output = output
        self.got = got


class NestedException(RunningProgramException):
    '''
    An exception occured while running the student
    program.
    '''
    def __init__(self, instance, real_exception, output=None):
        self.instance = instance
        self.real_exception = real_exception
        self.output = output


class TimeoutException(NestedException):
    pass


class TerminationException(NestedException):
    pass


class ValidatorBrokenException(JobException):
    '''
    Indication that the validator script is broken.
    '''
    pass
