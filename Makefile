SHELL = /bin/bash

.PHONY: build docs

build:
	# Build the install packages from the sources.
	pip install -r requirements.txt
	pushd web; ./setup.py bdist_wheel; popd
	pushd executor; ./setup.py bdist_wheel; popd

docs:
	# Build the HTML documentation from the sources.
	pushd docs; make html; popd

docker: build
	# Create and run docker images
	docker-compose up

venv:
	# Create a virtualenv.
	# Activate it afterwards with "source venv/bin/activate"
	(python3.4 -m venv venv; \
	 source venv/bin/activate; \
	 pip install -r requirements.txt; \
	 pushd executor; pip install -r requirements.txt; popd; \
	 pushd web; pip install -r requirements.txt; popd;)

tests:
	# Run all tests.
	# Assumes activated VirtualEnv
	pushd web; ./manage.py test; popd

coverage:
	# Run all tests and obtain coverage information.
	# Assumes activated VirtualEnv
	coverage run ./web/manage.py test opensubmit.tests; coverage html

clean:
	# Clean temporary files
	rm -fr  web/dist
	rm -fr  executor/dist
	rm -fr  web/*egg-info
	rm -fr  executor/*egg-info
	rm -f  ./.coverage
	rm -rf ./htmlcov
	find . -name "*.bak" -delete

clean-docs:
	# Clean HTML version of the documentation
	rm -rf docs/formats

pypi_web:
	# Upload built package for web application to PyPI.
	# Assumes valid credentials in ~/.pypirc
	twine upload web/dist/opensubmit_*.whl

pypi_exec:
	# Upload built package for executor application to PyPI.
	# Assumes valid credentials in ~/.pypirc
	twine upload executor/dist/opensubmit_*.whl
