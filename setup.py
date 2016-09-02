try:
  from setuptools import setup
except ImportError:
  print("No setuptools package, using distutils.core")
  from distutils.core import setup

setup(name='kpp',
      version='0.1',
      author='Jamie Fairbrother',
      author_email='j.fairbrother@lancaster.ac.uk',
      url='http://www.lancs.ac.uk/~fairbrot',
      packages=['kpp'])
