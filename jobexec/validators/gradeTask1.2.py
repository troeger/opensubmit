import os, sys, re, time, subprocess
from multiprocessing import Process, Value, Array, Pipe

#------------------------------------------------
# constants  ------------------------------------
#------------------------------------------------

executeable = './dinner'
outputFile = 'output.txt'

executionInfos = [
# parameters, outputformat, threadcount, execution time
['assignment example', ['3', '10'], '^\d+;\d+;\d+$', 3, 10],
['one thread and short execution time', ['1', '3'], '^\d+$', 1, 3],
['many threads and some runtime', ['100', '30'], '^(\d+;)+\d+$', 100, 30],
]

#------------------------------------------------
# global variables ------------------------------
#------------------------------------------------

maximalthreadcount=Value('i',0)

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
def execute(command, parameters):
    maximalthreadcount.value = 0
    pipeRecv, pipeSend = Pipe(duplex=False)
    pollingthread = Process(target=pollingthreadbody, args=(pipeRecv,))
    pollingthread.start()
    start = time.time()
    proc = subprocess.Popen([command] + parameters)
    pipeSend.send([proc.pid])
    proc.communicate()
    end = time.time()
    pollingthread.terminate()
    threadcount = maximalthreadcount.value
    return [end - start, threadcount]

# check if file exists
def ensurefileexists(file):
    if not os.path.exists(file) or not os.path.isfile(file):
        errorexit("File not found: " + file, 1)
    
# exit with message and error code
def errorexit(message, exitcode):
    print("[ERROR]-----------------------------")
    print(message)
    print("------------------------------------")
    # sys.exit(exitcode)

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
    ensurefileexists(executeable)
    
    for info in executionInfos:
        print('Test description: ' + info[0])
        print('Running:          ' + executeable + ' ' + ' '.join(info[1]))
        result = execute(executeable, info[1])
        
        threadcountquality = "Ok"
        if result[1] > info[3] + 1:
            threadcountquality = "Too Many!"
        if result[1] < info[3]:
            threadcountquality = "Too Few!"
        print("Max thread count: {} [{}]".format(result[1], threadcountquality))
        
        runtimequality = "Ok"
        if result[0] < 0.9 * info[4]:
            runtimequality = "Too Fast!"
        if result[0] > 1.1 * info[4]:
            runtimequality = "Took to Long!"
        print("Runtime:          {:.2f} [{}]".format(result[0], runtimequality))
        
        ensurefileexists(outputFile)
        checkfile(outputFile, info[2])
        print('')
