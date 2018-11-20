.. _administrator:

Administrator Manual
####################

OpenSubmit consists of two parts: The web application and the executor daemon. The web application provides the user interface for students and teachers, while the executor daemons evaluate student code with according test scripts.

.. image:: files/architecture.png    

If you just want to play around, use our `demo installation <http://www.demo.open-submit.org>`_.

Please note that OpenSubmit :ref:`does not support password-based login <principles>`. You need to work with one of the supported :ref:`auth`.

Full-stack installation with Docker Compose
*******************************************

We offer a `Docker Compose <https://docs.docker.com/compose/overview/>`_ script for deploying a complete OpenSubmit environment (web frontend, test machine, database) on a single machine running a normal `Docker installation <https://www.docker.com/community-edition#/download>`_. For such an installation:

- Download the `compose file <https://raw.githubusercontent.com/troeger/opensubmit/master/deployment/docker-compose.yml>`_ on the machine. One way to do that is: ``curl -o docker-compose.yml https://raw.githubusercontent.com/troeger/opensubmit/master/deployment/docker-compose.yml``.
- Call ``docker-compose up`` to download, configure and start the OpenSubmit Docker containers and a separate database container.
- Got to ``http://localhost:8000`` and use one of the authentication methods.

If you want to adjust things such as the allowed login methods, just edit the ``docker-compose.yml`` file and modify the environment variables for the ``web`` container. The list of options can be found :ref:`below <configtable>`.

Please note also that running a database inside a Docker container might not be the smartest idea. You can easily adjust the web container configuration and use an external database instead.

.. _Terraform:

Full-stack installation with Terraform
**************************************

We offer a  `Terraform <http://terraform.io>`__ script for deploying a complete OpenSubmit environment (web frontend, test machine, database) on a single machine running on the `Google Cloud <https://cloud.google.com/compute>`_. For such an installation:

- Install `Terraform <http://terraform.io>`__ on your local machine.
- Clone the Git repository for OpenSubmit and adjust the variables in `terraform.tf <https://github.com/troeger/opensubmit/blob/master/terraform.tf>`_.
- Call ``terraform apply``.


Single installation of the web application
******************************************

For the OpenSubmit web application alone, there are two options to run it:

.. _dockerweb:

Docker-based installation
=========================

The latest official release of the OpenSubmit web application is available as `Docker image <https://hub.docker.com/r/troeger/opensubmit-web/>`__. It expects a couple of environment variables to be set, which you can easily determine from the `compose file <https://raw.githubusercontent.com/troeger/opensubmit/master/deployment/docker-compose.yml>`_.

.. _manualweb:

Manual installation
===================

When you want to run the OpenSubmit web application without Docker, you need to follow these steps:
  
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

.. _executors:

Single installation of a test machine
*************************************

Test machines are used to run the validation scripts (see :ref:`testing`) for student submission. Pending validation jobs are fetched from the OpenSubmit web server in regular intervals and executed on a test machine.

The creator of an assignment can chose which test machines are used for the validation. This enables a flexible setup with dedicated test machines for special assignments, e.g. GPU programming.

There are two options for installation:

Docker-based installation
=========================

The latest official release of the OpenSubmit executor application is available as `Docker image <https://hub.docker.com/r/troeger/opensubmit-exec/>`__. It expects a single environment variable to be set, which you can easily determine from the `compose file <https://raw.githubusercontent.com/troeger/opensubmit/master/deployment/docker-compose.yml>`_.

.. _manualexec:

Manual installation
===================

When you want to run the OpenSubmit executor daemon without Docker, you need to follow these steps:

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

.. _config_web:

Configuration of the web application
************************************

The web application searches for a configuration file in ``/etc/opensubmit/settings.ini``. This file should be initially created by calling ``opensubmit-web configcreate``. The command allows to pre-define specific configuration options via command-line, or environment variables, and creates an according config file. 

The Docker images run ``opensubmit-web configcreate`` on every startup. Since this command considers environment variables, you can easily set all your options in the normal Docker way.

.. _configtable:

Overview
========

The following table shows all supported configuration options:

