Developer manual
################

.. warning::

   This manual is work in progress and therefore incomplete. Feel free to help us with a `pull request on GitHub <https://github.com/troeger/opensubmit>`_.

OpenSubmit runs with Python 3.4 or newer versions. 

For an OpenSubmit development enviroment, please do the following steps:

- Install Python >= 3.4.
- Clone the repository with ``git clone https://github.com/troeger/opensubmit.git``.
- Prepare a virtualenv with all neccessary python packages by calling ``make venv``. It is stored in the ``venv`` folder.
- `Activate <https://virtualenv.pypa.io/en/stable/userguide/#activate-script>`_ the virtualenv.
- Run ``make tests`` to run all tests.
- In the *web* folder:

  - Run ``manage.py migrate`` to create the database.
  - Run ``manage.py runserver`` to run a development web server.
