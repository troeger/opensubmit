Admin manual
############

.. warning::

   This manual is work in progress and therefore incomplete. Feel free to help us with a `pull request on GitHub <https://github.com/troeger/opensubmit>`_.

Web application
***************

OpenSubmit runs with Python 3.5 or newer versions. For an installation, you need to follow these steps:
  
- Prepare a Python 3 web hosting environment. 

  - Debian / Ubuntu: ``apt-get install libapache2-mod-wsgi-py3 apache2 sqlite python3``. 

- Run ``pip install opensubmit-web`` as root or in a virtualenv environment. If you get error messages about unresolved dependencies, try running ``pip install -U opensubmit-web``. PIP should come as part of your Python installation.
- Run ``opensubmit-web configure`` to create an OpenSubmit configuration file template. Edit the generated file (``/etc/opensubmit/settings.ini``):

  - The default database is SQLite. You can use an empty MySQL, PostgreSQL or Oracle database instead.
  - OpenSubmit does not support password-based logins. You need to choose one of the supported :ref:`authentication methods <auth>`.
  - Configure a MEDIA_ROOT folder that stores all the student uploads.

- Re-run ``opensubmit-web configure`` to check your configuration. If everything looks good, then a default Apache 2.4 configuration for mod_wsgi is generated in ``/etc/opensubmit/apache24.config``.  You can `include <http://httpd.apache.org/docs/2.4/en/mod/core.html#include>`_ this file in some `virtual host configuration <http://httpd.apache.org/docs/2.4/vhosts/examples.html>`_. 
- Restart your web server.
- Got to the OpenSubmit start page and use your configured authentication method.
- Run ``opensubmit-web makeadmin <email>`` to make the created user an administrator in the system.

Updating your installation
==========================

Authentication methods
======================
.. _auth:

User management
===============


User permissions
----------------
.. _permissions:


Merging accounts
----------------
.. _merge users:



Test machines
*************
.. _executors:

- Choose a dedicated machine beside the web server. This will compile (and run) the student submissions.
- Think again. IT WILL RUN THE STUDENT SUBMISSIONS. Perform all neccessary security precautions, such as network isolation and limited local rights.
- Run ``pip install opensubmit-exec`` as root or in a virtualenv environment. If you get error messages about unresolved dependencies, try running ``pip install -U opensubmit-exec``.
- Run ``opensubmit-exec configure`` and follow the instructions. Make sure that you adjust ``/etc/opensubmit/executor.ini`` accordingly. You can run the script multiple times to check your configuration.
- Add a call to ``opensubmit-exec run`` to cron, so that it regulary asks the web server for fresh work. We have good experiences with a 30s interval. You can also do it manually for testing purposes.

Smart students may try to connect to their own machines from their code, mainly to copy tutor validation scripts. An easy prevention mechanism for that is the restriction of your test machine routing to the OpenSubmit web server only. 

Updating your installation
==========================


