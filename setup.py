from distutils.core import setup
import setuptools
from setuptools import find_packages

setup(
    name='Botic',
    version='1.0.0',
    author='Matth Ingersoll',
    author_email='matth@mtingers.com',
    packages=find_packages(),
    license='BSD 2-Clause License',
    long_description='None', #open('README.md').read(),
    url='https://github.com/mtingers/botic',
    install_requires=[
        'filelock>=3.0.12',
        'cbpro>=1.1.4',
    ],
    entry_points={
        'console_scripts': [
            'botic=botic.cli:main',
            'boticp=botic.cli:main_persist',
            'botictop=botic.top:main',
        ],
    },
    package_data={'botic': ['data/historical-btc.csv.gz']},
    include_package_data=True,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)


