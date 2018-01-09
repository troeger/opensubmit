Teacher Manual
##############

OpenSubmit was invented for making assignments more fun for the students, and less work for the teachers. Before you start to read into details, we recommend to get into the basic :ref:`idea <index>` and general :ref:`principles <principles>`. 

Student tutors, course owners and administrators (see also :ref:`permissions`) all operate in the teacher backend, which is reachable by a link at the bottom of the student dashboard page, or directly via *<your OpenSubmit url>/teacher*.

Managing study programs
***********************

Location: ``Teacher backend`` - ``System`` - ``Actions`` - ``Manage study programs``

This function is only available for users with according :ref:`permissions <permissions>`.

Students register in OpenSubmit by themselves, simply by using one of the configured authentication methods (see :ref:`auth`). After the first login, there are asked to complete their user details (see also :ref:`userdetails`). 

One part of the user details dialogue is the choice of the study program, e.g. *computer science (Bachelor)* or *Greek philosophy (Master)*. When more than one study program is configured in OpenSubmit, then this choice becomes mandatory. If only a single or no study program is configured, then the students are not forced to make that choice.

The study program is shown in the :ref:`useroverview` and the :ref:`gradingtable`. Is has no further impact on the operation of OpenSubmit, but can help with the grading of mixed courses.

Managing courses
****************

Location: ``Teacher backend`` - ``System`` - ``Actions`` - ``Manage courses``

This function is only available for users with according :ref:`permissions <permissions>`.

Assignments for students belong to a course. The registered students can choose (see also :ref:`usercourses`) which course they participate in. This is different to many other learning management systems, which offer dedicated course permission systems (see also :ref:`principles`). 

Course creation 
===============

Location: ``Teacher backend`` - ``System`` - ``Actions`` - ``Manage courses`` - ``Add course``

The following settings must be configured for a new course:

.. _active:

Title
    The title of the course.
Course owner 
    A user who automatically gets :ref:`course owner <permissions>` permissions for this course. His email address is used as sender in student notifications. 
Tutors
    A set of users that get :ref:`student tutor <permissions>` permissions for this course. 
Course description link
    A URL for the course home page. Used in the student dashboard.
Active
   The flag decides if any assignments from this course are shown to the students, regardless of their deadlines. This allows to put courses in an 'archive' mode after the term is over. 
LTI key / LTI passphrase
   OpenSubmit supports the LTI protocol, so that you can integrate it into other learning management systems (LMSs) such as `Moodle <https://docs.moodle.org/34/en/External_tool>`_. 

   The LMS needs a consumer key and a shared secret resp. passphrase that you configure separately for each OpenSubmit course. This makes sure that the system knows automatically the course in which the external LMS user is interested in. Such users don't need to perform any authentication, OpenSubmit blindly believes in the identify information forwarded by the LMS. If a user already exists with the same email address, the LMS identity is added to his social login credentials. 

   Using LTI authentication can lead to duplicate accounts. You can :ref:`merge users <merge users>` to fix that.

Providing a link to the course assignments 
==========================================

Location: ``Teacher backend`` - ``Course`` - ``Info``

After using an :ref:`authentication provider <auth>`, students get automatically an account and end up on the student dashboard, where none of the OpenSubmit courses is activated for them. This leads to the fact that they can't see any course assignments by default.

If you want to make sure that students automatically see the assignments for your course, you need to tell OpenSubmit the course ID when entering the system. This can be done by linking to a course-specific OpenSubmit URL. It is shown in the course details on the teacher backend landing page.

.. _gradingscheme:

Grading scheme creation
=======================

Location: ``Teacher backend`` - ``System`` - ``Actions`` - ``Manage grading schemes``

Before you can create assignments for students, you must think about the grading scheme. A grading scheme is an arbitrary collection of gradings, were each grading either means 'pass' or 'fail'. 

Grading schemes can later be used in the creation of assignments.

Assignment creation
===================

Location: ``Teacher backend`` - ``Course`` - ``Actions`` - ``Manage assignments`` - ``Add assignment``

With an existing course and an appropriate grading scheme, you can now create a new assignment:

Title (mandatory)
    The title of the assignment.
