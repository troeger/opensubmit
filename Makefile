build:
	pushd web;      ./setup.py build sdist; popd
	pushd executor; ./setup.py build sdist; popd
	mv executor/dist/* .
	mv web/dist/* .

tests:
	export PYTHONPATH=../executor/opensubmit:$PYTHONPATH; pushd web; ./manage.py test; popd

clean:
	rm -rf ./cmdline/dist
	rm -rf ./cmdline/build
	rm -rf ./web/dist
	rm -rf ./web/build
	rm -rf ./web/*.egg-info/
	rm -rf ./executor/dist
	rm -rf ./executor/build
	rm -rf ./executor/*.egg-info/
