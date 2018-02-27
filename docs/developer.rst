Developer Manual
################

The development of OpenSubmit is coordinated on `GitHub <https://github.com/troeger/opensubmit>`_.
We need help in everything. Feel free to join us.

The central `Makefile <https://github.com/troeger/opensubmit/blob/master/Makefile>`_ is a good starting point. It supports several targets for preparing a development environment:

make venv
    Prepares a `virtualenv <https://virtualenv.pypa.io/en/stable/userguide/>`_ with all neccessary packages for packaging and running OpenSubmit.
make runserver
    Perform all neccessary preparations to run the `Django development server <https://docs.djangoproject.com/en/2.0/intro/tutorial01/#the-development-server>`_. This includes the creation of a configuration file, the execution of the neccessary database creation / migration steps and the startup of the server.
make tests
    Run the test suite.
make coverage
    Run test suite and create code coverage analysis.
make docs
    Build the HTML documentation.
make build
    Create Python installation packages (wheels).
make docker-build
    Create Docker images for web application and executors.
make docker
    Run Docker containers for the web application, executors and a PostgreSQL database.




