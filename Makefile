all: clean build

clean:
	python setup.py clean --all

build:
	python setup.py build sdist bdist_wheel

upload:
	twine upload dist/*