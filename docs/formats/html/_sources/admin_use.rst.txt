Admin manual
############

Web server
**********

OpenSubmit runs with Python 3.4 or newer versions. For an installation, you need to follow these steps:
  
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

Updating an existing OpenSubmit web installation consists of the following steps:

- Run ``pip install --upgrade opensubmit-web`` as root or in a virtualenv environment. 
- Run ``opensubmit-web configure`` to perform neccessary database updates.
- Restart your web server.

.. _auth:

Authentication methods
======================

OpenSubmit supports different authentication methods, as described in the following sections. There is **no password login** support in OpenSubmit - authentication is always supposed to be handled by some third-party service.

If you need another authentication method for your institution, please `open an according issue <https://github.com/troeger/opensubmit/issues/new>`_.

Login with OpenID
-----------------

If you want to allow users to login with OpenID, you need to configure the following settings:

- ``LOGIN_OPENID: True``
- ``LOGIN_DESCRIPTION: <visible button title>``
- ``OPENID_PROVIDER: <provider URL>``

The standard OpenSubmit installation already contains an example setting for using StackExchange as OpenID provider.

Login with Shibboleth
---------------------

If you want to allow users to login with Shibboleth, you need to configure the following settings:

- ``LOGIN_SHIB: True``
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

- ``LOGIN_GOOGLE: True``
- ``LOGIN_GOOGLE_OAUTH_KEY: <OAuth key>``
- ``LOGIN_GOOGLE_OAUTH_SECRET: <OAuth secret>``

The standard OpenSubmit installation already contains a key/secret pair for development purposes. It only works for OpenSubmit installations operating on *http://localhost:8000*, so in a production environment, you need a new pair of OAuth key/secret for your server.

A new pair can be created in the `Google API Console <https://console.developers.google.com/apis/credentials>`_. The authorized forwarding URL should be ``<base url of your installation>/complete/google-oauth2/``.

You also need to `activate the Google+ API <https://console.developers.google.com/apis/api/plus.googleapis.com/overview>`_, so that OpenSubmit is able to fetch basic user information from Google.

Login with Twitter account
--------------------------

If you want to allow users to login with an Twitter account, you need to configure the following settings:

- ``LOGIN_TWITTER: True``
- ``LOGIN_TWITTER_OAUTH_KEY: <OAuth key>``
- ``LOGIN_TWITTER_OAUTH_SECRET: <OAuth secret>``

The standard OpenSubmit installation already contains a key/secret pair for development purposes. It only works for OpenSubmit installations operating on *http://localhost:8000*, so in a production environment, you need a new pair of OAuth key/secret for your server.

A new key / secret pair can be created in the `Twitter Application Management <https://apps.twitter.com/>`_.  The authorized forwarding URL should be ``<base url of your installation>/complete/twitter/``. We recommend to modify the application access to *Read only*, and to allow access to the email addresses. 

Login with GitHub account
-------------------------

If you want to allow users to login with an GitHub account, you need to configure the following settings:

- ``LOGIN_GITHUB: True``
- ``LOGIN_GITHUB_OAUTH_KEY: <OAuth key>``
- ``LOGIN_GITHUB_OAUTH_SECRET: <OAuth secret>``

The standard OpenSubmit installation already contains a key/secret pair for development purposes. It only works for OpenSubmit installations operating on *http://localhost:8000*, so in a production environment, you need a new pair of OAuth key/secret for your server.

A new key / secret pair can be created in the `OAuth application registration <https://github.com/settings/applications/new>`_.  The authorized forwarding URL should be ``<base url of your installation>/complete/github/``.

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

Test machines
*************

Test machines are used to run the validation scripts for student submission. These scripts use a specialized set of functions, the :ref:`validatorlibrary`. Pending validation jobs are fetched from the OpenSubmit web server in regular intervals and executed on a test machine.

The creator of an assignment can chose which test machines are used for the validation. This enables a flexible setup with dedicated test machines for special assignments, e.g. GPU programming.

Both the validator library and the job fetching is implemented in a Python package called ``opensubmit-exec`` (the *executor*). It runs with Python 3.4 or newer versions. For an installation, you need to follow these steps:
  
- Choose a dedicated machine with Python 3 beside the web server. It will compile (and run) the student submissions.
- Think again. IT WILL RUN THE STUDENT SUBMISSIONS. Perform all neccessary security precautions, such as network isolation and limited local rights.
- Run ``pip install opensubmit-exec`` as root or in a virtualenv environment. If you get error messages about unresolved dependencies, try running ``pip install -U opensubmit-exec``. PIP should come as part of your Python installation.
- Run ``opensubmit-exec configure`` and follow the instructions. Make sure that you adjust ``/etc/opensubmit/executor.ini`` accordingly after the first run. You can run the script multiple times to check your configuration.
- Add a call to ``opensubmit-exec run`` to cron, so that it regulary asks the web server for fresh work. We have good experiences with a 30s interval. You can also do it manually for testing purposes.

Smart students may try to connect to machines under their control in their code, mainly to copy tutor validation scripts. An easy prevention mechanism for that is the restriction of your test machine routing to the OpenSubmit web server only. 

The fetching of validations is protected by a shared secret between the web application and the executor installations. Check both the ``settings.ini`` on the web server, and ``executor.ini`` on the test machines.

Updating your installation
==========================

Updating an existing OpenSubmit executor installation consists of the following steps:

- Run ``pip install --upgrade opensubmit-exec`` as root or in a virtualenv environment. 
- Run ``opensubmit-exec configure`` to check the configuration for compatibility.

