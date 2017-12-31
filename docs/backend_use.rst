Teacher backend
###############

.. warning::

   This manual is work in progress and therefore incomplete. Feel free to help us with a `pull request on GitHub <https://github.com/troeger/opensubmit>`_.

OpenSubmit was invented for making assignments more fun for the students, and less work for the teachers. Before you start to read into details, we recommend to get into the basic :ref:`idea <index>` and general :ref:`principles <principles>`. 

Student tutors, course owners and administrators (see also :ref:`permissions`) all operate in the teacher backend, which is reachable by a link at the end of the OpenSubmit student frontend, or directly via *<your OpenSubmit url>/teacher*.

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

Assignments for students belong to a course. The registered students can choose (see also :ref:`usercourses`) which course they participate in. This is different to many other learning management systems, which offer sophisticated registration mechanisms (see also :ref:`principles`). 

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

Submission states
=================

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

The grading of student submissions follows the same workflow, regardless of the fact if you have code evaluation activated or not. 

Short version:

- For each submission:

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


Automated testing of submissions
********************************
.. _testing:

The automated testing of submissions is possible by writing a Python 3 script that is executed by OpenSubmit on the :ref:`test machines <executors>`. This script is developed by the assignment creator, in order to check the behavior or output of student code submissions for correctness. 

Since OpenSubmit makes no assumption about your style of student code evaluation, these scripts are rather generic. You can upload a validation test or full test in two ways:

- As single Python file named `validator.py`.
- As ZIP / TGZ archive with an arbitrary name, which must contain a file `validator.py`. This allows you to deploy custom validator support code (e.g. profiling tools, libraries) to the test machine. 

The test machine daemon makes sure that all test-related files are uncompressed in the same directory as the student code.

How to write a validator
========================

OpenSubmit is compatible to Python 3.4 or higher. Given the fact that :ref:`test machines <executors>` directly call the validator code,
these scripts must be written in the same language.

It is possible to install the OpenSubmit executor standalone. Similar to the installation of :ref:`test machines <executors>`, the following procedure (for Debian / Ubuntu systems) helps to get a testing environment:

- Install Python 3: ``sudo apt-get install python3 python3-pip``

To keep your Python installation clean, we recommend to use `Virtualenv <https://virtualenv.pypa.io/en/stable/>`_:

- Install the Virtualenv tool: ``sudo pip3 install virtualenv``
- Create a new virtual environment, e.g. in ``~/my_env``: ``python3 -m virtualenv ~/my_env``
- Activate it with ``source ~/my_env/bin/activate``
- Install the OpenSubmit validator library / executor inside: ``pip3 install opensubmit-exec``
- Do your work.
- Deactivate it with ``deactivate``

With a working installation of the OpenSubmit executor, it is now possible to develop validation scripts. Working demonstrators for different aspects can be found `online <https://github.com/troeger/opensubmit/tree/master/examples>`_.

We illustrate the idea with the following example:

The students have to create a program in C that prints 'Hello World' on the terminal. The assignment demands that they submit a C-file and a matching *Makefile* that creates a program called *hello*. The assignment description explains the students that they have to `submit a ZIP archive <_newsubmission>`_ containing both files.

Your job, as the assignment creator, is now to develop the ``validator.py`` file that checks an arbitrary student submission. Create a fresh directory that only contains an example student upload and the validator file:

.. literalinclude:: files/validators/helloworld/validator.py
   :linenos:

A ``validator.py`` file must contain a function ``validate(job)``, which is called when a student submission should be validated. In the example above, it performs the following steps:

- Line 1: The validator function is called when all student files (and all files from the validator archive) are unpacked in a temporary working directory on the test machine. In case of name conflicts, the validator files always overwrite the student files.
- Line 2: Run the *make* tool in the working directory. This step is declared to be mandatory, so `job.run_make` will throw an exception if *make* fails.
- Line 3: Run a binary called *hello* in the working directory. The result is the exit code and the output of the running program.
- Line 4: Check the generated output of the student program for some expected text.
- Line 5: Send a positive validation result back to the OpenSubmit web application. The text is the one shown to students and tutors.
- Line 6: Send a negative validation result back to the OpenSubmit web application. The text is the one shown to students and tutors.

Validator scripts are ordinary Python code, so beside the functionalities provided by the job object, you can use any Python functionality. The example shows that in Line 4. 

If any of the functions throws an exception that is not catched by your validator code, it is automatically interpreted as negative validation result. The OpenSubmit executor code then ensures that a generic information is provided to the student. If you want to customize the reporting in those cases, catch the exception and use your own call of `send_fail_result` instead.

To check if the validator is working correctly, you can run the command ``opensubmit-exec test <directory>``. It assumes the given directory to contain a validator script resp. archive and the student submission file resp. archive. The command simulates a complete validation run on a test machine and prints exhaustive debugging information. The last line contains the feedback sent to the web application after finalization.

Validator examples
==================

The following example shows a validator for a program in C that prints the sum of two integer values. Those values are given as command line arguments. If the wrong number of arguments is given it should print `"Wrong number of arguments!"`. The student only has to submit the C-file.

.. literalinclude:: files/validators/program_params/validator.py
    :linenos:

- Line 1: GCC specifies the compiler, which ist to be used for compiling the submitted C-file.
- Line 3-10: The variable `test_cases` consists of the lists of inputs and the corresponding expected outputs.
- Line 13: The C-file can be compiled directly by using `job.run_compiler`. You can specify the used compiler as well as the names of the input and output files.
- Line 14: The for-loop is used for traversing the `test_cases`-list. It consists of tuples which are composed of the arguments and the expected output.
- Line 15: The arguments can be handed over to the program through the second parameter of the `job.run_program` method. The former method returns the exit_code as well as the output of the program.
- Line 16: The if-statement checks if the created output equals the expected output.
- Line 17: If this is not the case an appropriate negative result is sent to the student and teacher.
- Line 18: After a negative result is sent there is no need for traversing the rest of the test cases so we can leave the `validate`-function.
- Line 19: After we traversed all test cases we can inform the student and teacher that everything went well. 

The following example shows a validator for a C program that reads an positive integer from standard input und prints the corresponding binary number.

.. literalinclude:: files/validators/std_input/validator.py
    :linenos:

- Line 1: A TimeoutException is thrown when a program does not respond in the given time. The exception is needed for checking if the student program calculates fast enough.
- Line 3-9: The test cases consist in this case of the input strings and the corresponding output strings.
- Line 12: The method `run_build` is a combined call of `configure`, `make` and the compiler. The success of `make` and `configure` is optional. The default value for the compiler is GCC.
- Line 13: The test cases are traversed like in the previous example.
- Line 14: This time a program is spawned. This allows us to use standard input.
- Line 15: Standard input is used through the `sendline`-method of the running object.
- Line 17: We wait for the expected output. If the program calculates longer the the specified timeout, it is closed and a `TimeoutException` is thrown. If the program output is different from the expected output a message containing the negative result is sent automatically.
- Line 19: If a `TimeoutException` is thrown the corresponding negative result is sent.
- Line 20: The function can be left because there is no need for testing the other test cases.
- Line 22: After the program created an output it is expected to end.
- Line 23: When the loop finishes a positive result is sent to student and teacher.

Job reference
=============

.. autoclass:: opensubmitexec.server.Job
    :members: 