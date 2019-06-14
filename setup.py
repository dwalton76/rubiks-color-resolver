from setuptools import setup


setup(
    name="rubikscolorresolver",
    version="1.0.0",
    description="Resolve rubiks cube RGB values to the six cube colors",
    keywords="rubiks cube color",
    url="https://github.com/dwalton76/rubiks-color-resolver",
    author="dwalton76",
    author_email="dwalton76@gmail.com",
    license="GPLv3",
    scripts=["usr/bin/rubiks-color-resolver.py"],
    packages=["rubikscolorresolver"],
)
