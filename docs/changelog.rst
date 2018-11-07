Changelog
#########

.. _v0.7.15:

v0.7.15 Release
===============

This is a stable release that brings the following updates:

- The configured site admin now automatically becomes an OpenSubmit admin on first login with a matching eMail address.

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

.. _v0.7.14:

v0.7.14 Release
===============

This is a stable release that brings the following updates:

- OpenSubmit now supports :ref:`GitLab authentication <gitlab>`.
- All login providers can now be restricted by providing a user whitelist. Please check the :ref:`configuration docs <config_web>` for details.
- There is a :ref:`new management command <troubleshooting>` that allows to check the run-time configuration of OpenSubmit, mainly for debugging purposes.
- The :ref:`administration docs <administrator>` docs are heavily extended and re-organized. 
- LTI credentials are now generated automatically. 
- There are now separate LTI links for each assignment, so that they can be directly integrated into your learning management system.
- When users access OpenSubmit through LTI, the optics now change accordingly. All interaction is reduced to a single view, so that submission creation, submission detail checking and withdrawal all happens under the same URL.

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

.. _v0.7.9:

v0.7.9 Release
==============

This is a stable release that brings :ref:`OpenID Connect support <oidc>` for the authentication. Thanks to :user:`tzwenn` for the contribution!

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

.. _v0.7.8:

v0.7.8 Release
==============

This is a stable release which adds support for compliance to the GDPR / DSGVO regulations in Europe.

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

Here is the list of changes since the last official release:

- OpenSubmit now provides an impress and a privacy policy page. Details about the configuration can be found in the `documentation <http://docs.open-submit.org/en/latest/administrator.html>`_.
- Script download was broken on the executors and is now fixed.
- The release changelog moved to the official documentation.

.. _v0.7.4:

v0.7.4 Release
==============

This is a stable release that only brings internal and administrative improvements, with no visible impact for end users.

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

Here is the list of changes:

- We now offer Docker images for the `web application <https://hub.docker.com/r/troeger/opensubmit-web/>`_ and the `executor <https://hub.docker.com/r/troeger/opensubmit-exec/>`_. The :ref:`administrator` was updated accordingly.
- We now offer a demo installation at http://www.demo.open-submit.org (:issue:`98`). This lead to a new configuration option called ``DEMO``, which allows to enable passthrough login buttons on the landing page.
- We now offer a `Terraform <http://terraform.io>`_-based installation of OpenSubmit on cloud computing resources. Check the :ref:`Terraform` section in the admin manual for further details.
- The traditional ``opensubmit-web configure`` call is now split up into three explicit commands:

  ``opensubmit-web configcreate``
      Creates a new config file for OpenSubmit. Supports several command-line options and environment variables for pre-defining configuration options, as described in the manual section about :ref:`config_web` (:issue:`238`).

  ``opensubmit-web apachecreate``
      Creates a new Apache configuration snippet, based on an existing OpenSubmit configuration.

  ``opensubmit-web configtest``
      Checks the current configuration for validity. Supposed to be called after updates.

- The new ``HOST_ALIASES`` configuration option allows you to set alternative host names for your OpenSubmit web machine. This makes sure that the CSRF protection does not prevent users from entering the site under a different name. 
- All views are now Django class-based views, which eases the future development and implicitely improves the catching of illegal HTTP requests (:issue:`233`).
- We switched to Django 1.11.
- We switched to a new LTI support library, which hopefully improves the compatibility to LMS systems. There is now also support for :ref:`automated LTI configuration <lti>`.

Make sure that you run ``opensubmit-web configtest`` resp. ``opensubmit-exec configtest`` after installation.

This release is compatible to executors from the v0.7 series.

Installation is possible with:

``pip install --upgrade opensubmit-web; opensubmit-web configtest; service apache2 restart``

``pip install --upgrade opensubmit-exec; opensubmit-exec configtest``


.. _v0.7.3:

v0.7.3 Release
==============

This is a stable release with some urgent patches and minor updates for the 0.7 series functionalities.

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

Here is the list of changes:

- The student frontend got a small design change (:issue:`219`). Withdrawn submissions are now collected on a separate page ("Archive"). The landing page provides three sections with open work (=open assignments the student can submit for), work in progress (=submissions under validation / grading) and finished work (=submissions that where graded, positively validated or where the deadline is over). This also allows to access assignments from the past, even when the deadline is over, as long as the course remains active. The student manual was updated accordingly.
- You can now send mails to a set of students (:issue:`123`) from the list of submissions.
- The grading table got more powerful, you can now enable / disable the assignments to be shown (:issue:`214`).
- Validation scripts can produce dedicated messages that are only visible to tutors. They are now also shown in the teacher backend (:issue:`213`).
- The documentation is now clearer about the Job.expect() interface and the role of TimeoutException.
- The link to the assignment download in the submission details is now fixed. It also shows more details with this update.
- Assignment lists in the teacher backend are now sorted.
- Error code generated by student programs are no longer modified, but reported as-is by the executors (:issue:`215`).
- The output of student programs was saved with double new-lines. This is fixed now (thanks to :user:`tttee`).
- The footer now links to the student / teacher manual page. The teacher backend link now only shows when the user has the according rights.
- The code base is now automatically checked for security bugs in the dependencies. Keyboard input created by the validation script is no longer double-echoed (:issue:`229`).
- We got a logo!

Make sure that you run ``opensubmit-web configure`` resp. ``opensubmit-exec configure`` after installation.

This release is compatible to executors from the v0.7 series.

Installation is possible with:

``pip install --upgrade opensubmit-web; opensubmit-web configure; service apache2 restart``

``pip install --upgrade opensubmit-exec; opensubmit-exec configure``

.. _v0.7.2:

v0.7.2 Release
==============

This is a stable release with some minor fixes.

If you upgrade from a v0.6.x release, make sure that you read the :ref:`v0.7.0 release notes <v0.7.0>`!

Here is the list of changes:

- Fixed a bug that prevented executors from removing their generated temporary files. (:issue:`210`)
- Executors now also stop working, with an error report for every tested submission, when they run out of disk space. (:issue:`208`)
- The file preview loads faster and shows line numbers. (:issue:`162`)
- Full tests can now only be started for submissions that are not already under test. (:issue:`211`)
- The configured maximum number of authors for an assignment is now checked in the student frontend (:issue:`205`) Thanks to :user:`tzwenn` for reporting this issue.
- The teacher manual now provides a lot more information and examples about writing validation test scripts (:issue:`207`, :issue:`209`).

Make sure that you run ``opensubmit-web configure`` resp. ``opensubmit-exec configure`` after installation.

This release is compatible to executors from the v0.7 series.

Installation is possible with:

``pip install --upgrade opensubmit-web; opensubmit-web configure; service apache2 restart``

``pip install --upgrade opensubmit-exec; opensubmit-exec configure``

.. _v0.7.0:

v0.7.0 Release
==============

After several months of beta testing, this is the largest release ever made for OpenSubmit.

There are two major changes that make this upgrade more important (and more painful) than the ones before:

- OpenSubmit no longer supports Python 2. You need Python 3.4 or newer, both on the web server and and test machines.

- The programming model for test scripts has changed in an incompatible way.

With this release, we also introduce the new home page at http://open-submit.org. It currently offers a set of (unfinished) manuals for students, course owners and administrators.

This update is the first major change, since 2012, in the way how test scripts are written. We hope that the new features and future possibilities are convincing enough for the additional upgrade efforts.

Thanks to :user:`tttee` and :user:`tzwenn` for contributing patches to this release.

Changes in comparison to v0.6.12
--------------------------------


- The web application (opensubmit_web) and the executor daemon (opensubmit_exec) are now written in Python 3. You need to adjust your web server configuration and, in case, your Virtualenv installation accordingly (see below).

- The separation between admin backend and teacher backend is gone (:issue:`179`). There is only a teacher backend now. Administrative actions are offered in the 'System' section of the teacher dashboard. Everbody, including the administrators, is therefore now forced to go through the student authentication page.

- Since admins have no longer a separate user name / password entry into the system, they need a different way to manage initial user permissions. This is realized with new features in the ``opensubmit-web`` command-line tool. It supports explicit role assignment (``make_student``, ``make_owner``, ``make_admin``), based on an user email address. As an alternative, these actions are also offered in the user section of the teacher backend. (:issue:`9`)

- The ``opensubmit-web`` tool now also has a ``create_demo`` command. It installs a set of dummy courses, dummy assignments and dummy users for quick testing.

- Assignments can now be non-graded, simply by not chosing a grading scheme in the assignment configuration. Assignments can now also be published without a deadline. Both things are indicated in the student dashboard, the ordering was adjusted accordingly. (:issue:`183`, :issue:`198`, :issue:`177`)

- Several list views in the teacher backend now have advanced sorting and search support.

- File names of student submissions are now kept. This ensures that Makefiles being provided by the validator package always work. (:issue:`149`)

