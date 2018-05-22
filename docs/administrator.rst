.. _administrator:

Administrator Manual
####################

OpenSubmit consists of two parts: The web application and the executor daemon. The web application provides the user interface for students and teachers, while the executor daemons evaluate student code with according test scripts.

.. image:: files/architecture.png    

If you just want to play around, use our `demo installation <http://www.demo.open-submit.org>`_.

If you want your own production setup, go the manual way for :ref:`web application <manualweb>` and :ref:`test machines <manualexec>`.

Please note that OpenSubmit :ref:`does not support password-based login <principles>`. You need to work with one of the supported :ref:`auth`.

.. _terraform:

Full-stack installation with Terraform
**************************************

The source code repository offers a  `Terraform <http://terraform.io>`_ script for deploying a complete OpenSubmit environment on a single machine running in the `Google Compute Engine <https://cloud.google.com/compute>`_. The installation procedure deploys the Docker containers described in the following sections. For such an installation:

- Install `Terraform <http://terraform.io>`_ on your local machine.
- Clone the Git repository for OpenSubmit and adjust the variables in `terraform.tf <https://github.com/troeger/opensubmit/blob/master/terraform.tf>`_.
- Call ``terraform apply``.

This setup is not recommended for production, since the database is installed as Docker image. 

Full-stack installation with Docker Compose
*******************************************

You can replicate our `demo installation <http://www.demo.open-submit.org>`_ on your own machine with `Docker Compose <https://docs.docker.com/compose/overview/>`_, which comes as part of a normal `Docker installation <https://www.docker.com/community-edition#/download>`_. Our compose file relies on the official Docker images for the `web application <https://hub.docker.com/r/troeger/opensubmit-web/>`_ and the `executor <https://hub.docker.com/r/troeger/opensubmit-exec/>`_.

- Download the `compose file <https://raw.githubusercontent.com/troeger/opensubmit/master/docker-compose.yml>`_ on the machine.
- Call ``docker-compose up`` to download, configure and start the OpenSubmit Docker containers and a separate database container.
- Got to ``http://localhost:8000`` and use one of the configured authentication methods.

This setup is not recommended for production, since the database is installed as Docker image. 

Single installation of the web application
******************************************

The OpenSubmit web application runs with Python 3.4 or newer versions. There are two options:

.. _dockerweb:

Docker-based installation
=========================

The latest official release of the OpenSubmit web application is available as single `opensubmit-web Docker image <https://hub.docker.com/r/troeger/opensubmit-web/>`_. It expects a couple of environment variables to be set, check the :ref:`configuration section <config_web>` for further details.

.. _manualweb:

Manual installation
===================

This is the recommended approach for production environments. You need to follow these steps:
  
- Prepare a Python 3 web hosting environment. 

  - Debian / Ubuntu: ``apt-get install libapache2-mod-wsgi-py3 apache2 sqlite python3``. 

- Run ``pip install opensubmit-web`` as root or in a virtualenv environment. If you get error messages about unresolved dependencies, try running ``pip install -U opensubmit-web``. PIP should come as part of your Python installation.
- Run ``opensubmit-web configcreate`` to create an OpenSubmit configuration file. Check the :ref:`configuration section <config_web>` for details.  
- Run ``opensubmit-web configtest`` to check your configuration.
- Run ``opensubmit-web apachecreate`` to generate a default Apache 2.4 configuration for mod_wsgi, which is stored in ``/etc/opensubmit/apache24.config``.  You can `include <http://httpd.apache.org/docs/2.4/en/mod/core.html#include>`_ this file in some `virtual host configuration <http://httpd.apache.org/docs/2.4/vhosts/examples.html>`_.
- Restart your web server.
- Got to the OpenSubmit start page and use your configured authentication method.
- Run ``opensubmit-web makeadmin <email>`` to make the created user an administrator in the system.

Updating an existing manual installation is easy:

- Run ``pip install --upgrade opensubmit-web`` as root or in the virtualenv environment. 
- Run ``opensubmit-web configtest`` to perform neccessary database updates.
- Restart your web server.


.. _config_web:

Configuration of the web application
====================================

OpenSubmit searches for a configuration file in ``/etc/opensubmit/settings.ini``. This file should be initially created by calling ``opensubmit-web configcreate``. This management command allows to pre-define specific configuration options via command-line or environment variables, and creates an according config file. Check ``opensubmit-web configcreate -h`` for details.

Impress and privacy policy
--------------------------

There are several European regulations that expect a web page to provide both an impress and a privacy policy page (GDPR / DSGVO). There are two ways to achieve that:

