SHELL = /bin/bash

.PHONY: build docs

build: venv
	# Build the install packages from the sources.
	pushd web; ../venv/bin/python ./setup.py bdist_wheel; popd
	pushd executor; ../venv/bin/python ./setup.py bdist_wheel; popd

docs: venv
	# Build the HTML documentation from the sources.
	source venv/bin/activate; pushd docs; make html; popd; deactivate

docker:
	# Run docker images locally
	docker-compose up

docker-build: build
	# Re-create docker images
	docker-compose build

venv: venv/bin/activate

venv/bin/activate: web/requirements.txt executor/requirements.txt
	# Prepare VirtualEnv
	test -d venv || python3.4 -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r executor/requirements.txt
	venv/bin/pip install -r web/requirements.txt
	touch venv/bin/activate

tests: venv
	# Run all tests.
	pushd web; ../venv/bin/python ./manage.py test; popd

coverage:
	# Run all tests and obtain coverage information.
	coverage run ./web/manage.py test opensubmit.tests; coverage html

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

pypi_web: venv
	# Upload built package for web application to PyPI.
	# Assumes valid credentials in ~/.pypirc
	source venv/bin/activate; twine upload web/dist/opensubmit_*.whl; deactivate

pypi_exec: venv
	# Upload built package for executor application to PyPI.
	# Assumes valid credentials in ~/.pypirc
	source venv/bin/activate; twine upload executor/dist/opensubmit_*.whl; deactivate
