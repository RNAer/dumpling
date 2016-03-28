#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Copyright (c) 2015--, micronota development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import re
import ast
from setuptools import find_packages, setup


# version parsing from __init__ pulled from Flask's setup.py
# https://github.com/mitsuhiko/flask/blob/master/setup.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('dumpling/__init__.py', 'rb') as f:
    hit = _version_re.search(f.read().decode('utf-8')).group(1)
    version = str(ast.literal_eval(hit))

classifiers = [
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: BSD License',
    'Environment :: Console',
    'Topic :: Software Development :: Libraries',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Operating System :: Unix',
    'Operating System :: POSIX',
    'Operating System :: MacOS :: MacOS X']


description = 'DUMPLING: command-line app controller'
with open('README.org') as f:
    long_description = f.read()


setup(name='dumpling',
      version=version,
      license='BSD',
      description=description,
      long_description=long_description,
      classifiers=classifiers,
      author="Zhenjiang Zech Xu",
      author_email="zhenjiang.xu@gmail.com",
      maintainer_email="zhenjiang.xu@gmail.com",
      url='http://github.com/rnaer/dumpling',
      test_suite='nose.collector',
      packages=find_packages(),
      install_requires=[],
      extras_require={'test': ["nose", "pep8", "flake8"],
                      'coverage': ["coverage"],
                      'doc': ["Sphinx == 1.3.3"]})
