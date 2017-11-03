build:
	# Build the install packages.
	pip install -r requirements.txt

	pushd web;      ./setup.py bdist_wheel; popd
	mv web/dist/* dist/
	rmdir web/dist
	rm -rf ./web/build
	rm -rf ./web/*.egg-info/

	pushd executor; ./setup.py bdist_wheel; popd
	mv executor/dist/* dist/
	rmdir executor/dist
	rm -rf ./executor/build
	rm -rf ./executor/*.egg-info/

venv:
	# Create a virtualenv.
	# Activate it afterwards with "source venv/bin/activate"
	python3.6 -m venv venv

uninstall:
	pip uninstall -y opensubmit-web
	pip uninstall -y opensubmit-exec

re-install: build uninstall
	# Installs built packages locally.
	# This is intended for staging tests in a virtualenv.
	# On production systems, install a release directly from PyPI.
	pip install dist/*.whl

docker: build
	# Create Docker image, based on fresh build
	pushd dist; docker build .; popd

tests:
	# Run all tests.
	pushd executor; pip install -r requirements.txt; popd
	pushd web; pip install -r requirements.txt; popd
	export PYTHONPATH=../executor/opensubmit:$PYTHONPATH; pushd web; ./manage.py test; popd

coverage:
	# Run all tests and obtain coverage information.
	pushd web; coverage run --source='.','../executor/' --omit='*/setup.py',opensubmit/wsgi.py manage.py test opensubmit.tests; coverage html; popd

clean:
	rm -f  ./dist/*.whl
	rm -f  ./web/.coverage
	rm -rf ./htmlcov
	rm -rf ./web/htmlcov
	find . -name "*.bak" -delete

pypi: build
	# Upload built packages to PyPI.
	# Assumes valid credentials in ~/.pypirc
	twine upload dist/opensubmit_*.whl