Course (mandatory)
    The course this assignment belongs to. 
Grading scheme (optional)
    The grading scheme for this assignment. If you don't chose a grading scheme, than this assignment is defined as ungraded, which is also indicated on the student dashboard. Ungraded assignments are still validated.
Max authors (mandatory)
    For single user submissions, set this to one. When you choose larger values, the students get a possiblity to define their co-authors when submitting a solution.
Student file upload (mandatory)
    If students should upload a single file as solution, enable this flag. Otherwise, they can only enter submission notes. Students typically submit archives (ZIP / TGZ) or PDF files, but the system puts no restrictions on this.
Description (mandatory)
    The assignment description is linked on the student dashboard. It can either bei configured as link, f.e. when you host it by yourself, or can be uploaded to OpenSubmit.
Publish at (mandatory)
    The point in time where the assignment becomes visible for students. Users with teacher backend access rights always see the assignment in their student dashboard, so that they can test the validation before the official start.
Soft deadline (optional)
    The deadline shown to the students. After this point in time, submission is still possible, although the remaining time counter on the student dashboard shows zero.

    If you leave that value empty, then the hard deadline becomes the soft deadline, too.

    The separation between hard and soft deadline is intended for the typical late-comers, which try to submit their solution shortly after the deadline. Broken internet, time zone difficulties, dogs eating the homework ... we all know the excuses.
Hard deadline (optional)
    The deadline after which submissions for this assignment are no longer possible.

    If you leave that value empty, then submissions are possible as long as the course is :ref:`active <active>`.
Validation test (optional)
    The uploaded :ref:`validation test <testing>` is executed automatically for each student submission and can lead to different subsequent :ref:`states <states>` for the submission. Students are informed about this state change by email. The test is executed before the hard deadline. It is intended to help the students to write a valid solution.
Download of validation test (optional)
    The flag defines if the students should get a link to the :ref:`validation test <testing>`. This makes programming for the students much more easy, since the can locally if their uploaded code would pass the validation checks.
Full test (optional)
    The uploaded :ref:`full test <testing>` is executed automatically for each student submission and can lead to different subsequent :ref:`states <states>` for the submission. Students are *not informed* about this test. The test is executed after the hard deadline. It is intended to support the teachers in their grading with additional information.  
Support files (optiona)
    A set of files that you want to have in the same directory when the :ref:`validation test <testing>` or the :ref:`full test <testing>` is running.
Test machines (mandatory in some cases)
    When you configure a :ref:`validation test <testing>` or :ref:`full test <testing>`, you need to specify the ::ref:`test machines <executors>` that run it. When chosing multiple machines, the testing load is distributed.

Managing submissions
********************

A submission is a single (archive) file + notes handed in by a student. Every submission belongs to a particular assignment and its according course in OpenSubmit.

A student submission can be in different states. Each of the states is represented in a different way in student frontend and the teacher backend: 

.. _states:
.. literalinclude:: ../web/opensubmit/models/submission.py
   :language: python
   :start-after: # Docs start: States
   :end-before:  # Docs end: States

Submission grading
==================

Location: ``Teacher backend`` - ``Course`` - ``Manage submissions``

Location: ``Teacher backend`` - ``Course`` - ``Manage assignments``  - ``Show submissions``

The grading of student submissions always follows the same workflow, regardless of the fact if you are using the automated testing facilities or not.

Short version:

- For every submission:

  - Open the submission in the teacher backend.
  - Use the preview function for inspecting uploaded student archives.
  - Check the output from validation test and full test.
  - Optional: Add grading notes and a grading file for the student as feedback.
  - Decide for a grading, based on the provided information.
  - Mark the submission as **grading finished** if you are done with it.

- Close and notify all finished submissions as bulk action.

Long version:

On the right side of the submissions overview page, different filtering options are available.

.. image:: files/ui_backend_submissions.png    

The most important thing is the distinguishing between **non-graded**, **graded** and **closed** submissions:

**Non-graded** submissions are the ones that were submitted (and successfully validated) before the hard deadline. Your task is to go through these submissions and decided for a particular grading. If this is done, than the grading is marked as being completed for this particular submission. This moves it into the **graded** state.

