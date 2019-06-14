
install:
	micropython -m upip install micropython-array
	micropython -m upip install micropython-logging
	micropython -m upip install micropython-os
	micropython -m upip install micropython-unittest
	cp -r rubikscolorresolver/ /usr/lib/micropython
	python3 setup.py install

clean:
	sudo rm -rf build dist rubikscolorresolver.egg-info rubikscolorresolver/*.pyc rubikscolorresolver/__pycache__

test:
	python3 ./test-unittest.py
	micropython ./test-unittest.py
	python3 ./test-cubes.py
	micropython ./test-cubes.py