=============================== ===================================== ============================================================================
Command-line option             Environment variable                  Description
=============================== ===================================== ============================================================================
--debug                         OPENSUBMIT_DEBUG                      Enable debug mode, not for production systems
--server_url                    OPENSUBMIT_SERVER_URL                 The main URL of the OpenSubmit installation, including sub-directories
--server_mediaroot              OPENSUBMIT_SERVER_MEDIAROOT           Storage path for uploadeded files
--server_hostaliases            OPENSUBMIT_SERVER_HOSTALIASES         Comma-separated list of alternative host names for the web server
--server_logfile                OPENSUBMIT_SERVER_LOGFILE             Log file for the OpenSubmit application
--server_timezone               OPENSUBMIT_SERVER_TIMEZONE            Time zone for all dates and deadlines
--database_name                 OPENSUBMIT_DATABASE_NAME              Name of the database (file)
--database_engine               OPENSUBMIT_DATABASE_ENGINE            Datababase engine being used
--database_user                 OPENSUBMIT_DATABASE_USER              The user name for accessing the database. Not needed for SQLite
--database_password             OPENSUBMIT_DATABASE_PASSWORD          The user password for accessing the database. Not needed for SQLite
--database_host                 OPENSUBMIT_DATABASE_HOST              The host name for accessing the database. Not needed for SQLite
--database_port                 OPENSUBMIT_DATABASE_PORT              The port number for accessing the database. Not needed for SQLite
--login_google_oauth_key        OPENSUBMIT_LOGIN_GOOGLE_OAUTH_KEY     Google OAuth client key
--login_google_oauth_secret     OPENSUBMIT_LOGIN_GOOGLE_OAUTH_SECRET  Google OAuth client secret
--whitelist_google              OPENSUBMIT_WHITELIST_GOOGLE			  Comma-separated list of allowed email addresses for Google login. Leave empty to allow all users.')
--login_twitter_oauth_key       OPENSUBMIT_LOGIN_TWITTER_OAUTH_KEY    Twitter OAuth client key
--login_twitter_oauth_secret    OPENSUBMIT_LOGIN_TWITTER_OAUTH_SECRET Twitter OAuth client secret
--whitelist_twitter             OPENSUBMIT_WHITELIST_TWITTER		  Comma-separated list of allowed email addresses for Twitter login.  Leave empty to allow all users.')
--login_github_oauth_key        OPENSUBMIT_LOGIN_GITHUB_OAUTH_KEY     GitHub OAuth client key
--login_github_oauth_secret     OPENSUBMIT_LOGIN_GITHUB_OAUTH_SECRET  GitHub OAuth client secret
--whitelist_github              OPENSUBMIT_WHITELIST_GITHUB			  Comma-separated list of allowed email addresses for GitHub login. Leave empty to allow all users.')
--login_gitlab_description      OPENSUBMIT_LOGIN_GITLAB_DESCRIPTION   Title of the GitLab login button
--login_gitlab_oauth_key        OPENSUBMIT_LOGIN_GITLAB_OAUTH_KEY     GitLab OAuth client key
--login_gitlab_oauth_secret     OPENSUBMIT_LOGIN_GITLAB_OAUTH_SECRET  GitLab OAuth client secret
--login_gitlab_url              OPENSUBMIT_LOGIN_GITLAB_URL           GitLab URL
--whitelist_gitlab              OPENSUBMIT_WHITELIST_GITLAB			  Comma-separated list of allowed email addresses for GitLab login. Leave empty to allow all users.')
--login_openid_description      OPENSUBMIT_LOGIN_OPENID_DESCRIPTION   Title of the OpenID login button
--login_openid_provider         OPENSUBMIT_LOGIN_OPENID_PROVIDER      URL of the OpenID provider
--whitelist_openid              OPENSUBMIT_WHITELIST_OPENID			  Comma-separated list of allowed email addresses for OpenID login. Leave empty to allow all users.')
--login_oidc_description        OPENSUBMIT_LOGIN_OIDC_DESCRIPTION     Title of the OpenID Connect login button
--login_oidc_endpoint           OPENSUBMIT_LOGIN_OIDC_ENDPOINT        URL of the OpenID Connect endpoint
--login_oidc_client_id          OPENSUBMIT_LOGIN_OIDC_CLIENT_ID       OpenID Connect client id
--login_oidc_client_secret      OPENSUBMIT_LOGIN_OIDC_CLIENT_SECRET   OpenID Connect client secret
--whitelist_oidc                OPENSUBMIT_WHITELIST_OIDC			  Comma-separated list of allowed email addresses for OpenID connect login. Leave empty to allow all users.')
--login_shib_description        OPENSUBMIT_LOGIN_SHIB_DESCRIPTION     Title of the Shibboleth login button
--whitelist_shib                OPENSUBMIT_WHITELIST_SHIB			  Comma-separated list of allowed email addresses for Shibboleth login. Leave empty to allow all users.')
--login_demo                    OPENSUBMIT_LOGIN_DEMO                 Offer demo login options. Not for production use.
--admin_name                    OPENSUBMIT_ADMIN_NAME                 Name of the administrator, shown in privacy policy, impress and backend
--admin_email                   OPENSUBMIT_ADMIN_EMAIL                eMail of the administrator, shown in privacy policy, impress and backend
--admin_address                 OPENSUBMIT_ADMIN_ADDRESS              Address of the administrator, shown in privacy policy and impress
--admin_impress_page            OPENSUBMIT_IMPRESS_PAGE               Link to alternative impress page
--admin_privacy_page            OPENSUBMIT_PRIVACY_PAGE               Link to alternative privacy policy page
=============================== ===================================== ============================================================================

