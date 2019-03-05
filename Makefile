SHELL = /bin/bash
VERSION = 0.7.21

.PHONY: build docs check-venv

# Make Python wheels
default: build

# Prepare VirtualEnv by installing project dependencies
venv/bin/activate: web/requirements.txt executor/requirements.txt
	test -d venv || python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r executor/requirements.txt
	venv/bin/pip install -r web/requirements.txt
	touch venv/bin/activate

# Shortcut for preparation of VirtualEnv
venv: venv/bin/activate

check-venv:
ifndef VIRTUAL_ENV
	$(error Please create a VirtualEnv with 'make venv' and activate it)
endif

# Create an OpenSubmit config file for the development server
web/opensubmit/settings_dev.ini: check-venv 
	python -m web.opensubmit.cmdline -c web/opensubmit/settings_dev.ini configcreate --debug --login_demo

# Run the OpenSubmit development server
runserver: check-venv web/opensubmit/settings_dev.ini
	pushd web; python ./manage.py migrate; popd
	pushd web; python ./manage.py runserver; popd

# Build the Python wheel install packages.
build: check-venv
	pushd web; python ./setup.py bdist_wheel; popd
	pushd executor; python ./setup.py bdist_wheel; popd

# Build the HTML documentation from the sources.
docs: check-venv
	pushd docs; make html; popd

# Run all tests.
tests: check-venv web/opensubmit/settings_dev.ini
	pushd web; python ./manage.py test; popd

# Run all tests and obtain coverage information.
coverage: check-venv web/opensubmit/settings_dev.ini
	coverage run ./web/manage.py test opensubmit.tests; coverage html

# Run docker container with current code for interactive smoke testing
# Mounts the sources in the Docker container - so, as long as Apache
# detects the source code change, you should be able to do live patching
docker-test: clean build
	docker-compose -f deployment/docker-compose-test.yml up

docker-test-front-shell:
	docker exec -it deployment_web_1 bash

# Update version numbers, commit and tag 
bumpversion:
	bumpversion --verbose patch

# Re-create docker images and upload into registry
docker-push: clean build
	docker login --username=troeger
	pushd web; docker build -t troeger/opensubmit-web:$(VERSION) .; popd
	docker push troeger/opensubmit-web:$(VERSION)
	pushd executor; docker build -t troeger/opensubmit-exec:$(VERSION) .; popd
	docker push troeger/opensubmit-exec:$(VERSION)

# Upload built packages to PyPI.
# Assumes valid credentials in ~/.pypirc
pypi-push: check-venv build
	twine upload web/dist/opensubmit_web-$(VERSION)-py3-none-any.whl
	twine upload executor/dist/opensubmit_exec-$(VERSION)-py3-none-any.whl

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

