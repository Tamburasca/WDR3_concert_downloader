# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='WDR3 Concert Downloader',
    version='1.0.0',
    description='WDR3 Concert Downloader for their websites, where the '
                'download button it lacking.',
    long_description=readme,
    author='Ralf Antonius Timmermann',
    author_email='ralf.timmermann@gmx.de',
    url='https://github.com/Tamburasca/WDR3_concert_downloader/tree/master/src/WDR3_concert_downloader',
    license=license,
    python_requires='>3.9',
    packages=find_packages(),
)