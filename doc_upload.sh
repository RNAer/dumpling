#!/bin/bash

make -C doc clean
git clone -b gh-pages --single-branch https://$GH_TOKEN@github.com/biocore/calour.git doc/_build/html
make -C doc html
cd doc/_build/html
git commit -a -m "$1"
git push --quiet origin gh-pages
