
install:
	micropython -m upip install micropython-array
	micropython -m upip install micropython-logging
	micropython -m upip install micropython-os
	cp -r rubikscolorresolver /usr/lib/micropython

clean:
	sudo rm -rf build dist rubikscolorresolver.egg-info
