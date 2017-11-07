Developer manual
================

OpenSubmit runs with Python 3.4 or newer versions. 

For an OpenSubmit development enviroment, please do the following steps:

  * Install Python >= 3.4
  * Install a virtualenv with ``python3 -m venv venv``
  * Enter the virtualenv with ``source venv/bin/active``
  * Clone the repository
  * Install the build dependencies with ``pip install -r requirements.txt``
  * Run ``make tests`` to install all runtime dependencies and run all tests.
  * In the *web* folder:

    * Run ``manage.py migrate`` to create the database.
    * Run ``manage.py runserver`` to run a development web server.
