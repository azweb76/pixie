
bootstrap:
	pip install twine wheel poetry

build:
	rm -rf build/
	poetry build

publish: build
	poetry publish
