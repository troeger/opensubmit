SHELL = /bin/bash
VERSION = 0.7.4

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

# Re-create docker images locally
docker-build: build
	docker-compose build

# Run docker images locally
docker:
	docker-compose up

# Update version numbers, commit and tag 
bumpversion:
	bumpversion --verbose patch

# Re-create docker images and upload into registry
docker-push: build
	docker login --username=troeger
	docker build -t troeger/opensubmit-web:$(VERSION) web
	docker push troeger/opensubmit-web:$(VERSION)
	docker build -t troeger/opensubmit-exec:$(VERSION) executor
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

