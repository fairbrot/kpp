try:
  from setuptools import setup
except ImportError:
  print("No setuptools package, using distutils.core")
  from distutils.core import setup

import unittest
def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite

setup(name='kpp',
      version='0.1',
      author='Jamie Fairbrother',
      author_email='j.fairbrother@lancaster.ac.uk',
      url='http://www.lancs.ac.uk/~fairbrot',
      test_suite='setup.my_test_suite',
      packages=['kpp'])
