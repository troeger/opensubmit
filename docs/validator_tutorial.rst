Tutorial on creating validators for student submissions
###################################################

Setting up the environment
**************************

opensubmit requires Python version 3.4 or higher.
Validators should be written in this version as well.
The current version of Python 3 can be installed using the following command:
``sudo apt-get install python3``

For testing the validator on your local machine the tool opensubmit-exec is required.
It can be obtained via using pip3.
To install pip3 use the following command.
``sudo apt-get install python3-pip``

To keep your Python standard installation clean use virtualenv for creating an virtual environment.
Use the following command for installing virtualenv.
``pip3 install virtualenv``

Use the following command for creating a new virtual environment in the desired directory (~/my_env in the following example).
``python3 -m virtualenv -p /usr/bin/python3 ~/my_env``

To switch to the newly created environment use ``source ~/my_env/bin/activate``.
To leave it use ``deactivate``.

Now you can install python packages as usual by using pip3.
For installing opensubmit-exec the following command is used.
``sudo pip3 install opensubmit-exec``

If you want to use the beta version of the software use the following command.
0.7b3 can be replaced by the desired version.
``sudo pip3 install opensubmit-exec==0.7b3`` 

To use opensubmit-exec you have to switch to the corresponding virtual environment.
``source ~/my_env/bin/activate``


///
The next step is to configure opensubmit-exec.
``sudo opensubmit-exec configure``
On the first run a config file is created which can be changed accordingly.
Run ``sudo opensubmit-exec configure`` again afterwards.
///

Creating validators and using opensubmit-exec
*********************************************

The creation of a validator is illustrated by the following example.
The students have to create a program in C that prints 'hello world' to the command prompt.
They have to submit the corresponding c-file and the Makefile, which creates a program called 'hello'.

The student files are located in an zip-archive.
The directory for testing the newly created validator with the exemplary student submission should only contain the student submission archive (c-file and Makefile) and the validator.py file.

.. image:: files/validation_example_hello.png

The validator consists of a validate-function, which is given an job-object as parameter.
The job-object is used for interacting with the student submission.
In the example above the delivered Makfile is run and the created program 'hello' is executed.
The output and exit code of the program are returned and can be used for checking the correctness of the student submission.
According to the outcome a pass or fail result is sent to the student and the teacher.

To check if the validator is working correctly you can run the command ``opensubmit-exec test path/to/used/directory``.
All the necessary output for checking if the validator is working correctly and for reviewing the student and teacher notifications is created.

Sometimes it is necessary to use multiple files for validation.
If that is the case you have to create an archive named validator.zip containing the according files.
The directory for testing your validator should only contain the validator.zip archive and the student submission archive in this instance.

Examples for validators
***********************