#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Copyright (c) 2016--, dumpling development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from setuptools import setup
import dumpling


classifiers = [
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: BSD License',
    'Environment :: Console',
    'Topic :: Software Development :: Libraries',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Operating System :: Unix',
    'Operating System :: POSIX',
    'Operating System :: Microsoft',
    'Operating System :: MacOS :: MacOS X']


description = 'DUMPLING: command-line app controller'
with open('README.org') as f:
    long_description = f.read()


setup(name='dumpling',
      version=dumpling.__version__,
      license='BSD',
      description=description,
      long_description=long_description,
      classifiers=classifiers,
      keywords='application wrapper',
      author="Zhenjiang Zech Xu",
      author_email="zhenjiang.xu@gmail.com",
      maintainer_email="zhenjiang.xu@gmail.com",
      url='http://github.com/rnaer/dumpling',
      py_modules=["dumpling"],
      test_suite='nose.collector',
      install_requires=[],
      extras_require={'test': ["nose", "pep8", "flake8"],
                      'coverage': ["coverage"],
                      'doc': ["Sphinx"]})
