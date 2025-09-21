# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

dependencies = [
    "pyperclip >= 1.8.2",
    "wcwidth >= 0.2.6",
    "Pillow >= 10.0.0",
    # Windows
    "pywin32 >= 304; sys_platform == 'win32'",
]

setup(
    name='vindauga',
    version='0.5.0',
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
    install_requires=dependencies,
)

# Note to self
# python3 -m pip install --upgrade twine
# python3 -m pip install --upgrade wheel
# rm -rf dist/*
# python3 setup.py sdist bdist_wheel
# twine upload dist/*
