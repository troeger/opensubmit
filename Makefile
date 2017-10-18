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
	rm -f   *.tar.gz
	rm -f   ./web/.coverage
	rm -rf  ./htmlcov
	rm -rf  ./web/htmlcov

pypi:
	# Assumes valid credentials in ~/.pypirc
	twine upload opensubmit-*.tar.gz
