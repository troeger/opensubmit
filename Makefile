SHELL = /bin/bash

.PHONY: build docs

# Make Python wheels
default: build

# Prepare VirtualEnv by installing project dependencies
venv/bin/activate: web/requirements.txt executor/requirements.txt
	test -d venv || python3.4 -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r executor/requirements.txt
	venv/bin/pip install -r web/requirements.txt
	touch venv/bin/activate

# Shortcut for preparation of VirtualEnv
venv: venv/bin/activate

# Create an OpenSubmit config file for the development server
web/opensubmit/settings_dev.ini: venv 
	venv/bin/python -m web.opensubmit.cmdline -c web/opensubmit/settings_dev.ini configcreate --debug

# Run the OpenSubmit development server
runserver: venv web/opensubmit/settings_dev.ini
	pushd web; ../venv/bin/python ./manage.py migrate; popd
	pushd web; ../venv/bin/python ./manage.py runserver; popd

# Build the Python wheel install packages.
build: venv
	pushd web; ../venv/bin/python ./setup.py bdist_wheel; popd
	pushd executor; ../venv/bin/python ./setup.py bdist_wheel; popd

# Build the HTML documentation from the sources.
docs: venv
	source venv/bin/activate; pushd docs; make html; popd; deactivate

# Run all tests.
tests: venv
	pushd web; ../venv/bin/python ./manage.py test; popd

# Run all tests and obtain coverage information.
coverage:
	coverage run ./web/manage.py test opensubmit.tests; coverage html

# Re-create docker images locally
docker-build: build
	docker-compose build

# Run docker images locally
docker:
	docker-compose up

# Re-create docker images and upload into registry
docker-push: build
	docker login --username=troeger
	docker build -t troeger/opensubmit-web:latest web
	docker push troeger/opensubmit-web:latest
	docker build -t troeger/opensubmit-exec:latest executor
	docker push troeger/opensubmit-exec:latest

# Upload built package for web application to PyPI.
# Assumes valid credentials in ~/.pypirc
pypi-push-web: build
	source venv/bin/activate; twine upload web/dist/opensubmit_*.whl; deactivate

# Upload built package for executor application to PyPI.
# Assumes valid credentials in ~/.pypirc
pypi-push-exec: build
	source venv/bin/activate; twine upload executor/dist/opensubmit_*.whl; deactivate

# Clean temporary files
clean:
	rm -fr  web/build
	rm -fr  web/dist
	rm -fr  executor/build
	rm -fr  executor/dist
	rm -fr  web/*egg-info
	rm -fr  executor/*egg-info
	rm -f  ./.coverage
	rm -rf ./htmlcov
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete

# Clean HTML version of the documentation
clean-docs:
	rm -rf docs/formats

# Clean cached Docker data and state
clean-docker:
	docker container prune
	docker volume prune
	docker system prune

