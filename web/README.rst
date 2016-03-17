The OpenSubmit web application
==============================

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
as source code archive. OpenSubmit offers an executor daemon that runs 
on another machine and downloads submitted solutions from the
web server. You can install it with the *opensubmit-exec* package.

Since OpenSubmit is only for assignment submission, it has no management
of course participants. Everybody who can perform a successful login can
submit solutions. Therefore, we expect you to have an institute-specific 
authentication provider. OpenSubmit currently supports OpenID and Shibboleth
out of the box for such cases. You can also offer GitHub, Twitter or Google login
for determining the student identity.

The `end-user documentation`_ is available in the GitHub Wiki.

.. _end-user documentation: https://github.com/troeger/opensubmit/wiki/User-Manual

There is also an `installation guide`_ in the GitHub Wiki.

.. _installation guide: https://github.com/troeger/opensubmit/wiki/Installation-Instructions

License
-------

OpenSubmit is licensed under the AGPL Version 3. This means you are
allowed to:

-  Install and run the unmodified OpenSubmit code at your site.
-  Re-package and distribute the unmodified version of OpenSubmit.
-  Modify and re-publish (fork) the sources, as long as your modified
   versions are accessible for everybody.

In short, AGPL forbids you to distribute / run your own modified version
of OpenSubmit without publishing your code.
