# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def read_requirements():
    with open("requirements.txt", "r") as req_file:
        return [line.strip() for line in req_file.readlines()]


def main():
    with open('README.rst') as f:
        readme = f.read()

    with open('LICENSE') as f:
        license = f.read()

    setup(
        name='WDR3 Concert Downloader',
        version='1.2.0',
        description='WDR3 Concert Downloader for their websites, where the '
                    'download button it lacking.',
        long_description=readme,
        author='Ralf Antonius Timmermann',
        author_email='ralf.timmermann@gmx.de',
        url='https://github.com/Tamburasca/WDR3_concert_downloader/tree/master/src/WDR3_concert_downloader',
        license=license,
        python_requires='>3.9',
        install_requires=read_requirements(),
        packages=find_packages(),
    )


if __name__ == "__main__":
    main()