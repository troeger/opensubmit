:orphan:

About
=====

The development of OpenSubmit is coordinated on `GitHub <https://github.com/troeger/opensubmit>`_.
We need help in everything. Feel free to join us.

.. _principles:

The Zen of OpenSubmit 
*********************

Following an old `tradition <https://www.python.org/dev/peps/pep-0020/>`_, there 
is a set of guiding principles for the design of OpenSubmit:

Minimalism is good.
    OpenSubmit follows the philosophy that teachers know the best how their teaching works.
    This leads to the conclusion that teaching policies and workflows do not belong into
    code or complicated configuration options. Assignment rules vary widely in different
    institutions and groups. Given that,
    it is a main philosophy of OpenSubmit to reduce the functionality 
    to the submission and validation of of student submissions. And nothing else. This
    simplifies the student user interface and clarifies the teacher workflow.

Passwords are bad. 
    History has shown that `even the largest companies <https://haveibeenpwned.com/>`_
    fail at implementing a secure password
    authentication mechanism. Doing this properly includes captcha management, email 
    roundtrips, recovery procedures, two-factor magic, identity checks, permanent software updates,
    and solid basic crypto knowledge. There are better ways to spend our restricted resources.
    OpenSubmit therefore does not have a password-based authentication mechanism.
    Instead, we support the authentication through third-party services.
    Since every eductional institution already has an existing scheme for that, we focus on
    integrating them properly instead.

Machines don't grade. Humans do.
    Even though OpenSubmit is focusing on the automated validation of student submissions,
    we do not aim for automated grading. These ideas became popular in the context
    of `MOOCs <https://en.wikipedia.org/wiki/Massive_open_online_course>`_,
    but cannot work in an educational environment where the future of humans depends
    on the certificates they get. OpenSubmit is therefore focusing on supporting teachers in their
    grading in every possible way, so that bulk activities (grading teams, duplicate checks a.s.o) 
    becomes a fast and painless activity.

Students are too creative.
    OpenSubmit is intended to deal with the fact that student are extremely creative in what they
    submit as solution. Especially with code. The tool should be the forgiving middleman that translates the
    arbitrary student package into something that can be graded fast and easily.       

If you are interested in the why's and how's of these principles, check our (slightly outdated)
:download:`presentation <files/clt16-presentation.pdf>` from LinuxTage 2016.

License
*******

OpenSubmit is licensed under the AGPL Version 3. This means you are
allowed to:

-  Install and run the unmodified OpenSubmit code at your site.
-  Re-package and distribute the unmodified version of OpenSubmit.
-  Modify and re-publish (fork) the sources, as long as your modified
   versions are accessible for everybody.

In short, AGPL forbids you to distribute / run your own modified version
of OpenSubmit without publishing your changes. This does not relate to configuration files.

Acknowledgements
****************

People who contributed to this project so far:

-  Jafar Akhundov (testing)
-  Kai Fabian (frontend, code evaluation)
-  Frank Feinbube (code evaluation backend, testing)
-  Jens Pönisch (testing)
-  Bernhard Rabe (testing)
-  Peter Tröger (project owner)
-  Matthias Werner (testing)


