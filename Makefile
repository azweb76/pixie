
bootstrap:
	python -m venv .venv
	pip install twine wheel poetry

install:
	poetry install

build:
	rm -rf build/
	poetry build

publish: build
	poetry publish
