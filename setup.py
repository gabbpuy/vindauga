# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

dependencies = [
    # Windows
    "pywin32 >= 304; sys_platform == 'win32'",
    "windows_curses >= 2.3.0 ; sys_platform == 'win32'",

    # Mac
    "pasteboard >= 0.3.3 ; sys_platform == 'darwin'",
]

setup(
    name='vindauga',
    version='0.1.0',
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
    install_requires = dependencies,
)

# Note to self
# python3 -m pip install --upgrade twine
# rm -rf dist/*
# python3 setup.py sdist bdist_wheel
# twine upload dist/*
