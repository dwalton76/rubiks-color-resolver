#!/usr/bin/env micropython

from rubikscolorresolver import run_test_cases
import logging


# logging.basicConfig(filename='rubiks-rgb-solver.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)5s: %(message)s')
log = logging.getLogger(__name__)

run_test_cases()
