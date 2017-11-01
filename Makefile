build:
	# Build the install packages.
	pip install -r requirements.txt
	pushd web;      ./setup.py bdist_wheel; popd
	pushd executor; ./setup.py bdist_wheel; popd
	mv executor/dist/* .
	rmdir executor/dist
	mv web/dist/* .
	rmdir web/dist

venv:
	# Create a virtualenv.
	# Activate it afterwards with "source venv/bin/activate"
	python3.6 -m venv venv

install: build
	# Installs built packages locally.
	# This is intended for staging tests in a virtualenv.
	# On production systems, install a release directly from PyPI.
	pip install --upgrade *.whl

uninstall:
	pip uninstall opensubmit-web
	pip uninstall opensubmit-exec

tests:
	# Run all tests.
	pushd executor; pip install -r requirements.txt; popd
	pushd web; pip install -r requirements.txt; popd
	export PYTHONPATH=../executor/opensubmit:$PYTHONPATH; pushd web; ./manage.py test; popd

coverage:
	# Run all tests and obtain coverage information.
	pushd web; coverage run --source='.','../executor/' --omit='*/setup.py',opensubmit/wsgi.py manage.py test opensubmit.tests; coverage html; popd

clean:
	rm -rf ./cmdline/dist
	rm -rf ./cmdline/build
	rm -rf ./web/dist
	rm -rf ./web/build
	rm -rf ./web/*.egg-info/
	rm -rf ./executor/dist
	rm -rf ./executor/build
	rm -rf ./executor/*.egg-info/
	rm -f  ./*.tar.gz
	rm -f  ./*.whl
	rm -f  ./web/.coverage
	rm -rf ./htmlcov
	rm -rf ./web/htmlcov

pypi: build
	# Upload built packages to PyPI.
	# Assumes valid credentials in ~/.pypirc
	twine upload opensubmit_*.whl
