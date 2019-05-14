all: clean build

up:
	docker-compose -f docker-compose.yml up

halt:
	docker-compose -f docker-compose.yml down

destroy:
	docker-compose -f docker-compose.yml down -v

clean:
	python setup.py clean --all
	rm -r dist
	rm -r *.egg-info

build: 
	python setup.py build sdist
	python setup.py build bdist_wheel --universal
	
upload:
	twine upload dist/*

test:
	pytest -sv
