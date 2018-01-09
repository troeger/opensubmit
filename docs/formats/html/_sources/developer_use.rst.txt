Developer Manual
################

The development of OpenSubmit is coordinated on `GitHub <https://github.com/troeger/opensubmit>`_.
We need help in everything. Feel free to join us.

OpenSubmit runs with Python 3.4 or newer versions. For a development enviroment, please follow these steps:

- Install Python >= 3.4.
- Clone the repository with ``git clone https://github.com/troeger/opensubmit.git``.
- Prepare a virtualenv with all neccessary python packages by calling ``make venv``. It is stored in the ``venv`` folder.
- `Activate <https://virtualenv.pypa.io/en/stable/userguide/#activate-script>`_ the virtualenv.
- Run ``make tests`` to run all tests.
- In the *web* folder:

  - Run ``manage.py migrate`` to create the database.
  - Run ``manage.py runserver`` to run a development web server.

The central `Makefile <https://github.com/troeger/opensubmit/blob/master/Makefile>`_ is a good starting point.