Check ``opensubmit-web configcreate -h`` for more details.

Impress and privacy policy
==========================

There are several European regulations that expect a web page to provide both an impress and a privacy policy page (GDPR / DSGVO). There are two ways to achieve that:

- Option 1: Your configuration file defines name, address, and email of an administrator. The according options for ``opensubmit-web configcreate`` are ``--admin_name``, ``--admin_email``, and ``--admin_address``. Given that information, OpenSubmit will provide a default impress and privacy policy page.

- Option 2: Your configuration file defines alternative URLs for impress page and privacy policy page. The according options for ``opensubmit-web configcreate`` are ``--admin_impress_page`` and ``--admin_privacy_page``.  

.. _auth:

Authentication methods
======================

OpenSubmit supports different authentication methods, as described in the following sections. It :ref:`does not support password-based logins <principles>` - authentication is always supposed to be handled by some third-party service.

If you need another authentication method for your institution, please `open an according issue <https://github.com/troeger/opensubmit/issues/new>`_.

Authentication methods show up on the front page when the according settings are not empty. You can therefore disable any of the mechanisms by commenting them out in settings.ini.

Please note that the names in the following sections relate to the configuration environment variables.

.. _oidc:

Login with OpenID Connect
-------------------------

If you want to allow users to login with OpenID Connect (OIDC), you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_OIDC_DESCRIPTION: <visible button title>``
- ``OPENSUBMIT_LOGIN_OIDC_ENDPOINT: <OpenID connect endpoint URL>``
- ``OPENSUBMIT_LOGIN_OIDC_CLIENT_ID: <OpenID client ID>``
- ``OPENSUBMIT_LOGIN_OIDC_CLIENT_SECRET: <OpenID client secret>``
- ``OPENSUBMIT_WHITELIST_OICD: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

OpenID Connect is the recommended authentication method in OpenSubmit. It is offered by different endpoint providers, such as `Google <https://developers.google.com/identity/protocols/OpenIDConnect#authenticatingtheuser>`_, `Microsoft Azure AD <https://msdn.microsoft.com/en-us/library/azure/dn645541.aspx>`_, `Yahoo <https://developer.yahoo.com/oauth2/guide/openid_connect/?guccounter=1>`_, `Amazon <https://images-na.ssl-images-amazon.com/images/G/01/lwa/dev/docs/website-developer-guide._TTH_.pdf>`_, and `PayPal <https://developer.paypal.com/docs/integration/direct/identity/log-in-with-paypal/>`_.

Login with classical OpenID
---------------------------

If you want to allow users to login with classical OpenID, you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_OPENID_DESCRIPTION: <visible button title>``
- ``OPENSUBMIT_LOGIN_OPENID_PROVIDER: <provider URL>``
- ``OPENSUBMIT_WHITELIST_OPENID: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

The standard OpenSubmit installation already contains an example setting for using StackExchange as authentication provider. Please note that classical OpenID is considered as being deprecated. We recommend to use OpenID Connect instead.

Login with Shibboleth
---------------------

If you want to allow users to login with Shibboleth, you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_SHIB_DESCRIPTION: <visible button title>``
- ``OPENSUBMIT_WHITELIST_SHIB: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

You also need a fully working installation of the `Apache 2.4 mod_shib <https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPApacheConfig>`_ module. The authentication module of OpenSubmit assumes that, as result of the work of *mod_shib*, the following environment variables are given:

- ``REMOTE_USER``: The user name of the authenticated user.
- ``HTTP_SHIB_ORGPERSON_EMAILADDRESS``: The email address of the authenticated user.
- ``HTTP_SHIB_INETORGPERSON_GIVENNAME``: The first name of the authenticated user.
- ``HTTP_SHIB_PERSON_SURNAME``: The last name of the authenticated user.

Note: If you are using Apache 2.4 with *mod_wsgi*, make sure to set ``WSGIPassAuthorization On``. Otherwise, these environment variables may not pass through.

.. _gitlab:

Login with GitLab
-----------------

If you want to allow users to login with some GitLab account, you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_GITLAB_DESCRIPTION: <visible button title>``
- ``OPENSUBMIT_LOGIN_GITLAB_URL: <URL of the GitLab installation>``
- ``OPENSUBMIT_LOGIN_GITLAB_OAUTH_KEY: <Application ID, as configured in GitLab>``
- ``OPENSUBMIT_LOGIN_GITLAB_OAUTH_SECRET: <Application secret, as configured in GitLab>``
- ``OPENSUBMIT_WHITELIST_GITLAB: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

A new pair of Application ID and secret can be generated within your GitLab installation:

