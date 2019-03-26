all: clean build

clean:
	python setup.py clean --all
	rm -r dist
	rm -r *.egg-info

build: 
	python setup.py build sdist
	python setup.py build bdist_wheel --universal
	
upload:
	twine upload dist/*