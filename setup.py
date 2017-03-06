"""Setup file for uvclite

"""

from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

# Python versions less than 3.4 require enum34 backport
if sys.version_info[0] == 2 or sys.version_info[1] < 4:
    requirements = ['enum34',]
else:
    requirements = []

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='uvclite',
    version='0.0.1a1',
    description='A libuvc wrapper for python',
    long_description=long_description,
    url='https://githib.com/arksine/uvclite',
    author='Eric Callahan',
    author_email='kode4food@yahoo.com',
    license='Apache',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Video :: Capture',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='libuvc uvc video capture',
    packages=find_packages(exclude=['examples']),

    # Python < 3.4 requires Enum backport
    install_requires=requirements
)
