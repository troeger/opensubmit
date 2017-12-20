Tutorial on creating validators for student submissions
###################################################

Setting up the environment
**************************

Python version 3.4 or higher is required for opensubmit to work correctly.
Validators should be written in the same version.
The current version of Python 3 can be installed using the following command.

``sudo apt-get install python3``

For testing the validator on our local machine the tool opensubmit-exec is required.
It can be obtained by using pip3.
To install pip3 use the following command.

``sudo apt-get install python3-pip``

To keep our Python standard installation clean we use virtualenv for creating an virtual environment.

``pip3 install virtualenv``

The following command creates a new virtual environment in the desired directory (~/my_env in the following example).

``python3 -m virtualenv -p /usr/bin/python3 ~/my_env``

``source ~/my_env/bin/activate`` makes us switch to the newly created environment (activates it).
``deactivate`` makes us leave it.

When we activated the virtual environment we can install Python packages as usual by using pip3 but they will be installed in to our newly created directory, so our standard python installation stays clean.
For installing opensubmit-exec the following command is used.

``sudo pip3 install opensubmit-exec``

For obtaining the beta version of the software use the following command (0.7b3 can be replaced by the desired version).

``sudo pip3 install opensubmit-exec==0.7b3`` 

opensubmit-exec can now be used whenever we activated the corresponding virtual environment.
The next step is to configure opensubmit-exec.

``sudo opensubmit-exec configure``

On the first run a config file is created which can be changed accordingly.
Run the configure command again afterwards.

Creating validators and using opensubmit-exec
*********************************************

The creation of a validator is illustrated by the following example.
The students have to create a program in C that prints 'hello world' to the command prompt.
They have to submit the corresponding c-file and the makefile, which creates a program called 'hello'.

The student files are located in an zip-archive.
The directory for testing the newly created validator with the exemplary student submission should only contain the student submission archive (c-file and makefile) and the validator.py file.

.. image:: files/validation_example_hello.png

The validator.py file always consists of a validate-function, which is given an job-object as parameter.
The job-object is used for interacting with the student submission.
In the example above the delivered makefile is run and the created program 'hello' is executed.
The output and exit code of the program are returned and can be used for checking the correctness of the student submission.
According to the outcome a pass or fail result is sent to the student and the teacher.

To check if the validator is working correctly you can run the command ``opensubmit-exec test path/to/used/directory``.
All the necessary output for checking if the validator is working correctly and for reviewing the student and teacher notifications is created.

Sometimes it is necessary to use multiple files for validation.
If that is the case an archive named validator.zip containing the according files has to be created.
The directory for testing your validator should only contain the validator.zip archive and the student submission archive in this instance.

Examples for validators
***********************