When all gradings are done, then the submissions can be **closed**. This is the point in time were the status for the students changes, before that, no notification is done. The idea here is to first finish the grading - maybe with multiple people being involved - before notifying all students about their results. Only submissions in the **graded** status can be closed. This is a safeguard to not forget the finishing of some grading procedure.

The submission details dialogue shows different information:

.. image:: files/ui_backend_submission.png    

The assignment may allow the students to define co-authors for their submission. You can edit this list manually, for example when students made a mistake during the submission. The according section is hidden by default, click on the `Authors` tab to see it.

The original *submitter* of the solution is stated separately. Submitters automatically become authors. 

Students can always add notes to their submission. If file upload is disabled for the assignment, this is the only gradable information.

The *file upload* of the students is available for direct download, simply by clicking on the file name. This is especially relevant when having text or PDF document as solution attachment. The *Preview* link opens a separate web page with a preview of the file resp. the archive content.

When :ref:`testing <testing>` is activated for this assignment, then the according result output is shown in the submission details.

The choice of a *grading* is offered according to the :ref:`grading scheme <gradingscheme>` being configured for the particular assignment. The *grading notes* are shown in the student frontend, together with the grade, when the submission is closed. 

The *grading file* is also offered after closing, and may - for example - contain some explanary template solution or a manually annotated version of the student file upload.

The radio buttons at the bottom of the page allow to mark the submission as **non-graded** or **graded**.

When all submissions are finally graded, it is time to release the information to the students. In order to do this, mark on the overview page all finished submissions. This can be easily done by using the filters on the right side and the 'mark all' checkbox in the upper left corner. The choose the action 'Close graded submissions + send notification'.

.. _gradingtable:

Grading table
=============

Location: ``Teacher backend`` - ``Course`` - ``Show grading table``

If you want to have a course-level overview of all student results so far, use the *grading table* overview. It is available as action in the *Courses* section of the teacher backend.

Duplicate report
================

Location: ``Teacher backend`` - ``Course`` - ``Manage assignments``  - ``Show duplicates``

A common task in assignment correction is the detection of cheating. In OpenSubmit terms, this leads to the question if different students have submitted identical, or at least very similar, solutions for an assignment.

Checking arbitrary code for similarities is a complex topic by itself and is closely related to the type and amount of code being checked. OpenSubmit follows it general :ref:`principles <principles>` here by not restricting the possible types of submission for a perfect duplicate detection. Instead, we encourage users with specific demands to use such services in their :ref:`testing scripts <testing>`. 

OpenSubmit provides a basic duplicate checking for submitted files based on weak hashing of the student archives content. This method works independently from the kind of data and can, at least, detect the most lazy attempts of re-using other peoples work.

Based on the hashing results, the duplicate report shows groups of students that may have submitted the same result. This list must be treated as basic indication for further manual inspection. The report works independently from the course and the status of the submissions. Withdrawn solutions are skipped in the report.

.. _testing:

Automated testing of submissions
********************************

The automated testing of submissions is performed by a Python 3 script that you, the assignment creator, have to write. This script is executed by OpenSubmit on some configured :ref:`test machines <executors>`. You are completely free in what you want to do in this script - at the end, OpenSubmit just needs an indication about the result. Common tasks, such as code compilation and execution, are supported by helper functions you can use in this script.

You can upload such a script in two ways:

- As single Python file named `validator.py`.
- As ZIP / TGZ archive with an arbitrary name, which must contain a file named `validator.py`.

The second option allows you to deploy additional files (e.g. profiling tools, libraries, code not written by students) to the test machine. OpenSubmit ensures that all these files are stored in the same directory as the student code and the Python script.

How to write a test script
==========================

Test scripts are written in Python 3.4 and will be directly called by the OpenSubmit daemon running on test machines.

You can install this daemon, which is also called *executor*, on your own computer easily. This gives you an offline development environment for test scripts while you are working on the assignment description.

Similar to the installation of :ref:`test machines <executors>`, the following procedure (for Debian / Ubuntu systems) gives you a testing environment:

- Install Python 3: ``sudo apt-get install python3 python3-pip``

To keep your Python installation clean, we recommend to use `Virtualenv <https://virtualenv.pypa.io/en/stable/>`_:

