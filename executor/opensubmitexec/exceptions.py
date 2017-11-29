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
    def __init__(self, instance):
        '''
        A problem that occured while running a student program.
        The instance parameter stores the
        RunningProgram instance raising this
        issue.
        '''
        self.instance = instance


class WrongExitStatusException(RunningProgramException):
    def __init__(self, instance, expected, got=None):
        self.instance = instance
        self.expected = expected
        self.got = got


class NestedException(RunningProgramException):
    '''
    An exception occured while running the student
    program.
    '''
    def __init__(self, instance, real_exception):
        self.instance = instance
        self.real_exception = real_exception


class ValidatorBrokenException(JobException):
    '''
    Indication that the validator script is broken.
    '''
    pass
