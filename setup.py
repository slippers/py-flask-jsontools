#!/usr/bin/env python
""" JSON API tools for Flask """

from setuptools import setup, find_packages
import os
import re
import ast


def get_requirements(suffix=''):
    BASE_PATH = os.path.join(os.path.dirname(__file__), 'requirements')
    with open(os.path.join(BASE_PATH, 'requirements%s.txt' % suffix)) as f:
        rv = f.read().splitlines()
        return rv

def get_version(file):
    _version_re = re.compile(r'__version__\s+=\s+(.*)')

    with open(file, 'rb') as f:
        version = str(ast.literal_eval(_version_re.search(
            f.read().decode('utf-8')).group(1)))
        return version


setup(
    # http://pythonhosted.org/setuptools/setuptools.html
    name='flask_jsontools_slippers',
    version=get_version('flask_jsontools/__init__.py'),
    author='Mark Vartanyan',
    author_email='kolypto@gmail.com',

    url='https://github.com/slippers/py-flask-jsontools',
    license='BSD',
    description=__doc__,
    long_description=open('README.rst').read(),
    keywords=['flask', 'json', 'sqlalchemy'],

    packages=find_packages(),
    scripts=[],
    entry_points={},

    install_requires=get_requirements(),
    extras_require={},
    include_package_data=True,
    test_suite='pytest',

    platforms='any',
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
