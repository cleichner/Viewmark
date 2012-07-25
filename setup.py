import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(name='ViewMark',
      version='0.1.0',
      description='Quick Markdown Viewer',
      author='Chas Leichner',
      author_email='chas@chas.io',
      url='http://github.com/cleichner/viewmark',
      py_modules=['viewmark']
     )
