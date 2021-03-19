from distutils.core import setup
import setuptools
from setuptools import find_packages

setup(
    name='Botic',
    version='1.1.2',
    author='Matth Ingersoll',
    author_email='matth@mtingers.com',
    packages=find_packages(),
    license='GPLv3',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
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
            'boticdump=botic.dumpdata:main',
        ],
    },
    package_data={'botic': ['data/historical-btc.csv.gz']},
    include_package_data=True,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)


