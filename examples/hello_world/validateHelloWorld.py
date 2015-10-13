'''
	This is an example for a validation test script.

	It runs a binary './helloworld' in the student submission directory
	and checks the output. Therefore, the compilation option must be checked
	for the assignment using this script.

	if the output matches, the exit code of this script is 0. This shows the
	submission system that the student code passed the test.
'''
import subprocess

output = subprocess.check_output(['./helloworld'])
if 'Hello World' in output:
	exit(0)
else:
	exit(-1)



