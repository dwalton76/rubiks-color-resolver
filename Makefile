
install:
	micropython -m upip install micropython-array
	micropython -m upip install micropython-logging
	micropython -m upip install micropython-os
	cp -r rubikscolorresolver /usr/lib/micropython
	python3 setup.py install

clean:
	sudo rm -rf build dist rubikscolorresolver.egg-info
