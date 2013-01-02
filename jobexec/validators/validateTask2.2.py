import os, sys, re, time, subprocess, urllib.request, stat
from multiprocessing import Process, Value, Array, Pipe

#------------------------------------------------
# constants  ------------------------------------
#------------------------------------------------

baseurl = 'http://www.dcl.hpi.uni-potsdam.de/teaching/parProg/'
localFolder = '/tmp/'
inputFiles = ['task_2.2_pwsmall.txt', 'task_2.2_dict.txt']

executeable = './decrypt'
parameters = [localFolder + inputFiles[0], localFolder + inputFiles[1]]

outputFile = 'output.txt'
outputFormat = '^((user906;Bahnhof.*?user\d*;.*?)|(user\d*;.*?user906;Bahnhof))$'

solutionFile = 'task2solution.txt'

#------------------------------------------------
# global variables ------------------------------
#------------------------------------------------

maximalthreadcount=Value('i',0)

#------------------------------------------------
# functions -------------------------------------
#------------------------------------------------

# download text file via URL
def downloadText(url, filename):
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")
    fp.close()    
    if os.path.exists(filename):
        os.chmod(filename, stat.S_IWOTH | stat.S_IWGRP | stat.S_IWUSR)
    with open(filename, "w") as f:
        f.write(mystr)
    os.chmod(filename, stat.S_IROTH | stat.S_IRGRP | stat.S_IRUSR)

# download and store text files from remote location
def loadremotefiles(baseurl, inputFiles):
    for inputFile in inputFiles:
        file = localFolder + inputFile
        if not os.path.exists(file) or not os.path.isfile(file) or os.path.getsize(file) == 0:
            downloadText(baseurl + inputFile, file)
        
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
    match = re.search(format, text, re.DOTALL)
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
    loadremotefiles(baseurl, inputFiles)
    
    ensurefileexists(executeable)
    execute(executeable, parameters)

    ensurefileexists(outputFile)    
    checkfile(outputFile, outputFormat)

    ensurefileexists(solutionFile)    
    checkfile(solutionFile, outputFormat)
