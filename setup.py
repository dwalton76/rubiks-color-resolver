# third party libraries
from setuptools import setup

setup(
    name="rubikscolorresolver",
    version="1.0.0",
    description="Resolve rubiks cube RGB values to the six cube colors",
    keywords="rubiks cube color",
    url="https://github.com/dwalton76/rubiks-color-resolver",
    author="Daniel Walton",
    author_email="dwalton76@gmail.com",
    license_files=("LICENSE",),
    scripts=["usr/bin/rubiks-color-resolver.py"],
    packages=["rubikscolorresolver"],
)
