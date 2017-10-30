from subprocess import CompletedProcess

UNSPECIFIC_ERROR=-9999

class Result():
    '''
        A validation result that can be sent to the OpenSubmit Server.
    '''
    error_code:int=None             # Error code from execution
    info_student=''                 # Information text for the student
    info_tutor=''                   # Information text for the tutor
    perf_data=''                    # Performance data for the tutor
    stdout=''                       # Original stdout from the validation run
    stderr=''                       # Original stderr from the validation run
    action=''                       # Demanded action (legacy)

    def __init__(self, subprocess_result:CompletedProcess=None, max_length=10000):
        '''
            Creates a new OpenSubmit result object from a compile / test run result.
        '''
        if subprocess_result:
            self.convert(subprocess_result, max_length);

    def convert(self, subprocess_result, max_length):
        # There are cases where the program was not finished, but we still deliver a result
        # Transmitting "None" is a bad idea, so we use a special code instead
        if subprocess_result.returncode==None:
            self.error_code=UNSPECIFIC_ERROR
        else:
            self.error_code=subprocess_result.returncode
        if subprocess_result.stdout:
            if max_length:
                self.info_student=subprocess_result.stdout[0:max_length-20]+"\n[Output truncated]"
                self.info_tutor  =subprocess_result.stdout[0:max_length-20]+"\n[Output truncated]"
            else:
                self.info_student=subprocess_result.stdout
                self.info_tutor  =subprocess_result.stdout
        self.perf_data=''


class PassResult(Result):
    '''
        A validation result indication success.
    '''
    def __init__(self, info_student):
        super().__init__()
        self.error_code=0
        self.info_student=info_student

class FailResult(Result):
    '''
        A validation result indication failure.
    '''
    def __init__(self, info_student):
        super().__init__()
        self.error_code=UNSPECIFIC_ERROR
        self.info_student=info_student
