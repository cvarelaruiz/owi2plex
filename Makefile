all: clean build

clean:
	python setup.py clean --all
	rm -r dist


build: 
	python setup.py build sdist bdist_wheel
	
build2:
	python2 setup.py build bdist_wheel

upload:
	twine upload dist/*