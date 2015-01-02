#!/usr/bin/env sh

python2 -m coverage run --source vecrec vecrec_tests.py
python2 -m coverage html -d htmlcov2

python3 -m coverage run --source vecrec vecrec_tests.py
python3 -m coverage html -d htmlcov3
