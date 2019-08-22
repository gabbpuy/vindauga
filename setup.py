# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()


setup(
    name='vindauga',
    version='0.0.6',
    packages=find_packages(exclude=('test', 'build', 'dist')),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/gabbpuy/vindauga',
    license='BSD',
    author='Andrew Milton',
    author_email='vindauga@unyx.net',
    description='Cross Platform Text UI library',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