- Install the Virtualenv tool: ``sudo pip3 install virtualenv``
- Create a new virtual environment, e.g. in ``~/my_env``: ``python3 -m virtualenv ~/my_env``
- Activate it with ``source ~/my_env/bin/activate``
- Install the OpenSubmit validator library / executor inside: ``pip3 install opensubmit-exec``
- Develop the `validator.py` for your assignment.

Examples for test scripts can be found `online <https://github.com/troeger/opensubmit/tree/master/examples>`_.

We illustrate the idea with the following walk-through example:

Students get the assignment to create a C program that prints 'Hello World' on the terminal. The assignment description demands that they submit the C-file and a *Makefile* that creates a program called *hello*. The assignment description also explains that the students have to `submit a ZIP archive <_newsubmission>`_ containing both files.

Your job, as the assignment creator, is now to develop the ``validator.py`` file that checks an arbitrary student submission. Create a fresh directory that only contains an example student upload and the validator file:

.. literalinclude:: files/validators/helloworld/validator.py
   :linenos:

The ``validator.py`` file *must contain a function ``validate(job)``* that is called by OpenSubmit when a student submission should be validated. In the example above, this function performs the following steps for testing:

- Line 1: The validator function is called when all student files (and all files from the validator archive) are unpacked in a temporary working directory on the test machine. In case of name conflicts, the validator files always overwrite the student files.
- Line 2: The *make* tool is executed in the working directory with :meth:`~opensubmitexec.job.run_make`. This step is declared to be mandatory, so the method will throw an exception if *make* fails.
- Line 3: A binary called *hello* is executed in the working directory with the helper function :meth:`~opensubmitexec.job.Job.run_program`. The result is the exit code and the output of the running program.
- Line 4: The generated output of the student program is checked for some expected text.
- Line 5: A positive validation result is sent back to the OpenSubmit web application with :meth:`~opensubmitexec.job.Job.send_pass_result`. The text is shown to students in their dashboard.
- Line 6: A negative validation result is sent back to the OpenSubmit web application with :meth:`~opensubmitexec.job.Job.send_fail_result`. The text is shown to students in their dashboard.

Test scripts are ordinary Python code, so beside the functionalities provided by the job object, you can use any Python functionality. The example shows that in Line 4. 

If any part of the code leads to an exception that is not catched inside ``validate(job)``, than this is automatically interpreted as negative validation result. The OpenSubmit executor code forwards the exception as generic information to the student. If you want to customize the error reporting, catch all potential exceptions and use your own call of :meth:`~opensubmitexec.job.Job.send_fail_result` instead.

To check if the validator is working correctly, you can run the command ``opensubmit-exec test <directory>`` in your VirtualEnv. It assumes the given directory to contain a validator script resp. archive and the student submission file resp. archive. The command simulates a complete validation run on a test machine and prints exhaustive debugging information. The last line contains the feedback sent to the web application after finalization.

Test script examples
====================

The following example shows a validator for a program in C that prints the sum of two integer values. The values are given as command line arguments. If the wrong number of arguments is given, the student code is expected to print `"Wrong number of arguments!"`. The student only has to submit the C file.

.. literalinclude:: files/validators/program_params/validator.py
    :linenos:

- Line 1: The `GCC` tuple constant is predefined by the OpenSubmit library and refers to the well-known GNU C compiler. You can also define your own set of command-line arguments for another compiler.
- Line 3-10: The variable `test_cases` consists of the lists of inputs and the corresponding expected outputs.
- Line 13: The C file can be compiled directly by using :meth:`~opensubmitexec.job.Job.run_compiler`. You can specify the used compiler as well as the names of the input and output files.
- Line 14: The for-loop is used for traversing the `test_cases`-list. It consists of tuples which are composed of the arguments and the expected output.
- Line 15: The arguments can be handed over to the program through the second parameter of the :meth:`~opensubmitexec.job.Job.run_program` method. The former method returns the exit code as well as the output of the program.
- Line 16: It is checked if the created output equals the expected output.
- Line 17: If this is not the case an appropriate negative result is sent to the student and teacher with :meth:`~opensubmitexec.job.Job.send_fail_result`
- Line 18: After a negative result is sent there is no need for traversing the rest of the test cases so the `validate(job)`-function can be left.
- Line 19: After the traversion of all test cases the student and teacher are informed that everything went well with :meth:`~opensubmitexec.job.Job.send_pass_result` 

