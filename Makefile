SHELL = /bin/bash

.PHONY: build docs

default: build

venv/bin/activate: web/requirements.txt executor/requirements.txt
	# Prepare VirtualEnv
	test -d venv || python3.4 -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r executor/requirements.txt
	venv/bin/pip install -r web/requirements.txt
	touch venv/bin/activate

venv: venv/bin/activate
	# Activate virtual env

build: venv
	# Build the Python wheel install packages from the sources.
	pushd web; ../venv/bin/python ./setup.py bdist_wheel; popd
	pushd executor; ../venv/bin/python ./setup.py bdist_wheel; popd

docs: venv
	# Build the HTML documentation from the sources.
	source venv/bin/activate; pushd docs; make html; popd; deactivate

tests: venv
	# Run all tests.
	pushd web; ../venv/bin/python ./manage.py test; popd

coverage:
	# Run all tests and obtain coverage information.
	coverage run ./web/manage.py test opensubmit.tests; coverage html

docker-build: build
	# Re-create docker images locally
	docker-compose build

docker:
	# Run docker images locally
	docker-compose up

docker-push: build
	# Re-create docker images for upload into registry
	docker login --username=troeger
	docker build -t troeger/opensubmit-web:latest web
	docker push troeger/opensubmit-web:latest
	docker build -t troeger/opensubmit-exec:latest executor
	docker push troeger/opensubmit-exec:latest

pypi-push-web: build
	# Upload built package for web application to PyPI.
	# Assumes valid credentials in ~/.pypirc
	source venv/bin/activate; twine upload web/dist/opensubmit_*.whl; deactivate

pypi-push-exec: build
	# Upload built package for executor application to PyPI.
	# Assumes valid credentials in ~/.pypirc
	source venv/bin/activate; twine upload executor/dist/opensubmit_*.whl; deactivate

clean:
	# Clean temporary files
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

clean-docs:
	# Clean HTML version of the documentation
	rm -rf docs/formats

clean-docker:
	docker container prune
	docker volume prune
	docker system prune

