
all:
	micropython -m upip install micropython-array
	micropython -m upip install micropython-logging
	micropython -m upip install micropython-os

clean:
	sudo rm -rf build dist rubikscolorresolver.egg-info