The following example shows a validator for a C program that reads an positive integer from standard input und prints the corresponding binary number.

.. literalinclude:: files/validators/std_input/validator.py
    :linenos:

- Line 1: A `TimeoutException` is thrown when a program does not respond in the given time. The exception is needed for checking if the student program calculates fast enough.
- Line 3-9: In this case the test cases consist of the input strings and the corresponding output strings.
- Line 12: The method :meth:`~opensubmitexec.job.Job.run_build` is a combined call of `configure`, `make` and the compiler. The success of `make` and `configure` is optional. The default value for the compiler is GCC.
- Line 13: The test cases are traversed like in the previous example.
- Line 14: This time a program is spawned with :meth:`~opensubmitexec.job.Job.spawn_program`. This allows the interaction with the running program.
- Line 15: Standard input resp. keyboard input can be provided through the :meth:`~opensubmitexec.running.RunningProgram.sendline` method of the returned object from line 14.
- Line 17: The validator waits for the expected output with :meth:`~opensubmitexec.running.RunningProgram.expect`. If the program calculates longer then the specified timeout, it is terminated and a `TimeoutException` is thrown. If the program output is different from the expected output and the exception is not catched, a `TerminationException` exception would be thrown.
- Line 19: If a `TimeoutException` is thrown the corresponding negative result is sent explicitely.
- Line 20: The function can be left because there is no need for testing the other test cases.
- Line 22: After the program created an output, it is expected to terminate. The test script waits for this with :meth:`~opensubmitexec.running.RunningProgram.expect_end`
- Line 23: When the loop finishes, a positive result is sent to the student and teacher with :meth:`~opensubmitexec.job.Job.send_pass_result`.

The following example shows a validator for a C program that reads a string from standard input and prints it reversed. The students have to use for-loops for solving the task. Only the C file has to be submitted.

.. literalinclude:: files/validators/grep/validator.py
    :linenos:

- Line 1: A `TimeoutException` is thrown when a program does not respond in the given time. The exception is needed for checking if the student program calculates fast enough.
- Line 2: A `TerminationException` is thrown when a program terminates before delivering the expected output.
- Line 4-8: The test cases consist of the input strings and the corresponding reversed output strings.
- Line 11: The :meth:`~opensubmitexec.job.Job.grep` method searches the student files for the given pattern (e.g. a for-loop) and returns a list of the files containing it.
- Line 12-14: If there are not enough elements in the list, a negative result is sent with :meth:`~opensubmitexec.job.Job.send_fail_result` and the validation is ended.
- Line 16-24: For every test case a new program is spawned with :meth:`~opensubmitexec.job.Job.spawn_program`. The test script provides the neccessary input with :meth:`~opensubmitexec.running.RunningProgram.sendline` and waits for the expected output with :meth:`~opensubmitexec.running.RunningProgram.expect`. If the program is calculating for too long, a negative result is sent with :meth:`~opensubmitexec.job.Job.send_fail_result`.
- Line 25: If the result is different from the expected output a `TerminationException` is raised.
- Line 26-27: The corresponding negative result for a different output is sent with :meth:`~opensubmitexec.job.Job.send_fail_result` and the validation is cancelled.
- Line 28-29: If the program produced the expected output the validator waits  with :meth:`~opensubmitexec.running.RunningProgram.expect_end` until the spawned program ends.
- Line 30: If every test case was solved correctly, a positive result is sent with :meth:`~opensubmitexec.job.Job.send_pass_result`. 

Developer reference
*******************

The Job class summarizes all information about the submission to be validated by the test script. It also offers a set of helper functions that can be directly used by the test script implementation.

.. autoclass:: opensubmitexec.job.Job
    :members: 

Test scripts can interact with a running student program, to send some simulated keyboard input and check the resulting output for expected text patterns.

.. autoclass:: opensubmitexec.running.RunningProgram
    :members: 

