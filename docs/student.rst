Students Manual
###############

Welcome!

Your course responsible decided that it might be a good idea to manage the course assignments in OpenSubmit. This manual gives you a short introduction into the system, although most parts should be self-explanatory.

The most common use case for OpenSubmit are programming assignments, where your submitted solution is compiled and initially validated on dedicated test machines. In the further manual, we refer to this feature as `validation`.

The final grading of your solution is always done by humans. Validation just helps you and the correctors to have a working and gradable solution being submitted before the deadline.

Login
*****

The URL of the OpenSubmit installation was announced by your course responsible. Depending on the configuration, you see one or more options for login. After that, you see the student dashboard.

Please note first the menu at the top of the window. It allows you to:

* See a list of withdrawn solutions in the archive.
* Activate the courses you are interested in.
* Adjust your user settings.

.. _userdetails:

Setting your user details
=========================

Depending on the login method, some of your user details might be initially missing. This relates especially to your student ID and the study program you are in. 

Since you are (hopefully) interested in not getting the grade of another person, it is highly recommended to fill out the missing fields after the first login. Click on `Settings` in the upper right corner to fix your user details.

The eMail address has a special relevance. When your submitted results are validated or graded, you are informed by eMail about the results. When your OpenSubmit installation offers multiple login methods, it is also used the match accounts to each other. 

.. _usercourses:

Choosing your courses
=====================

After your first login into the system, you might not see any open assignments, although they are already published. This is reasoned by the fact that you need to *activate* the according courses in OpenSubmit. Click on `Courses` in the upper right corner of the dashboard and choose them accordingly.

Activating and deactivating courses does not impact the status of your past and current submissions in the system.

Courses and the related assignments may disappear from your dashboard when the course owner disables them, f.e. at the end of the semester.


Dashboard
*********

.. image:: files/ui_student.png    

The dashboard is your central starting point for working with assignments in OpenSubmit. It is divided into three major sections:

Open
    Assignments that you can submit solutions for.

In progress
    Solutions that are currently validated or graded.

Finished
    Past solutions and assignments.

.. _newsubmission:

Open assignments
================

The list of open assignments shows all relevant information that you need:

Course
    A link to more information about the course were this assignment is offered. 

Assignment
    A link to the assignment description.

Deadline
    The deadline for this assignment. When the deadline has passed, you can no longer submit a new solution.

Group Work
    The information if the submission of a single solution as group work is allowed, with the maximum number of authors in brackets. One student of the group is submitting the solution and specifies the other group members. OpenSubmit allows you to change your student group for every assignment, although this might not be allowed in your course. Check the assignment description. All group members have the same rights for the submission: Seing the status, getting notification mails, and withdrawing it before the deadline.

Graded
    The information if this is a graded assignment.

The `New Submission` button brings you to a separate screen where you can upload your assignment solution, either for yourself or your group of students.

The `Notes` fields allows you to drop additional information that is shown to the correctors.

Some assignments may expected the upload of a file. Please check your assignment description for the specific rules. Normally, this should be either a single file (source code, PDF file, DOCX file, image, ...) or a ZIP / TGZ archive of multiple files. 

In Progress
===========

Every uploaded file or archive is shown in the list of  submissions that are *in progress*. Their assignments are then no longer shown in the list of open assignments.

The state of a submission in progress may be:

Waiting for grading
    Your solution is waiting for being graded by a human.

Waiting for validation test
    Your solution is queued for automated validation on a test machine.

Validation failed
    The automated validation failed. You need to act before the deadline.

You get an eMail when the state of your active submission changes, so you don't need to check the web pages all the time.

The *Details* button brings you to a separate page with all the neccessary information about your submission. It includes all information visible for the correctors (notes, uploaded file, declared authors), the results of the automated validation on the test machine, and eventually your final grade for this assignment.

When the assignment has a deadline, you are free to withdraw your submitted solution *as often as you want* before the deadline. The idea here is that you can use the automated validation in a trial-and-error fashion. 

Withdrawn submissions are not considered for grading. They are still listed on the `Archive` page so that you can access your earlier attempts.

Finished
========

This section shows you finished work that no longer needs your active participation. This includes:

* Submission that were successfully validated and graded.
* Submissions for non-graded assignments that were successfully validated.
* Assignments for which you never submitted a valid solution.


Test Machines
=============

The validation of student submissions is performed on dedicated test machines. For programming assignments, it is often needed to get specific technical details about the target machine. This information is summarized in the `Test Machines` section on the Dashboard.

