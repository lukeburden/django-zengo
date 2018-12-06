from setuptools import find_packages
from setuptools import setup


NAME = "django-zengo"
DESCRIPTION = "Integrate Zendesk and your Django app"
AUTHOR = "Luke Burden"
AUTHOR_EMAIL = "lukeburden@gmail.com"
URL = "https://github.com/lukeburden/django-zengo"
LONG_DESCRIPTION = """
============
Integrate Zendesk and your Django app
============
.. image:: https://img.shields.io/travis/lukeburden/django-zengo.svg
    :target: https://travis-ci.org/lukeburden/django-zengo
.. image:: https://img.shields.io/codecov/c/github/lukeburden/django-zengo.svg
    :target: https://codecov.io/gh/lukeburden/django-zengo
.. image:: https://img.shields.io/pypi/dm/django-zengo.svg
    :target:  https://pypi.python.org/pypi/django-zengo/
.. image:: https://img.shields.io/pypi/v/django-zengo.svg
    :target:  https://pypi.python.org/pypi/django-zengo/
.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target:  https://pypi.python.org/pypi/django-zengo/

Zengo facilitates receiving webhook updates from Zendesk and detecting new tickets and comments on existing tickets
whilst maintaining a local cache of Zendesk ticket, comment and user data.
"""

tests_require = ["pytest", "pytest-django"]

setup(
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    version="1.0.0",
    license="MIT",
    url=URL,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
    install_requires=[
        "django>=1.11",
    ],
    test_suite="runtests.runtests",
    tests_require=tests_require,
    zip_safe=False,
)