- Option 1: Your configuration file defines name, address, and email of an administrator. The according options for ``opensubmit-web configcreate`` are ``--admin_name``, ``--admin_email``, and ``--admin_address``. If you want to modify settings.ini directly, add ``ADMIN_NAME``, `ÀDMIN_EMAIL`` and ``ADMIN_ADDRESS`` in the ``[admin]`` section. The first two settings are mandatory anyway. Given that information, OpenSubmit will provide a default impress and privacy policy page.

- Option 2: Your configuration file defines alternative URLs for impress page and privacy policy page. The according options for ``opensubmit-web configcreate`` are ``--admin_impress_page`` and ``--admin_privacy_page``.  If you want to modify settings.ini directly, add ``IMPRESS_PAGE`` and `PRIVACY_PAGE`` options with the links in the ``[admin]`` section.

.. _auth:

Authentication methods
======================

OpenSubmit supports different authentication methods, as described in the following sections. It :ref:`does not support password-based logins <principles>` - authentication is always supposed to be handled by some third-party service.

If you need another authentication method for your institution, please `open an according issue <https://github.com/troeger/opensubmit/issues/new>`_.

Authentication methods show up on the front page when the according settings are not empty. You can therefore disable any of the mechanisms by commenting them out in settings.ini.

Login with OpenID
-----------------

If you want to allow users to login with OpenID, you need to configure the following settings:

- ``LOGIN_DESCRIPTION: <visible button title>``
- ``OPENID_PROVIDER: <provider URL>``

The standard OpenSubmit installation already contains an example setting for using StackExchange as OpenID provider.

Login with Shibboleth
---------------------

If you want to allow users to login with Shibboleth, you need to configure the following settings:

- ``LOGIN_SHIB_DESCRIPTION: <visible button title>``

You also need a fully working installation of the `Apache 2.4 mod_shib <https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPApacheConfig>`_ module. The authentication module of OpenSubmit assumes that, as result of the work of *mod_shib*, the following environment variables are given:

- ``REMOTE_USER``: The user name of the authenticated user.
- ``HTTP_SHIB_ORGPERSON_EMAILADDRESS``: The email address of the authenticated user.
- ``HTTP_SHIB_INETORGPERSON_GIVENNAME``: The first name of the authenticated user.
- ``HTTP_SHIB_PERSON_SURNAME``: The last name of the authenticated user.

Note: If you are using Apache 2.4 with *mod_wsgi*, make sure to set ``WSGIPassAuthorization On``. Otherwise, these environment variables may not pass through.

Login with Google account
-------------------------

If you want to allow users to login with an Google account, you need to configure the following settings:

- ``LOGIN_GOOGLE_OAUTH_KEY: <OAuth key>``
- ``LOGIN_GOOGLE_OAUTH_SECRET: <OAuth secret>``

A new pair can be created in the `Google API Console <https://console.developers.google.com/apis/credentials>`_. The authorized forwarding URL should be ``<base url of your installation>/complete/google-oauth2/``.

You also need to `activate the Google+ API <https://console.developers.google.com/apis/api/plus.googleapis.com/overview>`_, so that OpenSubmit is able to fetch basic user information from Google.

Login with Twitter account
--------------------------

If you want to allow users to login with an Twitter account, you need to configure the following settings:

- ``LOGIN_TWITTER_OAUTH_KEY: <OAuth key>``
- ``LOGIN_TWITTER_OAUTH_SECRET: <OAuth secret>``

A new key / secret pair can be created in the `Twitter Application Management <https://apps.twitter.com/>`_.  The authorized forwarding URL should be ``<base url of your installation>/complete/twitter/``. We recommend to modify the application access to *Read only*, and to allow access to the email addresses. 

Login with GitHub account
-------------------------

If you want to allow users to login with an GitHub account, you need to configure the following settings:

- ``LOGIN_GITHUB_OAUTH_KEY: <OAuth key>``
- ``LOGIN_GITHUB_OAUTH_SECRET: <OAuth secret>``

A new key / secret pair can be created in the `OAuth application registration <https://github.com/settings/applications/new>`_.  The authorized forwarding URL should be ``<base url of your installation>/complete/github/``.


.. _useroverview:

User management
===============

One of the core concepts of OpenSubmit is that users register themselves by using an external authentication provider (see :ref:`auth`). 

Based on this, there are different groups such a registered user can belong to:

- *Students* (default): Users who cannot access the teacher backend.  
- *Student Tutors*: Users with limited rights in the teacher backend.
- *Course Owners*: Users with advanced rights in the teacher backend.
- *Administrators*: Users will unrestricted rights.

.. _permissions:

Permissions
-----------

The following table summarized the default permissions for each of the user groups.

