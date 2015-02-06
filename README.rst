The OpenSubmit project
======================

This is OpenSubmit, a small web application for managing student
assignment solutions in a university environment.

Other tools, such as Moodle, are more powerful and support not only
assignments, but also the management of learning material, course
progress and access rights. If you want the all-inclusive solution, this
is the wrong project.

OpenSubmit offers a trivial web page were *students can login and submit
their assignment solutions*. Teachers and their personal use the backend
interface to manage assignments, deadlines, and the gradings. Students
are informed about the progress of their correction and their final
grade via eMail and the frontend page.

The unique capability of OpenSubmit is the *support for coding
assignments*, were students upload their programming exercise solution
as source code archive. OpenSubmit offers a separate executor daemon,
which runs on another machine and downloads submitted solutions from the
web server. These archives are unpacked and tested for compilation, so
that non-compiling assignment solutions are rejected by the system
before the deadline. This makes the life of the corrector less
miserable, because after the deadline, all gradable solutions are
‘valid’ (e.g. compile). Students also seem to like the idea of having a
validated solution, so that they do not fail due to technical
difficulties at the correctors side.

Since OpenSubmit is only for assignment submission, it has no management
of course participants. Everybody who can perform a successful login can
submit solutions. We expect you to have an institute-specific OpenID
provider, otherwise you need to contribute your own patches for
authentication.

The end-user documentation is available in the GitHub Wiki.

Installation
------------

If you just want to install your own copy of OpenSubmit, please read the
installation guide in the GitHub Wiki.

License
-------

OpenSubmit is licensed under the AGPL Version 3. This means you are
allowed to:

-  Install and run the unmodified OpenSubmit code at your site.
-  Re-package and distribute the unmodified version of OpenSubmit from
   this repository.
-  Modify and re-publish (fork) the sources, as long as your modified
   versions are accessible for everybody.

In short, AGPL forbids you to distribute / run your own modified version
of OpenSubmit without publishing your code.

Acknowledgements
----------------

People who contributed to this project so far:

-  Kai Fabian (frontend, code evaluation)
-  Frank Feinbube (code evaluation backend, testing)
-  Bernhard Rabe (testing)
-  Peter Tröger (project owner)

