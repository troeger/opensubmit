The Submit project
==================

This is Submit, a small web application for managing student assignment solutions in a university environment.

Other tools, such as Moodle, are more powerful and support assignments, the management of learning material, course progress organization and access management at the same time. If you want the all-inclusive solution, this is the wrong project.

Submit offers a trivial web page were students can login and submit their assignment solutions. Teachers and their personal use the backend interface to manage the list of available assignments, deadlines, and the gradings. Students are informed about the progress of their correction and their final grade via eMail and the frontend page.

The unique capability of Submit is the support for coding assignments, were students upload their programming excercise solution as source code archive. Submit offers a separate executor daemon, which runs on another machine and downloads submitted solutions from the web server. These archives are unpacked and tested for compilation,  so that non-compiling assignment solutions are rejected by the system before the deadline. This makes the life of the corrector less miserable, because at the point of the assignment deadline, all gradable solutions are 'valid' (e.g. compile). Students also seem to like the idea of having a validated solution, so that they do not fail due to technical difficulties at the correctors side.

Since Submit is only for assignment submission, it has no management of course participants. Everbody who can perform a successful login can submit solutions. We expect you to have an institute-specific OpenID provider, otherwise you need to contributre your own patches.

Installation of the web application
-----------------------------------

- Download the source code distribution of the web application.
- Unpack it somehwere in a folder that your web server can access.
- Run "pip install -r requirements.txt".
- Copy settings.ini.template to /etc/submit/settings.ini and edit it according to your local needs. 
- Run "manage.py syncdb" and "manage.py migrate" to create / update the configured database. On creation,
  this will also establish an administrator account.
- Configure your web server to serve Submit as WSGI application. Typically, we would expect some snippet like this inside a VirtualHost definition:

	    WSGIScriptAlias /submit <src_dir>/submit/wsgi.py
    	WSGIDaemonProcess submit
    	WSGIProcessGroup  submit
    	Alias /submit/static/admin /usr/local/lib/python2.6/dist-packages/Django-1.4.2-py2.6.egg/django/contrib/admin/static/admin
    	Alias /submit/static       <src_dir>/submit/static

- Perform a login into the teacher backend. Create some teacher accounts with "staff status" and according roles. Student logins are created automatically by the OpenID login functionality.

Submit runs happily without code validation as simple assignment submission tool. 

Installation of code executor
------------------------------

- Download the source code distribution of the executor application.
- Choose a dedicated machine beside the web server. This will compile (and run) the student submissions.
- Install the script from '/jobexec' there.
- Think again. IT WILL RUN THE STUDENT SUBMISSIONS. Perform all neccessary security precautions, such as network isolation and limited local rights.
- Adjust executor.cfg according to your needs.
- Add executor.py to cron, so that it regulary asks the web server for fresh work.

Managing security
-----------------
The application relies on a combination of users roles and course-specific settings. Please consider carefully who you give which permissions, especially when students are involved.

If you want to enable a teacher or teaching assistant to access the backend, you need to enable the "Staff status" flag for this user. Otherwise, he/she has no chance to enter the teacher backend at all.

The next step is to assign the user to a general backend user group, regardless of the specific course or assignment. If you ommit that, than the backend is empty for him.

There are only two pre-defined groups, namely "Course Owners" and "Student Tutors". Course owners can do nasty things, such as re-defining grading schemes and modifying assignments. You typically never want a student to have these rights, even though he might act as corrector for you. "Student tutors" only have the generic right to edit submissions, especially for grading.

If you finished the role assignment, then it is time to create a course. For each course, you specify the owner and the list of tutors in terms of existing system users. Only after this step, the users can see something useful in their backend.

In summary: Student tutors need to be in the "Student Tutors" group and must be configured as tutor for a specific course. Faculty must be in the "Course Owners" group and must be configured as owner for a specific course.

Security is complicated. 

Creating an assignment
----------------------
- Make sure you have an existing course that you own.
- Make sure you have a grading scheme for your course.
- Create an assignment for a course and grading scheme.

