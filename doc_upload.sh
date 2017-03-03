#!/bin/bash

git config --global user.email "$GIT_EMAIL"
git config --global user.name "$GIT_NAME"
make -C doc clean
git clone -b gh-pages --single-branch https://$GH_TOKEN@github.com/RNAer/dumpling.git doc/_build/html
make -C doc html
cd doc/_build/html
pwd
ls
git remote -v
git status
git commit -a -m "$1"
git push --quiet origin gh-pages
