build:
	pushd web;      ./setup.py build sdist; popd
	pushd executor; ./setup.py build sdist; popd
	mv executor/dist/* .
	mv web/dist/* .

tests:
	pushd executor; pip install -r requirements.txt; popd
	pushd web; pip install -r requirements.txt; popd
	export PYTHONPATH=../executor/opensubmit:$PYTHONPATH; pushd web; ./manage.py test; popd

coverage:
	pushd web; coverage run --source='.'  --omit=setup.py,opensubmit/wsgi.py manage.py test opensubmit.tests; coverage html; popd

clean:
	rm -rf ./cmdline/dist
	rm -rf ./cmdline/build
	rm -rf ./web/dist
	rm -rf ./web/build
	rm -rf ./web/*.egg-info/
	rm -rf ./executor/dist
	rm -rf ./executor/build
	rm -rf ./executor/*.egg-info/
	rm -f   *.tar.gz
	rm -f   ./web/.coverage

pypi_web:
	# Assumes valid credentials in ~/.pypirc
	# For the format, this seems to work: https://pythonhosted.org/an_example_pypi_project/setuptools.html#intermezzo-pypirc-file-and-gpg
	pushd web; python ./setup.py sdist upload -r https://pypi.python.org/pypi; popd

pypi_executor:
	# Assumes valid credentials in ~/.pypirc
	# For the format, this seems to work: https://pythonhosted.org/an_example_pypi_project/setuptools.html#intermezzo-pypirc-file-and-gpg
	pushd executor; python ./setup.py sdist upload -r https://pypi.python.org/pypi; popd
