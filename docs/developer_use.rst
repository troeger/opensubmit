Developer Manual
################

The development of OpenSubmit is coordinated on `GitHub <https://github.com/troeger/opensubmit>`_.
We need help in everything. Feel free to join us.

OpenSubmit runs with Python 3.4 or newer versions. For a development enviroment, please follow these steps:

- Install Python >= 3.4.
- Clone the repository with ``git clone https://github.com/troeger/opensubmit.git``.

The central `Makefile <https://github.com/troeger/opensubmit/blob/master/Makefile>`_ is a good starting point. It supports several targets for a development environment.

You can start the web application alone with ``make runserver``, which performs the following steps:

- Creation of a virtualenv with all neccessary packages (see ``make venv/bin/activate``).
- Creation of a configuration file for the Django development server (see ``make web/opensubmit/settings_dev.ini``).
- Execution of the neccessary database creation / migration steps.
- Startup of the Django development server.

Other interesting targets are:

- ``make tests``: Run test suite.
- ``make coverage``: Run test suite and create code coverage analysis.
- ``make docs``: Build the HTML documentation.
- ``make build``: Create Python installation packages (wheels).
- ``make docker-build``: Create Docker images for web application and executors.
- ``make docker``: Start Docker containers for the web application, executors and a PostgreSQL database.




