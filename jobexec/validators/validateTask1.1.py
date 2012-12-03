import os, sys, re, time, subprocess
from multiprocessing import Process, Value, Array, Pipe

maximalthreadcount=Value('i',0)

#------------------------------------------------
# constants  ------------------------------------
#------------------------------------------------

executeable = './parsum'
parameters = ['30', '1',  '1000000000']

outputFile = 'output.txt'
outputFormat = '^500000000500000000$'

#------------------------------------------------
# functions -------------------------------------
#------------------------------------------------

# polling thread body
def pollingthreadbody(pipeRecv):
    #print("Waiting for PID")
    processid=pipeRecv.recv()[0]
    #print("Got PID "+str(processid))
    while True:
        #print("Poll")
        prog = os.popen('cat /proc/' + str(processid) + '/status | grep Thread')
        threadline = prog.read()
        if not threadline.startswith('Threads:'):
            return 0
        #print("#"+threadline+"#")
        currentthreadcount=int(threadline.replace("Threads:", "").strip())
        if currentthreadcount > maximalthreadcount.value:
            print("Found %u threads in application"%currentthreadcount)
            maximalthreadcount.value = currentthreadcount
        time.sleep(100)

# execute command
def execute(command, parameters, pipeSend):
    pollingthread.start()
    start = time.time()
    proc = subprocess.Popen([command] + parameters)
    pipeSend.send([proc.pid])
    proc.communicate()
    end = time.time()
    pollingthread.terminate()
    threadcount = maximalthreadcount.value
    print("Runtime:      %.4fs" % (end - start))
    print("Max thread count: " + str(threadcount))

# check if file exists
def ensurefileexists(file):
    if not os.path.exists(file) or not os.path.isfile(file):
        errorexit("File not found: " + file, 1)
    
# exit with message and error code
def errorexit(message, exitcode):
    print("[ERROR]-----------------------------")
    print(message)
    print("------------------------------------")
    sys.exit(exitcode)

# check if text is in the correct format
def matches(text, format):
    match = re.search(format, text)
    if match is None:
        return False
    return match.group(0) != ""

# check if file content matches pattern
def checkcontent(f, format):
    text = f.read()
    if not matches(text, format):
        errorexit("Result file does not match regular expression:\n" + format + "\n\n" + outputFile + "\n" + text, 3)

# check if file content matches pattern
def checkfile(file, contentformat):
    # try open file
    try:
        with open(file) as f:
            checkcontent(f, contentformat)
    except IOError as e:
        errorexit("Could not open file: " + file, 2)

#------------------------------------------------
# program starts HERE ---------------------------
#------------------------------------------------

if __name__ == '__main__':
    print("Starting validator")
    pipeRecv, pipeSend = Pipe(duplex=False)
    pollingthread = Process(target=pollingthreadbody, args=(pipeRecv,))

    ensurefileexists(executeable)
    execute(executeable, parameters, pipeSend)

    ensurefileexists(outputFile)    
    checkfile(outputFile, outputFormat)