- Login into the GitLab installation and go to your user profile
- Go to the *Application* section and create a new entry:

  - The name can be freely chosen.
  - The Redirect URI needs to be ``<base url of your OpenSubmit installation>/complete/gitlab/``.
  - You only need to enable *read_user* rights.
  - Copy the creation Application ID and secret into your OpenSubmit configuration.


Login with Google
-----------------

If you want to allow users to login with an Google account, you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_GOOGLE_OAUTH_KEY: <OAuth key>``
- ``OPENSUBMIT_LOGIN_GOOGLE_OAUTH_SECRET: <OAuth secret>``
- ``OPENSUBMIT_WHITELIST_GOOGLE: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

A new pair can be created in the `Google API Console <https://console.developers.google.com/apis/credentials>`_. The authorized forwarding URL should be ``<base url of your installation>/complete/google-oauth2/``.

You also need to `activate the Google+ API <https://console.developers.google.com/apis/api/plus.googleapis.com/overview>`_, so that OpenSubmit is able to fetch basic user information from Google.

Login with Twitter
------------------

If you want to allow users to login with an Twitter account, you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_TWITTER_OAUTH_KEY: <OAuth key>``
- ``OPENSUBMIT_LOGIN_TWITTER_OAUTH_SECRET: <OAuth secret>``
- ``OPENSUBMIT_WHITELIST_TWITTER: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

A new key / secret pair can be created in the `Twitter Application Management <https://apps.twitter.com/>`_.  The authorized forwarding URL should be ``<base url of your installation>/complete/twitter/``. We recommend to modify the application access to *Read only*, and to allow access to the email addresses. 

Login with GitHub
-----------------

If you want to allow users to login with an GitHub account, you need to configure the following settings:

- ``OPENSUBMIT_LOGIN_GITHUB_OAUTH_KEY: <OAuth key>``
- ``OPENSUBMIT_LOGIN_GITHUB_OAUTH_SECRET: <OAuth secret>``
- ``OPENSUBMIT_WHITELIST_GITHUB: foo@bar.de, bar@foo.org, ...``

The whitelist configuration is optional, leave it out for enabling all authenticated users.

A new key / secret pair can be created in the `OAuth application registration <https://github.com/settings/applications/new>`_.  The authorized forwarding URL should be ``<base url of your installation>/complete/github/``.

.. _config_exec:

Configuration of the executor
*****************************

The executor searches for a configuration file in ``/etc/opensubmit/executor.ini``. This file should be initially created by calling ``opensubmit-exec configcreate``. This management command allows to pre-define specific configuration options via command-line or environment variables, and creates an according config file. Check ``opensubmit-exec configcreate -h`` for details.

.. _useroverview:

User management
***************

One of the core concepts of OpenSubmit is that users register themselves by using an external authentication provider (see :ref:`auth`). 

Based on this, there are different groups such a registered user can belong to:

- *Students* (default): Users who cannot access the teacher backend.  
- *Student Tutors*: Users with limited rights in the teacher backend.
- *Course Owners*: Users with advanced rights in the teacher backend.
- *Administrators*: Users will unrestricted rights.

.. _permissions:

Permissions
===========

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
=========================

There are two ways to assign users to user groups, assuming that they logged-in once for registration:

- In the teacher backend, as administrator (see :ref:`auth`).
- With the ``opensubmit-web`` command-line tool.

The first option is the web-based configuration of user groups, which is only available for administrators. Click on *Manage users* and mark all user accounts to be modified. After that, choose an according action in the lower left corner of the screen.

The second option is the ``opensubmit-web`` command-line tool that is available on the web server. Calling it without arguments shows the different options to assign users to user groups.

.. _merge users:

Merging accounts
================

Since OpenSubmit users always register themselves in the platform (see :ref:`auth`), it can happen that the same physical person creates multiple accounts through different authentication providers. The main reason for that is a non-matching or missing email address being provided by the authentication provider.

Administrators can merge users in the teacher backend. Click on *Manage users*, mark all user accounts to be merged, and choose the according action in the lower left corner. The nect screen shows you the intended merging activity and allows to chose the "primary" account by flipping roles. The non-primary account is deleted as part of the merging activity.

.. _troubleshooting:

Troubleshooting
===============

The ``opensubmit-web`` command-line tool provides some helper functions to deal with problems:

- ``opensubmit-web dumpconfig``: Dumps the effective runtime configuration of OpenSubmit after parsing the config file. 
- ``opensubmit-web fixperms``: Checks and fixes the permissions of student and teacher accounts.
- ``opensubmit-web fixchecksums``: Re-generates all student upload checksums. You need that after fiddling around in the media folder manually.

In case of trouble, make also sure that you enabled the file logging and set OPENSUBMIT_DEBUG temporarly to TRUE. This leads to a larger amount of log information that may help to pinpoint your problem.

