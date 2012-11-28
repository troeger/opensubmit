import os, sys, re, time, subprocess
from multiprocessing import Process, Value, Array

#------------------------------------------------
# constants  ------------------------------------
#------------------------------------------------

executeable = './dinner'
parameters = ['3', '10']

outputFile = 'output.txt'
outputFormat = '^\d+;\d+;\d+$'

#------------------------------------------------
# functions -------------------------------------
#------------------------------------------------

# get thread count of process
def threadcount(processid):
    if processid == 0:
        return 0
    prog = os.popen('cat /proc/' + str(processid) + '/status | grep Thread')
    threadline = prog.read()
    if not threadline.startswith('Threads:'):
        return 0
    return int(threadline.replace("Threads:", "").strip())

# polling thread body
def pollingthreadbody(currentprocessid, maximalthreadcount):
    while True:
        currentthreadcount = threadcount(currentprocessid.value)
        if currentthreadcount > maximalthreadcount.value:
            maximalthreadcount.value = currentthreadcount
        time.sleep(100)

# execute command
def execute(command, parameters):
    pollingthread.start()
    start = time.time()
    proc = subprocess.Popen([command] + parameters, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    currentprocessid.value = proc.pid
    output, stderr = proc.communicate()
    end = time.time()
    pollingthread.terminate()
    threadcount = maximalthreadcount.value
    print("Runtime:      %.4fs" % (end - start))
    print("Thread count: " + str(threadcount))
    print()
    print("stdout: \n" + str(output))
    print()
    print("stderr: \n" + str(stderr))

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
    currentprocessid = Value('i', 0)
    maximalthreadcount = Value('i', 0)
    pollingthread = Process(target=pollingthreadbody, args=(currentprocessid, maximalthreadcount))

    ensurefileexists(executeable)
    execute(executeable, parameters)

    ensurefileexists(outputFile)    
    checkfile(outputFile, outputFormat)