================================ ======== ================ ================ ===============
Permission                       Students  Student Tutors  Course Owners    Administrators
================================ ======== ================ ================ ===============
Student Frontend                  Yes         Yes            Yes                Yes
- Create submissions              Yes         Yes            Yes                Yes
- Withdraw submission             Yes         Yes            Yes                Yes
- See unpublished assignments      No         Yes            Yes                Yes
Teacher Backend                    No         Yes            Yes                Yes
- eMail to participants            No         Yes [1]_       Yes [2]_           Yes [2]_
- Manage/grade submissions         No         Yes [1]_       Yes [2]_           Yes [2]_
- Manage assignments               No          No            Yes [2]_           Yes [2]_
- Manage grading schemes           No          No            Yes                Yes
- Manage study programs            No          No            Yes                Yes
- Manage courses                   No          No            Yes                Yes
- Manage users                     No          No             No                Yes
- Manage test machines             No          No             No                Yes
- Manage custom permissions        No          No             No                Yes 
================================ ======== ================ ================ ===============

.. rubric:: Footnotes

.. [1] Only for courses where the user was chosen as tutor.
.. [2] Only for courses where the user was chosen as tutor or course owner.

Administrators can create custom user groups and permissions. Normally this should be avoided, since some permissions have a non-obvious impact on the usage of the teacher backend.

Assigning users to groups
-------------------------

There are two ways to assign users to user groups, assuming that they logged-in once for registration:

- In the teacher backend, as administrator (see :ref:`auth`).
- With the ``opensubmit-web`` command-line tool.

The first option is the web-based configuration of user groups, which is only available for administrators. Click on *Manage users* and mark all user accounts to be modified. After that, choose an according action in the lower left corner of the screen.

The second option is the ``opensubmit-web`` command-line tool that is available on the web server. Calling it without arguments shows the different options to assign users to user groups.

.. _merge users:

Merging accounts
----------------

Since OpenSubmit users always register themselves in the platform (see :ref:`auth`), it can happen that the same physical person creates multiple accounts through different authentication providers. The main reason for that is a non-matching or missing email address being provided by the authentication provider.

Administrators can merge users in the teacher backend. Click on *Manage users*, mark all user accounts to be merged, and choose the according action in the lower left corner. The nect screen shows you the intended merging activity and allows to chose the "primary" account by flipping roles. The non-primary account is deleted as part of the merging activity.

.. _executors:

Single installation of a test machine
*************************************

Test machines are used to run the validation scripts (see :ref:`testing`) for student submission. Pending validation jobs are fetched from the OpenSubmit web server in regular intervals and executed on a test machine.

The creator of an assignment can chose which test machines are used for the validation. This enables a flexible setup with dedicated test machines for special assignments, e.g. GPU programming.

There are two options for installation:

Docker-based installation
=========================

The latest official release of the OpenSubmit executor application is available as `opensubmit-exec Docker image <https://hub.docker.com/r/troeger/opensubmit-exec/>`_. It expects a couple of environment variables to be set, check the :ref:`configuration section <config_exec>` for details.

.. _manualexec:

Manual installation
===================

Both the validator library and the job fetching is implemented in a Python package called ``opensubmit-exec`` (the *executor*). It runs with Python 3.4 or newer versions. For an installation, you need to follow these steps:
  
- Choose a dedicated machine beside the web server. It will compile (and run) the student submissions.
- Think again. IT WILL RUN THE STUDENT SUBMISSIONS. Perform all neccessary security precautions, such as network isolation and limited local rights.
- Install Python >= 3.4 on the machine. e.g. through ``sudo apt-get install python3 python3-pip``.
- Run ``pip3 install opensubmit-exec`` as root or in a virtualenv environment. If you get error messages about unresolved dependencies, try running ``pip install -U opensubmit-exec``. PIP should come as part of your Python installation.
- Create an initial configuration as described in the :ref:`configuration section <config_exec>`.
- Run ``opensubmit-exec configtest`` to check your configuration.
- Add a call to ``opensubmit-exec run`` to cron, so that it regulary asks the web server for fresh work. We have good experiences with a 30s interval. You can also do it manually for testing purposes.

Smart students may try to connect to machines under their control in their code, mainly for copying validation scripts. An easy prevention mechanism is the restriction of your test machine network routing so that it can talk to the web server only.

The fetching of validations is protected by a shared secret between the web application and the executor installations. Check both the ``settings.ini`` on the web server and ``executor.ini`` on the test machines.

Updating an existing manual executor installation consists of the following steps:

- Run ``pip install --upgrade opensubmit-exec`` as root or in a virtualenv environment. 
- Run ``opensubmit-exec configtest`` to check the configuration for compatibility.

.. _config_exec:

Configuration of the executor
=============================

OpenSubmit searches for a configuration file in ``/etc/opensubmit/executor.ini``. This file should be initially created by calling ``opensubmit-exec configcreate``. This management command allows to pre-define specific configuration options via command-line or environment variables, and creates an according config file. Check ``opensubmit-exec configcreate -h`` for details.
