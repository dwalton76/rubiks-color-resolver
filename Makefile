
clean:
	rm -rf build dist venv
	rm -rf rubikscolorresolver.egg-info rubikscolorresolver/*.pyc
	find . -name __pycache__ | xargs rm -rf

init:
	python3 -m venv venv
	@./venv/bin/python3 -m pip install -U pip==21.3.1
	@./venv/bin/python3 -m pip install -r requirements.dev.txt
	@./venv/bin/python3 -m pre_commit install --install-hooks --overwrite
	@./venv/bin/python3 -m pip check

install:
	micropython -m upip install micropython-array
	micropython -m upip install micropython-logging
	micropython -m upip install micropython-os
	micropython -m upip install micropython-unittest
	cp -r rubikscolorresolver/ /usr/lib/micropython/
	python3 setup.py install

test:
	python3 ./tests/test-unittest.py
	python3 ./tests/test-cubes.py
	micropython ./tests/test-unittest.py
	micropython ./tests/test-cubes.py

format:
	isort rubikscolorresolver/ utils/ usr/ tests/
	@./venv/bin/python3 -m black --config=pyproject.toml .
	@./venv/bin/python3 -m flake8 --config=.flake8

lint:
	black --check rubikscolorresolver/ utils/ usr/
	flake8 --config .flake8 --statistics rubikscolorresolver/ utils/ usr/
