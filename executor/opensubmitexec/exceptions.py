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
    def __init__(self, instance, real_exception=None):
        '''
        Wrapper for an arbitrary exception
        that occured while running a student program.
        The instance parameter stores the
        RunningProgram instance raising this
        issue. The real_exception parameter
        holds the truly happened exception.
        '''
        super.__init__(self)
        self.instance = instance
        self.real_exception = real_exception


class ValidatorBrokenException(JobException):
    '''
    Indication that the validator script is broken.
    '''
    pass
