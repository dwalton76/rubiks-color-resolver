clean:
	rm -rf build dist venv rubikscolorresolver.egg-info
	find . -name __pycache__ | xargs rm -rf
	find . -name *.pyc | xargs rm -rf

init: clean
	python3 -m venv venv
	./venv/bin/python3 -m pip install -U pip
	./venv/bin/python3 -m pip install -r requirements.dev.txt
	./venv/bin/python3 -m pre_commit install --install-hooks --overwrite
	./venv/bin/python3 -m pip check

install:
	sudo python3 setup.py install

install-micropython:
	micropython -m upip install micropython-array
	micropython -m upip install micropython-logging
	micropython -m upip install micropython-os
	micropython -m upip install micropython-unittest
	sudo cp -r rubikscolorresolver/ /usr/lib/micropython/

test:
	python3 ./tests/test-unittest.py
	python3 ./tests/test-cubes.py

test-micropython:
	micropython ./tests/test-unittest.py
	micropython ./tests/test-cubes.py

format:
	isort rubikscolorresolver tests usr utils setup.py
	./venv/bin/python3 -m black --config=pyproject.toml .
	./venv/bin/python3 -m flake8 --config=.flake8

wheel:
	./venv/bin/python3 setup.py bdist_wheel