- Test machines can now be disabled. This gives you an upgrade path when switching to v0.7-style test scripts - disable all test machines, exchange the test scripts in the assignments, and re-enable them.

- Student eMails are now more detailed. (:issue:`202`)

- Test machines now can have a human-readable name. If this is not given, than the old naming scheme applies (:issue:`201`).

- Assignment descriptions can now be uploaded to, and served by the OpenSubmit installation. You are still able to use an external link for the assignment description. (:issue:`172`, :issue:`174`)

Beside these changes, there were also several internal improvements:

- Since we switched to Python 3, all installation packages are now wheels.
- Since we switched to Python 3, all UTF-8 rendering issues are now solved (:issue:`182`, :issue:`184`).
- There is improved support for contributors by integrating Travis CI and Scrutinizer, by making PEP-8 a reality in many code parts, and by supporting Anaconda as default IDE.
- Due to the complete re-write of the executor code, the error reporting and internal logging is now much more detailed (:issue:`191`, :issue:`193`, :issue:`196`). The new executor checks by itself if it is still compatible to the contacted version of the OpenSubmit web application.
- OpenSubmit will now start to follow the PEP-440 version scheme. This allows us to release beta versions that are not installed during a regular upgrade procedure of your Python installation.
- Many little bugs were fixed (:issue:`181`, :issue:`185`, :issue:`186`, :issue:`197`, :issue:`203`, :issue:`200`, :issue:`199`, :issue:`180`, :issue:`190`).

The new test script format
--------------------------

The newly offered OpenSubmit manual is the central source of information for how to write a test script. Here is the short overview of differences for upgrading users:

- A validation test or full test script can now only be written in Python >=3.4. It contains a single function ``validate(job)`` that is called by the executor. It still must be named validator.py, but can be stored within an archive with additional support files.
- All information about the student submission is available in the provided ``Job`` object. Check the manual for more details. (:issue:`113`)
- The ``Job`` object also offers a set of convinience functions, such as searching for keywords in the submitted student files. Check the manual. (:issue:`6`, :issue:`124`)
- The result reported to the student is now sent explicitely by the test script, and no longer implicitely derived from the exit code of the script. If you forget to send a result in your validator, then every function run not throwing an exception is reported as success with a default message. Check the online examples.
- Calling ``configure``, ``make`` or the compiler is now an explicit activity in the test script. This reduces the amount of options for assignments in the web interface, and increases the flexibility on the testing side. It also leads to the fact that support files are no longer an extra thing, since they can be simply added to the test script archive (:issue:`189`). We hope that this fundamental architectural change, and the complete re-factoring of the code, helps to solve traditional problems with Windows-based test machines (e.g. :issue:`144`). This one is for you, :user:`thehappyhippo`.
- Based on the fantastic *pexpect* library, you can now interact with the running student application in your test script code. This includes the support for student applications that expect a TTY. Check the example.

There are updated online examples for test scripts in the new format. We are also still working on imroving the manual for teachers - stay tuned.

Upgrade hints
-------------

The upgrade from an existing v0.6.12 installation demands a little bit more effort. We recommend to follow this procedure:

- Make a database backup. Seriousely.
- Install Python 3.4 or better on your web server, including ``pip3`` for getting Python 3 packages.
- Make sure that your web server can run Python 3 code, f.e. by installing ``libapache2-mod-wsgi-py3``.
- Run ``pip3 install --upgrade opensubmit-web`` to fetch OpenSubmit into your Python 3 installation.
- Run ``opensubmit-web configure``, as usual. The configuration file format did not change, but there is a larger set of database migrations that must be executed for this release. The Apache 2.4 configuration is also re-generated in a format that fits to ``libapache2-mod-wsgi-py3``.
- Restart the web server.
- Go to the teacher backend and disable all test machines.
- Install Python 3.4 or better on your test machines, including ``pip3`` for getting Python 3 packages.
- Run ``pip3 install --upgrade opensubmit-exec`` to fetch OpenSubmit into your Python 3 installation.
- Run ``opensubmit-exec configure``, as usual. If you see strange error messages, try to delete ``/etc/opensubmit/executor.ini`` and re-run ``opensubmit-exec configure`` to create a new one. In case, adjust it accordingly.
- Start to port your test scripts to the new format, and upload them for your assignments.
- Re-enable the test machines and check if the validation works again.

This release is, obviously, only compatible to executors from the v0.7 series.

Releases before v0.7.0
======================

All release notes before v0.7.0 used to live on GitHub, and where accidentially deleted in February 2018. Don't play around with ``git tag -d`` ...
